import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tag import pos_tag
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import logging
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime
from app.models import Job, Resume, CandidateEvaluation
from app.schemas import EvaluationResult
from sqlalchemy.orm import Session
import pytz

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')
    nltk.download('averaged_perceptron_tagger')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobMatcher:
    def __init__(self):
        """Initialize the JobMatcher with NLTK components."""
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.skill_weights = {
            "required": 1.0,
            "preferred": 0.7,
            "bonus": 0.3
        }

    def preprocess_text(self, text: str) -> str:
        """Preprocess text by tokenizing, removing stopwords, and lemmatizing."""
        try:
            # Tokenize and convert to lowercase
            tokens = word_tokenize(text.lower())
            
            # Remove stopwords and lemmatize
            processed_tokens = [
                self.lemmatizer.lemmatize(token)
                for token in tokens
                if token not in self.stop_words and token.isalnum()
            ]
            
            return ' '.join(processed_tokens)
        except Exception as e:
            logger.error(f"Error preprocessing text: {str(e)}")
            return ""

    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from text using NLTK POS tagging."""
        try:
            tokens = word_tokenize(text)
            tagged = pos_tag(tokens)
            
            # Extract nouns and proper nouns as potential skills
            skills = [
                word.lower() for word, tag in tagged
                if tag in ['NN', 'NNS', 'NNP', 'NNPS'] and word.lower() not in self.stop_words
            ]
            
            return list(set(skills))
        except Exception as e:
            logger.error(f"Error extracting skills: {str(e)}")
            return []

    def calculate_match_score(self, job_text: str, resume_text: str) -> float:
        """Calculate semantic similarity between job and resume text."""
        try:
            # Preprocess texts
            job_processed = self.preprocess_text(job_text)
            resume_processed = self.preprocess_text(resume_text)
            
            # Create TF-IDF vectors
            tfidf_matrix = self.vectorizer.fit_transform([job_processed, resume_processed])
            
            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating match score: {str(e)}")
            return 0.0
        
    def analyze_skills_match(self, job_requirements: List[str], resume_skills: List[str]) -> Tuple[float, List[str]]:
        """Analyze the match between job requirements and resume skills."""
        try:
            # Preprocess skills
            job_skills = [self.preprocess_text(skill) for skill in job_requirements]
            resume_skills_processed = [self.preprocess_text(skill) for skill in resume_skills]
            
            # Calculate Jaccard similarity
            job_set = set(job_skills)
            resume_set = set(resume_skills_processed)
            
            if not job_set:
                return 0.0, []
            
            intersection = job_set.intersection(resume_set)
            union = job_set.union(resume_set)
            
            match_percentage = len(intersection) / len(union) if union else 0.0
            matching_skills = list(intersection)
            
            return match_percentage, matching_skills
        except Exception as e:
            logger.error(f"Error analyzing skills match: {str(e)}")
            return 0.0, []

    def calculate_skill_match(self, job_skills: List[str], candidate_skills: List[str]) -> float:
        """Calculate skill match percentage"""
        if not job_skills:
            return 0.0
        
        matched_skills = set(job_skills) & set(candidate_skills)
        return len(matched_skills) / len(job_skills)
    
    def calculate_experience_match(self, required_experience: float, candidate_experience: float) -> float:
        """Calculate experience match percentage"""
        if required_experience == 0:
            return 1.0
        return min(1.0, candidate_experience / required_experience)

    def evaluate_candidate(self, job: Job, resume: Resume) -> EvaluationResult:
        """Evaluate a candidate's match for a job"""
        try:
            # Extract skills and experience
            job_skills = [skill.lower() for skill in job.skills_required]
            candidate_skills = [skill.lower() for skill in resume.extracted_skills]
            
            # Calculate match scores
            skill_match = self.calculate_skill_match(job_skills, candidate_skills)
            experience_match = self.calculate_experience_match(
                job.experience_required,
                resume.total_experience
            )
            
            # Calculate overall score (weighted average)
            overall_score = (skill_match * 0.7) + (experience_match * 0.3)
            
            # Determine matching skills
            matching_skills = list(set(job_skills) & set(candidate_skills))
            
            return EvaluationResult(
                job_id=job.id,
                resume_id=resume.id,
                overall_score=overall_score,
                skill_match=skill_match,
                experience_match=experience_match,
                matching_skills=matching_skills,
                evaluation_date=datetime.now(pytz.UTC)
            )
        except Exception as e:
            logger.error(f"Error evaluating candidate: {str(e)}")
            raise

# Create a singleton instance of JobMatcher
_matcher = JobMatcher()

def evaluate_candidate(job: Job, resume: Resume) -> EvaluationResult:
    """Evaluate a candidate's match for a job using the JobMatcher singleton."""
    return _matcher.evaluate_candidate(job, resume)

def batch_evaluate_candidates(
    job_description: str,
    job_requirements: List[str],
    resumes: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Batch evaluate multiple resumes for a job."""
    results = []
    for resume in resumes:
        result = evaluate_candidate(
            job_description=job_description,
            job_requirements=job_requirements,
            resume_text=resume["text"],
            resume_skills=resume["skills"]
        )
        result["resume_id"] = resume["id"]
        results.append(result)
    return results

def calculate_match_score(job_text: str, resume_text: str) -> float:
    """Calculate semantic similarity between job and resume text using the JobMatcher singleton."""
    return _matcher.calculate_match_score(job_text, resume_text)

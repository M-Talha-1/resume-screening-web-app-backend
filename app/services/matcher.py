from typing import List, Dict
import re

def calculate_match_score(job_description: str, resume_text: str) -> float:
    """
    Calculate match score between job description and resume
    Returns a score between 0 and 100
    """
    # Preprocess text
    job_tokens = preprocess_text(job_description)
    resume_tokens = preprocess_text(resume_text)

    # Calculate skill match score
    skill_score = calculate_skill_match(job_tokens, resume_tokens)

    # Calculate experience match score
    experience_score = calculate_experience_match(job_description, resume_text)

    # Calculate keyword match score
    keyword_score = calculate_keyword_match(job_tokens, resume_tokens)

    # Weighted average of scores
    final_score = (skill_score * 0.4) + (experience_score * 0.3) + (keyword_score * 0.3)
    
    return round(final_score, 2)

def preprocess_text(text: str) -> List[str]:
    """Preprocess text by tokenizing and removing common words"""
    # Convert to lowercase
    text = text.lower()
    
    # Remove special characters and extra spaces
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Split into words
    tokens = text.split()
    
    # Remove common English words
    common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    tokens = [token for token in tokens if token not in common_words]
    
    return tokens

def calculate_skill_match(job_tokens: List[str], resume_tokens: List[str]) -> float:
    """Calculate skill match score"""
    # Common technical skills
    technical_skills = {
        'python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php',
        'html', 'css', 'react', 'angular', 'vue', 'node.js',
        'sql', 'mysql', 'postgresql', 'mongodb',
        'docker', 'kubernetes', 'aws', 'azure', 'gcp',
        'machine learning', 'artificial intelligence', 'data science'
    }
    
    # Find skills in job description
    job_skills = set(token for token in job_tokens if token in technical_skills)
    
    # Find skills in resume
    resume_skills = set(token for token in resume_tokens if token in technical_skills)
    
    # Calculate match score
    if not job_skills:
        return 0.0
    
    matched_skills = job_skills.intersection(resume_skills)
    return (len(matched_skills) / len(job_skills)) * 100

def calculate_experience_match(job_text: str, resume_text: str) -> float:
    """Calculate experience match score"""
    # Look for experience requirements in job description
    experience_pattern = r'(\d+)\+?\s*(?:years|yrs)'
    job_match = re.search(experience_pattern, job_text.lower())
    
    if not job_match:
        return 0.0
    
    required_experience = float(job_match.group(1))
    
    # Look for experience in resume
    resume_match = re.search(experience_pattern, resume_text.lower())
    
    if not resume_match:
        return 0.0
    
    candidate_experience = float(resume_match.group(1))
    
    # Calculate score based on experience match
    if candidate_experience >= required_experience:
        return 100.0
    else:
        return (candidate_experience / required_experience) * 100

def calculate_keyword_match(job_tokens: List[str], resume_tokens: List[str]) -> float:
    """Calculate keyword match score"""
    # Count unique keywords in job description
    job_keywords = set(job_tokens)
    
    # Count matching keywords in resume
    resume_keywords = set(resume_tokens)
    
    # Calculate match score
    if not job_keywords:
        return 0.0
    
    matched_keywords = job_keywords.intersection(resume_keywords)
    return (len(matched_keywords) / len(job_keywords)) * 100

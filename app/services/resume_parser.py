import os
import re
from io import StringIO
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.high_level import extract_text
import docx2txt
import json
from typing import Dict, Any, List
import logging
from datetime import datetime
import pytz

# Configure logging
logger = logging.getLogger(__name__)

class ResumeParser:
    def __init__(self):
        self.skill_keywords = [
            # Programming Languages
            "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "php", "go", "rust",
            "swift", "kotlin", "scala", "r", "matlab", "perl", "shell", "bash", "powershell",
            
            # Web Technologies
            "html", "css", "sass", "less", "react", "angular", "vue", "node.js", "express",
            "django", "flask", "fastapi", "spring", "laravel", "ruby on rails", "asp.net",
            
            # Databases
            "sql", "mysql", "postgresql", "mongodb", "redis", "cassandra", "oracle", "sqlite",
            "dynamodb", "firebase", "neo4j",
            
            # DevOps & Cloud
            "docker", "kubernetes", "aws", "azure", "gcp", "terraform", "ansible", "jenkins",
            "git", "ci/cd", "github actions", "gitlab ci", "prometheus", "grafana",
            
            # Machine Learning & Data Science
            "machine learning", "deep learning", "tensorflow", "pytorch", "keras", "scikit-learn",
            "pandas", "numpy", "matplotlib", "seaborn", "opencv", "nlp", "computer vision",
            
            # Mobile Development
            "android", "ios", "react native", "flutter", "xamarin", "swift", "kotlin",
            
            # Other Technologies
            "rest", "graphql", "grpc", "microservices", "serverless", "blockchain", "solidity",
            "ethereum", "web3", "cybersecurity", "penetration testing", "ethical hacking"
        ]
        
        self.education_keywords = [
            "bachelor", "master", "phd", "doctorate", "bsc", "msc", "mba", "b.tech", "m.tech",
            "b.e.", "m.e.", "bca", "mca", "diploma", "certification", "course", "training"
        ]
        
        self.experience_keywords = [
            "experience", "work", "employment", "career", "professional", "job", "role",
            "position", "responsibilities", "achievements", "projects"
        ]

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        try:
            logger.info(f"Attempting to extract text from PDF: {pdf_path}")
            resource_manager = PDFResourceManager()
            output_string = StringIO()
            codec = 'utf-8'
            laparams = LAParams()
            converter = TextConverter(resource_manager, output_string, codec=codec, laparams=laparams)
            interpreter = PDFPageInterpreter(resource_manager, converter)

            with open(pdf_path, 'rb') as fh:
                for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
                    interpreter.process_page(page)

            text = output_string.getvalue()
            converter.close()
            output_string.close()
            
            # Clean up the extracted text
            text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
            text = re.sub(r'\n+', '\n', text)  # Replace multiple newlines with single newline
            text = text.strip()
            
            if not text:
                logger.warning(f"No text extracted from PDF: {pdf_path}")
                return ""
                
            logger.info(f"Successfully extracted text from PDF: {pdf_path}")
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_path}: {str(e)}")
            return ""

    def extract_text_from_docx(self, docx_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            return docx2txt.process(docx_path)
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {str(e)}")
            return ""

    def extract_text_from_txt(self, txt_path: str) -> str:
        """Extract text from TXT file"""
        try:
            with open(txt_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            logger.error(f"Error extracting text from TXT: {str(e)}")
            return ""

    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from a file based on its extension"""
        file_extension = file_path.lower().split('.')[-1]
        
        if file_extension == 'pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_extension == 'docx':
            return self.extract_text_from_docx(file_path)
        elif file_extension == 'txt':
            return self.extract_text_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")

    def extract_contact_info(self, text: str) -> Dict[str, str]:
        """Extract contact information from resume text"""
        contact_info = {
            "email": "",
            "phone": "",
            "linkedin": "",
            "github": "",
            "website": ""
        }
        
        try:
            # Extract email
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            email_match = re.search(email_pattern, text)
            if email_match:
                contact_info["email"] = email_match.group(0)
            
            # Extract phone
            phone_pattern = r'(\+\d{1,3}[-.\s]?)?(\d{3}[-.\s]?)?\d{3}[-.\s]?\d{4}'
            phone_match = re.search(phone_pattern, text)
            if phone_match:
                contact_info["phone"] = phone_match.group(0)
        
            # Extract LinkedIn
            linkedin_pattern = r'(?:linkedin\.com/in/|linkedin\.com/company/)[a-zA-Z0-9-]+'
            linkedin_match = re.search(linkedin_pattern, text)
            if linkedin_match:
                contact_info["linkedin"] = linkedin_match.group(0)
            
            # Extract GitHub
            github_pattern = r'github\.com/[a-zA-Z0-9-]+'
            github_match = re.search(github_pattern, text)
            if github_match:
                contact_info["github"] = github_match.group(0)
            
            # Extract website
            website_pattern = r'(?:https?://)?(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:/\S*)?'
            website_match = re.search(website_pattern, text)
            if website_match:
                contact_info["website"] = website_match.group(0)
            
            return contact_info
        except Exception as e:
            logger.error(f"Error extracting contact info: {str(e)}")
            return contact_info

    def extract_education(self, text: str) -> List[Dict[str, str]]:
        """Extract education information from resume text"""
        education = []
        try:
            lines = text.split('\n')
            
            for i, line in enumerate(lines):
                if any(keyword in line.lower() for keyword in self.education_keywords):
                    education_entry = {
                        "institution": "",
                        "degree": "",
                        "field": "",
                        "start_date": "",
                        "end_date": "",
                        "gpa": ""
                    }
                    
                    # Extract degree and field
                    degree_pattern = r'(?:bachelor|master|phd|doctorate|bsc|msc|mba|b\.tech|m\.tech|b\.e\.|m\.e\.|bca|mca|diploma)\s*(?:in|of)?\s*([a-zA-Z\s]+)'
                    degree_match = re.search(degree_pattern, line.lower())
                    if degree_match:
                        education_entry["degree"] = degree_match.group(1).strip()
                    
                    # Extract institution
                    if i + 1 < len(lines):
                        education_entry["institution"] = lines[i + 1].strip()
                    
                    # Extract dates
                    date_pattern = r'(\d{4})\s*-\s*(\d{4}|present)'
                    date_match = re.search(date_pattern, line)
                    if date_match:
                        education_entry["start_date"] = date_match.group(1)
                        education_entry["end_date"] = date_match.group(2)
        
                    # Extract GPA
                    gpa_pattern = r'gpa\s*:\s*(\d+\.\d+)'
                    gpa_match = re.search(gpa_pattern, line.lower())
                    if gpa_match:
                        education_entry["gpa"] = gpa_match.group(1)
                    
                    education.append(education_entry)
            
            return education
        except Exception as e:
            logger.error(f"Error extracting education: {str(e)}")
            return []

    def extract_experience(self, text: str) -> List[Dict[str, str]]:
        """Extract work experience from resume text"""
        experience = []
        try:
            lines = text.split('\n')
            
            for i, line in enumerate(lines):
                if any(keyword in line.lower() for keyword in self.experience_keywords):
                    exp_entry = {
                        "company": "",
                        "position": "",
                        "start_date": "",
                        "end_date": "",
                        "location": "",
                        "description": []
                    }
                    
                    # Extract company and position
                    company_pattern = r'at\s+([a-zA-Z0-9\s]+)'
                    company_match = re.search(company_pattern, line.lower())
                    if company_match:
                        exp_entry["company"] = company_match.group(1).strip()
                    
                    # Extract position
                    position_pattern = r'([a-zA-Z\s]+(?:developer|engineer|architect|manager|consultant|analyst|specialist|lead|director|head))'
                    position_match = re.search(position_pattern, line)
                    if position_match:
                        exp_entry["position"] = position_match.group(1).strip()
                    
                    # Extract dates
                    date_pattern = r'(\d{4})\s*-\s*(\d{4}|present)'
                    date_match = re.search(date_pattern, line)
                    if date_match:
                        exp_entry["start_date"] = date_match.group(1)
                        exp_entry["end_date"] = date_match.group(2)
                    
                    # Extract location
                    location_pattern = r'in\s+([a-zA-Z\s,]+)'
                    location_match = re.search(location_pattern, line.lower())
                    if location_match:
                        exp_entry["location"] = location_match.group(1).strip()
        
                    # Extract description
                    j = i + 1
                    while j < len(lines) and lines[j].strip() and not any(keyword in lines[j].lower() for keyword in self.experience_keywords):
                        if lines[j].strip().startswith('-'):
                            exp_entry["description"].append(lines[j].strip()[1:].strip())
                        j += 1
                    
                    experience.append(exp_entry)
            
            return experience
        except Exception as e:
            logger.error(f"Error extracting experience: {str(e)}")
            return []

    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from resume text"""
        try:
            skills = []
            text_lower = text.lower()
            
            for skill in self.skill_keywords:
                if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
                    skills.append(skill)
            
            return skills
        except Exception as e:
            logger.error(f"Error extracting skills: {str(e)}")
            return []

    def extract_total_experience(self, text: str) -> float:
        """Extract total years of experience from resume text"""
        try:
            experience_pattern = r'(\d+)\+?\s*(?:years|yrs)'
            experience_matches = re.findall(experience_pattern, text.lower())
            if experience_matches:
                return float(max(map(int, experience_matches)))
            return 0.0
        except Exception as e:
            logger.error(f"Error extracting total experience: {str(e)}")
            return 0.0

    def extract_resume_data(self, file_path: str) -> Dict[str, Any]:
        """Extract all relevant data from resume file"""
        try:
            # Extract text based on file type
            text = self.extract_text_from_file(file_path)
            if not text:
                logger.error("No text extracted from file")
                return None
            
            # Extract all information
            contact_info = self.extract_contact_info(text)
            education = self.extract_education(text)
            experience = self.extract_experience(text)
            skills = self.extract_skills(text)
            total_experience = self.extract_total_experience(text)
            
            # Extract name (first line usually contains name)
            lines = text.split('\n')
            name = lines[0].strip() if lines else ""
            
            # Validate required fields
            if not name and not contact_info["email"]:
                logger.error("Missing required fields (name and email)")
                return None
    
            return {
                "name": name,
                "email": contact_info["email"],
                "phone": contact_info["phone"],
                "skills": skills,
                "experience_years": total_experience,
                "linkedin": contact_info["linkedin"],
                "github": contact_info["github"],
                "website": contact_info["website"],
                "education": education,
                "work_experience": experience,
                "raw_text": text
            }
        except Exception as e:
            logger.error(f"Error extracting resume data: {str(e)}")
            return None

def extract_resume_data(file_path: str) -> Dict[str, Any]:
    """Extract data from resume PDF"""
    try:
        # Create parser instance
        parser = ResumeParser()
        
        # Extract text from PDF
        text = parser.extract_text_from_file(file_path)
        logger.info(f"Successfully extracted text from PDF: {file_path}")
        
        # Log the raw text for debugging
        logger.debug(f"Raw text from PDF: {text[:500]}...")  # Log first 500 chars
        
        # Parse resume data
        try:
            data = parser.extract_resume_data(file_path)
            
            # Validate required fields
            if not data or not isinstance(data, dict):
                logger.error("Invalid resume data format")
                return extract_basic_info(text)
                
            if not data.get('name') or not data.get('email'):
                logger.error("Missing required fields in parsed resume data")
                return extract_basic_info(text)
                
            return data
            
        except Exception as e:
            logger.error(f"Error parsing resume data: {str(e)}")
            # Try to extract basic information from raw text
            return extract_basic_info(text)
            
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise

def extract_basic_info(text: str) -> Dict[str, Any]:
    """Extract basic information from raw text when parsing fails"""
    try:
        # Basic email extraction
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        email = re.search(email_pattern, text)
        
        # Basic name extraction (first line usually contains name)
        name = text.split('\n')[0].strip()
        
        # Basic phone extraction
        phone_pattern = r'(\+\d{1,3}[-.\s]?)?(\d{3}[-.\s]?)?\d{3}[-.\s]?\d{4}'
        phone = re.search(phone_pattern, text)
        
        return {
            'name': name if name else 'Unknown',
            'email': email.group(0) if email else '',
            'mobile_number': phone.group(0) if phone else '',
            'skills': [],  # Empty list as we can't reliably extract skills
            'experience': [],  # Empty list as we can't reliably extract experience
            'education': []  # Empty list as we can't reliably extract education
        }
    except Exception as e:
        logger.error(f"Error extracting basic info: {str(e)}")
        return {
            'name': 'Unknown',
            'email': '',
            'mobile_number': '',
            'skills': [],
            'experience': [],
            'education': []
        }
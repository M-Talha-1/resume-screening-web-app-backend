import os
import re
from io import StringIO
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
import docx2txt
from typing import Dict, Any

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF file"""
    try:
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
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
        return ""

def extract_text_from_docx(docx_path: str) -> str:
    """Extract text from DOCX file"""
    try:
        return docx2txt.process(docx_path)
    except Exception as e:
        print(f"Error extracting text from DOCX: {str(e)}")
        return ""

def extract_text_from_txt(txt_path: str) -> str:
    """Extract text from TXT file"""
    try:
        with open(txt_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error extracting text from TXT: {str(e)}")
        return ""

def extract_text_from_file(file_path: str) -> str:
    """
    Extract text from a file based on its extension.
    Supports PDF, DOCX, and TXT files.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        str: Extracted text from the file
        
    Raises:
        ValueError: If file type is not supported
    """
    file_extension = file_path.lower().split('.')[-1]
    
    if file_extension == 'pdf':
        return extract_text_from_pdf(file_path)
    elif file_extension == 'docx':
        return extract_text_from_docx(file_path)
    elif file_extension == 'txt':
        return extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")

def extract_resume_data(file_path: str) -> Dict[str, Any]:
    """Extract data from resume file"""
    # Get file extension
    file_ext = os.path.splitext(file_path)[1].lower()
    
    # Extract text based on file type
    if file_ext == '.pdf':
        text = extract_text_from_pdf(file_path)
    elif file_ext == '.docx':
        text = extract_text_from_docx(file_path)
    elif file_ext == '.txt':
        text = extract_text_from_txt(file_path)
    else:
        return None

    # Extract basic information
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
    
    email = re.search(email_pattern, text)
    phone = re.search(phone_pattern, text)
    
    # Extract name (assuming it's in the first few lines)
    lines = text.split('\n')
    name = next((line.strip() for line in lines[:5] if line.strip() and not re.search(email_pattern, line)), "")
    
    # Extract skills (common keywords)
    skills = []
    skill_keywords = [
        'python', 'java', 'javascript', 'react', 'angular', 'vue', 'node', 'express',
        'django', 'flask', 'fastapi', 'sql', 'postgresql', 'mysql', 'mongodb',
        'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'git', 'ci/cd',
        'html', 'css', 'typescript', 'rest', 'graphql', 'microservices'
    ]
    
    for skill in skill_keywords:
        if re.search(r'\b' + skill + r'\b', text.lower()):
            skills.append(skill)
    
    # Extract experience
    exp_pattern = r'(\d+)(?:\+)?\s*(?:year|yr)s?'
    exp_matches = re.findall(exp_pattern, text.lower())
    total_experience = float(max(map(int, exp_matches))) if exp_matches else 0.0
    
    # Extract current role/designation
    designation_patterns = [
        r'(?:^|\n)(?:current\s+)?(?:position|role|title):\s*([^\n]+)',
        r'(?:^|\n)([^,\n]+(?:developer|engineer|architect|manager|consultant)[^,\n]*)',
    ]
    
    designation = None
    for pattern in designation_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            designation = match.group(1).strip()
            break
    
    return {
        "name": name,
        "email": email.group() if email else "",
        "mobile_number": phone.group() if phone else "",
        "skills": skills,
        "designation": designation,
        "total_experience": total_experience,
        "raw_text": text
    }

def extract_email(text: str) -> str:
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(email_pattern, text)
    return match.group(0) if match else ""

def extract_phone(text: str) -> str:
    phone_pattern = r'(\+\d{1,3}[-.\s]?)?(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})'
    match = re.search(phone_pattern, text)
    return match.group(0) if match else ""

def extract_name(text: str) -> str:
    # Simple name extraction - first line usually contains name
    lines = text.split('\n')
    return lines[0].strip() if lines else ""

def extract_skills(text: str) -> list:
    # Common skills to look for
    common_skills = [
        "python", "java", "javascript", "c++", "c#", "ruby", "php",
        "html", "css", "react", "angular", "vue", "node.js",
        "sql", "mysql", "postgresql", "mongodb",
        "docker", "kubernetes", "aws", "azure", "gcp",
        "machine learning", "artificial intelligence", "data science",
        "project management", "agile", "scrum"
    ]
    
    found_skills = []
    text_lower = text.lower()
    
    for skill in common_skills:
        if skill in text_lower:
            found_skills.append(skill)
    
    return found_skills

def extract_experience(text: str) -> float:
    # Look for years of experience
    experience_pattern = r'(\d+)\+?\s*(?:years|yrs)'
    match = re.search(experience_pattern, text.lower())
    if match:
        return float(match.group(1))
    return 0.0

def extract_designation(text: str) -> str:
    # Common designations
    common_designations = [
        "software engineer", "developer", "programmer",
        "data scientist", "machine learning engineer",
        "project manager", "team lead", "architect",
        "devops engineer", "full stack developer"
    ]
    
    text_lower = text.lower()
    for designation in common_designations:
        if designation in text_lower:
            return designation
    return ""
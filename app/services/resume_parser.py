import spacy
import warnings
import os
from pyresparser import ResumeParser
from pdfminer.high_level import extract_text
import docx

warnings.filterwarnings("ignore", category=UserWarning)
nlp = spacy.load("en_core_web_sm")

def extract_text_from_docx(docx_path):
    doc = docx.Document(docx_path)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text_from_file(file_path):
    ext = os.path.splitext(file_path)[-1].lower()
    if ext == ".pdf":
        return extract_text(file_path)
    elif ext == ".docx":
        return extract_text_from_docx(file_path)
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        raise ValueError("Unsupported file type")

def extract_resume_data(resume_path):
    try:
        parsed_data = ResumeParser(resume_path).get_extracted_data()
        raw_text = extract_text_from_file(resume_path)
        doc = nlp(raw_text)
        companies = [ent.text for ent in doc.ents if ent.label_ == "ORG"]

        return {
            "name": parsed_data.get("name", ""),
            "email": parsed_data.get("email", ""),
            "mobile_number": parsed_data.get("mobile_number", ""),
            "skills": parsed_data.get("skills", []),
            "college_name": parsed_data.get("college_name", ""),
            "degree": parsed_data.get("degree", []),
            "designation": parsed_data.get("designation", []),
            "experience": parsed_data.get("experience", []),
            "company_names": parsed_data.get("company_names", companies),
            "total_experience": parsed_data.get("total_experience", 0.0),
            "raw_text": raw_text.strip(),
        }
    except Exception as e:
        print(f"Error parsing resume: {e}")
        return None
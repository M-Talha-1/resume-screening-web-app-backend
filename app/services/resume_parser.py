import spacy
import json
import warnings
import os
from pyresparser import ResumeParser
from pdfminer.high_level import extract_text
import docx

warnings.filterwarnings("ignore", category=UserWarning)

# Load spaCy NLP model
nlp = spacy.load("en_core_web_sm")

def extract_text_from_docx(docx_path):
    """Extract text from a DOCX file."""
    doc = docx.Document(docx_path)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text_from_file(file_path):
    """Extracts text from PDF, DOCX, or TXT files."""
    file_extension = os.path.splitext(file_path)[-1].lower()

    if file_extension == ".pdf":
        return extract_text(file_path)
    elif file_extension == ".docx":
        return extract_text_from_docx(file_path)
    elif file_extension == ".txt":
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    else:
        raise ValueError("Unsupported file format. Only PDF, DOCX, and TXT are supported.")

def extract_resume_data(resume_path):
    """
    Parses a resume and extracts structured data, including raw text.
    """
    try:
        # Extract structured data using pyresparser
        parsed_data = ResumeParser(resume_path).get_extracted_data()

        # Extract raw text for job matching
        raw_text = extract_text_from_file(resume_path)

        # Process with spaCy NLP for better entity recognition (custom enhancement)
        doc = nlp(raw_text)

        # Extract company names from raw text (pyresparser sometimes misses this)
        companies = [ent.text for ent in doc.ents if ent.label_ == "ORG"]

        # Ensure extracted data is not None
        extracted_data = {
            "name": parsed_data.get("name", ""),
            "email": parsed_data.get("email", ""),
            "mobile_number": parsed_data.get("mobile_number", ""),
            "skills": parsed_data.get("skills", []),
            "college_name": parsed_data.get("college_name", ""),
            "degree": parsed_data.get("degree", []),
            "designation": parsed_data.get("designation", []),
            "experience": parsed_data.get("experience", []),
            "company_names": parsed_data.get("company_names", companies),  # Use NLP if pyresparser misses it
            "total_experience": parsed_data.get("total_experience", 0.0),
            "raw_text": raw_text.strip()  # Store for job matching
        }

        return extracted_data

    except Exception as e:
        print(f"Error parsing resume: {e}")
        return None

# Example usage
if __name__ == "__main__":
    resume_path = "talha.pdf"  # Change to a valid file path
    extracted_info = extract_resume_data(resume_path)
    
    if extracted_info:
        print(json.dumps(extracted_info, indent=4))

import spacy
import re
import torch
from sentence_transformers import SentenceTransformer, util

# Load NLP & embedding models once (performance optimized)
nlp = spacy.load("en_core_web_sm")
bert_model = SentenceTransformer("all-MiniLM-L6-v2")

def preprocess_text(text: str) -> str:
    """Clean and enrich text using NLP."""
    if not text:
        return ""

    # Basic cleanup
    text = re.sub(r'\s+', ' ', text.lower())
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\d+', '', text)

    doc = nlp(text)

    keywords = [
        token.lemma_ for token in doc
        if token.is_alpha and not token.is_stop and token.pos_ in {"NOUN", "VERB", "ADJ"}
    ]
    entities = [
        ent.text for ent in doc.ents
        if ent.label_ in {"ORG", "GPE", "WORK_OF_ART", "PERSON", "DATE", "CARDINAL"}
    ]

    return " ".join(keywords + entities)

def calculate_match_score(job_desc: str, resume_text: str) -> float:
    """Returns semantic similarity score between JD and Resume."""
    job_desc_clean = preprocess_text(job_desc)
    resume_text_clean = preprocess_text(resume_text)

    if not job_desc_clean or not resume_text_clean:
        return 0.0

    job_embedding = bert_model.encode(job_desc_clean, convert_to_tensor=True)
    resume_embedding = bert_model.encode(resume_text_clean, convert_to_tensor=True)

    score = util.pytorch_cos_sim(job_embedding, resume_embedding).item()
    return round(score * 100, 2)  # Convert to percentage

import spacy
import re
import torch
from sentence_transformers import SentenceTransformer, util

# Load optimized spaCy NLP model
nlp = spacy.load("en_core_web_sm")

# Load Sentence-BERT model (optimized for similarity)
bert_model = SentenceTransformer("all-MiniLM-L6-v2")  # Fast, lightweight, and accurate

def preprocess_text(text):
    """Advanced text preprocessing: stopwords removal, NER, lemmatization, punctuation removal."""
    if not text:
        return ""

    # Convert to lowercase & remove unwanted characters
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)  # Remove multiple spaces
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    text = re.sub(r'\d+', '', text)  # Remove numbers

    doc = nlp(text)  # Process with spaCy

    # Keep only relevant words (Nouns, Verbs, Adjectives) and remove stopwords
    keywords = [
        token.lemma_ for token in doc
        if not token.is_stop and token.is_alpha and token.pos_ in {"NOUN", "VERB", "ADJ"}
    ]

    # Extract important Named Entities (Skills, Degrees, Job Titles)
    entities = [
        ent.text for ent in doc.ents
        if ent.label_ in {"ORG", "PERSON", "GPE", "DATE", "CARDINAL", "NORP", "WORK_OF_ART"}
    ]

    processed_text = " ".join(keywords + entities)  # Combine extracted words & entities
    return processed_text

def calculate_match_score(job_desc, resume_text):
    """Computes similarity score using BERT embeddings & cosine similarity."""
    job_desc_clean = preprocess_text(job_desc)
    resume_text_clean = preprocess_text(resume_text)

    if not job_desc_clean or not resume_text_clean:
        return 0.0  # No meaningful text to compare

    # Convert to BERT embeddings
    job_embedding = bert_model.encode(job_desc_clean, convert_to_tensor=True)
    resume_embedding = bert_model.encode(resume_text_clean, convert_to_tensor=True)

    # Compute Cosine Similarity
    similarity_score = util.pytorch_cos_sim(job_embedding, resume_embedding)

    return round(float(similarity_score) * 100, 2)  # Convert to percentage

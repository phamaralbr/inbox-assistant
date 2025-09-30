import spacy

nlp = spacy.load("pt_core_news_sm")
stopwords = nlp.Defaults.stop_words

def preprocess(text: str) -> str:
    doc = nlp(text.lower())
    tokens = [token.lemma_ for token in doc if token.is_alpha and token.text not in stopwords]
    return " ".join(tokens)

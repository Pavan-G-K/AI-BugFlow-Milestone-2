# Small local training corpus for an educational severity classifier.
TRAINING = [
 ("application crashes on launch and all users blocked", "Critical"),
 ("payment service unavailable for every customer", "Critical"),
 ("database corruption causes total data loss", "Critical"),
 ("login endpoint returns server error for all users", "High"),
 ("checkout fails for many users", "High"),
 ("cannot save customer profile", "High"),
 ("report export fails intermittently", "Medium"),
 ("search results are incorrect for some filters", "Medium"),
 ("notification is delayed", "Medium"),
 ("button alignment is slightly wrong", "Low"),
 ("typo in help text", "Low"),
 ("icon color is inconsistent", "Low"),
]
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    model = Pipeline([("tfidf", TfidfVectorizer(ngram_range=(1,2))), ("clf", LogisticRegression(max_iter=1000))])
    model.fit([x[0] for x in TRAINING], [x[1] for x in TRAINING])
except Exception:
    model = None

def predict_severity(title: str, description: str):
    text = (title + " " + description).strip()
    if model:
        pred = model.predict([text])[0]
        probs = model.predict_proba([text])[0]
        confidence = float(max(probs))
        return {"severity": pred, "confidence": round(confidence, 3), "model": "TF-IDF + Logistic Regression"}
    t = text.lower()
    if any(x in t for x in ["crash", "data loss", "all users", "unavailable"]):
        severity = "Critical"
    elif any(x in t for x in ["fails", "cannot", "blocked", "error"]):
        severity = "High"
    elif any(x in t for x in ["incorrect", "delayed", "intermittent"]):
        severity = "Medium"
    else:
        severity = "Low"
    return {"severity": severity, "confidence": 0.55, "model": "Rule-based fallback (install requirements for ML)"}

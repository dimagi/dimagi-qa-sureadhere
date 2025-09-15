import os
import joblib
from sklearn.tree import DecisionTreeClassifier
from sklearn.feature_extraction.text import TfidfVectorizer

# Dummy data — replace this with your actual training set
X_train = ["submit", "cancel", "search box", "form button", "dropdown"]
y_train = ["button", "button", "input", "button", "select"]

# Vectorizer and model
vectorizer = TfidfVectorizer()
X_vec = vectorizer.fit_transform(X_train)

model = DecisionTreeClassifier()
model.fit(X_vec, y_train)

# Save to compatible .pkl files
os.makedirs("ml_model", exist_ok=True)
joblib.dump(model, "ml_model/locator_ml_model.pkl")
joblib.dump(vectorizer, "ml_model/vectorizer.pkl")

print("✅ Model and vectorizer saved successfully.")

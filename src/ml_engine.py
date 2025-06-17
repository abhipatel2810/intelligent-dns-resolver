import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import os

# Load data
df = pd.read_csv("data/training_data.csv")

# Encode labels
le_query_type = LabelEncoder()
le_best_upstream = LabelEncoder()

df['query_type'] = le_query_type.fit_transform(df['query_type'])
df['best_upstream'] = le_best_upstream.fit_transform(df['best_upstream'])

# Split features and target
X = df[['query_type', 'query_len', 'time_bucket', 'upstream_rtt', 'last_success_rate', 'ttl_variability']]
y = df['best_upstream']

# Train/Test Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate Model
y_pred = model.predict(X_test)

# Ensure labels are specified to avoid mismatch issues
labels = list(range(len(le_best_upstream.classes_)))
report = classification_report(
    y_test, 
    y_pred, 
    labels=labels, 
    target_names=le_best_upstream.classes_,
    zero_division=0  # Prevent division by zero errors
)
print(report)

# Save model and encoders
os.makedirs("models", exist_ok=True)
joblib.dump(model, 'models/ml_model.joblib')
joblib.dump(le_query_type, 'models/le_query_type.joblib')
joblib.dump(le_best_upstream, 'models/le_best_upstream.joblib')

print("Model trained, evaluated, and saved successfully.")

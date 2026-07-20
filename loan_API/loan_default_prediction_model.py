from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import numpy as np

# Load the model
model = joblib.load("gradient_boosting_model.pkl")

app = FastAPI()

# ------------------------------
# MAPPINGS
# ------------------------------
home_ownership_map = {
    "MORTGAGE": 0,
    "OTHER": 1,
    "OWN": 2,
    "RENT": 3
}

previous_default_map = {
    "NO": 0,
    "YES": 1
}

# ------------------------------
# REQUEST BODY
# ------------------------------
class LoanInput(BaseModel):
    person_income: str
    person_home_ownership: str
    loan_int_rate: str
    previous_loan_defaults_on_file: str
    debt_to_income: str


# ------------------------------
# PREDICTION ENDPOINT
# ------------------------------
@app.post("/predict")
def predict_loan_status(data: LoanInput):

    # Convert strings → numeric
    try:
        income = float(data.person_income)
        interest_rate = float(data.loan_int_rate)
        dti = float(data.debt_to_income)
    except ValueError:
        return {"error": "Numeric fields must be valid numbers."}

    # Encode categorical
    home_own = home_ownership_map.get(data.person_home_ownership.upper())
    prev_default = previous_default_map.get(data.previous_loan_defaults_on_file.upper())

    if home_own is None:
        return {"error": "Invalid value for person_home_ownership."}

    if prev_default is None:
        return {"error": "Invalid value for previous_loan_defaults_on_file."}

    # Create feature vector in correct order
    features = np.array([[income, home_own, interest_rate, prev_default, dti]])

    # Predict
    pred = model.predict(features)[0]

    result_str = "approved" if pred == 1 else "rejected"

    return {"loan_status": result_str}

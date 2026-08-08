"""
Preprocessing & Feature Engineering
====================================

Two responsibilities:

1. CHAMPION PATH -- prepare a DataFrame for the 20-feature Home Credit model.
   Computes engineered features server-side (income_credit_ratio, annuity_ratio,
   age) so the user's CSV only needs raw columns.

2. CHALLENGER PATH -- map Home Credit columns to the 8-feature German model schema.
   Derives CreditScore, DTI, EmploymentYears, income_loan_ratio, loan_dti_ratio
   from available Home Credit columns.

Principle: The user should NEVER need to provide engineered features in their CSV.
"""
import numpy as np
import pandas as pd
import config


# --------------------------------------------
#  Champion Model: Feature Engineering
# --------------------------------------------

def engineer_champion_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the 3 engineered features the Champion model expects,
    using raw columns that the user uploads:
    
      income_credit_ratio = AMT_INCOME_TOTAL / AMT_CREDIT_x
      annuity_ratio       = AMT_ANNUITY / AMT_CREDIT_x
      age                 = abs(DAYS_BIRTH) / 365   (if DAYS_BIRTH present)
    
    If the engineered columns already exist in the CSV, they are
    left untouched (user might have pre-computed them).
    """
    df = df.copy()

    # income_credit_ratio
    if "income_credit_ratio" not in df.columns:
        if "AMT_INCOME_TOTAL" in df.columns and "AMT_CREDIT_x" in df.columns:
            df["income_credit_ratio"] = (
                df["AMT_INCOME_TOTAL"] / df["AMT_CREDIT_x"].replace(0, np.nan)
            ).fillna(0.0)

    # annuity_ratio
    if "annuity_ratio" not in df.columns:
        if "AMT_ANNUITY" in df.columns and "AMT_CREDIT_x" in df.columns:
            df["annuity_ratio"] = (
                df["AMT_ANNUITY"] / df["AMT_CREDIT_x"].replace(0, np.nan)
            ).fillna(0.0)

    # age (from DAYS_BIRTH if available, otherwise leave existing 'age' column)
    if "age" not in df.columns:
        if "DAYS_BIRTH" in df.columns:
            df["age"] = df["DAYS_BIRTH"].abs() / 365.0

    return df


def prepare_champion_input(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare a DataFrame for Champion model prediction.
    
    Steps:
      1. Engineer derived features
      2. Select only the 20 features in FEATURE_ORDER
      3. Fill any remaining NaN values with 0
    
    Returns a DataFrame with exactly the columns the model expects,
    in the correct order.
    """
    # Step 1: Compute engineered features from raw columns
    df = engineer_champion_features(df)

    # Step 2: Select features in model order, filling missing with 0
    feature_order = config.FEATURE_ORDER
    if not feature_order:
        raise ValueError("Feature order not loaded -- check features.txt")

    result = pd.DataFrame()
    for feat in feature_order:
        if feat in df.columns:
            result[feat] = df[feat].values
        else:
            # Missing column -> fill with 0 (safe default for numeric features)
            print(f"[preprocess] Warning: '{feat}' missing from input, filling with 0")
            result[feat] = 0.0

    # Step 3: Fill any remaining NaN
    result = result.fillna(0.0)

    return result


# --------------------------------------------
#  Challenger Model: Feature Mapping
# --------------------------------------------

def prepare_challenger_input(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map Home Credit columns to the German model's 8-feature schema.
    
    Challenger expects: Age, Income, CreditScore, LoanAmount, DTI,
                        EmploymentYears, income_loan_ratio, loan_dti_ratio
    
    Mapping:
      Income            AMT_INCOME_TOTAL
      LoanAmount        AMT_CREDIT_x
      Age               age (engineered) or abs(DAYS_BIRTH)/365
      EmploymentYears   abs(DAYS_EMPLOYED) / 365
      income_loan_ratio  AMT_INCOME_TOTAL / AMT_CREDIT_x
      CreditScore       derived from EXT_SOURCE scores (heuristic)
      DTI               AMT_ANNUITY / (AMT_INCOME_TOTAL / 12)
      loan_dti_ratio    LoanAmount * DTI / Income
    """
    df = engineer_champion_features(df)  # Ensure base features exist
    mapped = pd.DataFrame()

    # Direct mappings
    mapped["Income"] = df.get("AMT_INCOME_TOTAL", pd.Series(dtype=float)).fillna(150000)
    mapped["LoanAmount"] = df.get("AMT_CREDIT_x", pd.Series(dtype=float)).fillna(500000)

    # Age: use engineered 'age' column
    if "age" in df.columns:
        mapped["Age"] = df["age"]
    elif "DAYS_BIRTH" in df.columns:
        mapped["Age"] = df["DAYS_BIRTH"].abs() / 365.0
    else:
        mapped["Age"] = 35.0

    # EmploymentYears: convert DAYS_EMPLOYED (negative integer) to years
    if "DAYS_EMPLOYED" in df.columns:
        mapped["EmploymentYears"] = df["DAYS_EMPLOYED"].abs() / 365.0
        # Cap anomalous values (365243 = not employed flag in Home Credit)
        mapped["EmploymentYears"] = mapped["EmploymentYears"].clip(upper=50)
    else:
        mapped["EmploymentYears"] = 5.0

    # income_loan_ratio: same as income_credit_ratio
    if "income_credit_ratio" in df.columns:
        mapped["income_loan_ratio"] = df["income_credit_ratio"]
    else:
        mapped["income_loan_ratio"] = (
            mapped["Income"] / mapped["LoanAmount"].replace(0, np.nan)
        ).fillna(0.3)

    # CreditScore: derive from EXT_SOURCE scores (heuristic: scale 300-850)
    ext_cols = ["EXT_SOURCE_1", "EXT_SOURCE_2", "EXT_SOURCE_3"]
    available_ext = [c for c in ext_cols if c in df.columns]
    if available_ext:
        avg_ext = df[available_ext].mean(axis=1).fillna(0.5)
        mapped["CreditScore"] = 300 + (avg_ext * 550)  # Scale 0-1 -> 300-850
    else:
        mapped["CreditScore"] = 650.0

    # DTI (Debt-to-Income): monthly annuity / monthly income
    monthly_income = mapped["Income"] / 12.0
    if "AMT_ANNUITY" in df.columns:
        mapped["DTI"] = (
            df["AMT_ANNUITY"] / monthly_income.replace(0, np.nan)
        ).fillna(0.35)
    else:
        mapped["DTI"] = 0.35

    # loan_dti_ratio
    mapped["loan_dti_ratio"] = (
        mapped["LoanAmount"] * mapped["DTI"] / mapped["Income"].replace(0, np.nan)
    ).fillna(0.1)

    # Fill remaining NaN
    mapped = mapped.fillna(0.0)

    # Reorder to match model's expected feature order
    challenger_order = list(config.GERMAN_MODEL.feature_names_in_)
    for feat in challenger_order:
        if feat not in mapped.columns:
            mapped[feat] = 0.0

    return mapped[challenger_order]


def get_risk_label(probability: float) -> str:
    """
    Convert a default probability to a human-readable risk label.
    
    Low:    probability < 0.3
    Medium: 0.3 <= probability < 0.7
    High:   probability >= 0.7
    """
    if probability < config.RISK_LOW_THRESHOLD:
        return "Low"
    elif probability < config.RISK_HIGH_THRESHOLD:
        return "Medium"
    else:
        return "High"

"""
Unit tests for preprocessing.py -- feature engineering shared by the live
serving path (main.py) and the training path (scripts/train.py). A bug
here silently produces wrong model inputs on both sides at once.
"""
import numpy as np
import pandas as pd
import pytest

import config
from preprocessing import (
    engineer_champion_features,
    prepare_champion_input,
    engineer_challenger_features,
    prepare_challenger_input,
    get_risk_label,
)


# --------------------------------------------------------------------
# engineer_champion_features
# --------------------------------------------------------------------

def test_income_credit_ratio_computed_correctly():
    df = pd.DataFrame({"AMT_INCOME_TOTAL": [200000.0], "AMT_CREDIT_x": [500000.0]})
    out = engineer_champion_features(df)
    assert out["income_credit_ratio"].iloc[0] == pytest.approx(0.4)


def test_annuity_ratio_computed_correctly():
    df = pd.DataFrame({"AMT_ANNUITY": [25000.0], "AMT_CREDIT_x": [500000.0]})
    out = engineer_champion_features(df)
    assert out["annuity_ratio"].iloc[0] == pytest.approx(0.05)


def test_ratios_handle_division_by_zero_without_inf_or_nan():
    df = pd.DataFrame({
        "AMT_INCOME_TOTAL": [200000.0],
        "AMT_CREDIT_x": [0.0],
        "AMT_ANNUITY": [25000.0],
    })
    out = engineer_champion_features(df)
    assert out["income_credit_ratio"].iloc[0] == 0.0
    assert out["annuity_ratio"].iloc[0] == 0.0
    assert np.isfinite(out["income_credit_ratio"].iloc[0])


def test_age_computed_from_days_birth():
    df = pd.DataFrame({"DAYS_BIRTH": [-365 * 30]})  # 30 years old
    out = engineer_champion_features(df)
    assert out["age"].iloc[0] == pytest.approx(30.0, abs=0.01)


def test_existing_engineered_columns_are_not_overwritten():
    df = pd.DataFrame({
        "AMT_INCOME_TOTAL": [200000.0],
        "AMT_CREDIT_x": [500000.0],
        "income_credit_ratio": [0.99],  # user already supplied this
    })
    out = engineer_champion_features(df)
    assert out["income_credit_ratio"].iloc[0] == 0.99


# --------------------------------------------------------------------
# prepare_champion_input
# --------------------------------------------------------------------

@pytest.fixture
def feature_order(monkeypatch):
    order = [
        "AMT_INCOME_TOTAL", "AMT_CREDIT_x", "AMT_ANNUITY", "age", "income_credit_ratio",
    ]
    monkeypatch.setattr(config, "FEATURE_ORDER", order)
    return order


def test_prepare_champion_input_fills_missing_columns_with_zero(feature_order):
    df = pd.DataFrame({"AMT_INCOME_TOTAL": [100000.0], "AMT_CREDIT_x": [300000.0]})
    result = prepare_champion_input(df)
    assert list(result.columns) == feature_order
    assert result["AMT_ANNUITY"].iloc[0] == 0.0


def test_prepare_champion_input_orders_columns_per_feature_order(feature_order):
    # Deliberately shuffled input column order
    df = pd.DataFrame({
        "age": [40.0], "AMT_CREDIT_x": [500000.0], "AMT_INCOME_TOTAL": [200000.0],
        "AMT_ANNUITY": [25000.0],
    })
    result = prepare_champion_input(df)
    assert list(result.columns) == feature_order


def test_prepare_champion_input_raises_without_feature_order(monkeypatch):
    monkeypatch.setattr(config, "FEATURE_ORDER", [])
    with pytest.raises(ValueError):
        prepare_champion_input(pd.DataFrame({"AMT_INCOME_TOTAL": [1.0]}))


# --------------------------------------------------------------------
# engineer_challenger_features
# --------------------------------------------------------------------

def test_challenger_mapping_basic_fields():
    df = pd.DataFrame({
        "AMT_INCOME_TOTAL": [240000.0],
        "AMT_CREDIT_x": [600000.0],
        "AMT_ANNUITY": [30000.0],
        "DAYS_BIRTH": [-365 * 35],
        "DAYS_EMPLOYED": [-365 * 5],
    })
    out = engineer_challenger_features(df)
    assert out["Income"].iloc[0] == 240000.0
    assert out["LoanAmount"].iloc[0] == 600000.0
    assert out["Age"].iloc[0] == pytest.approx(35.0, abs=0.01)
    assert out["EmploymentYears"].iloc[0] == pytest.approx(5.0, abs=0.01)


def test_challenger_employment_years_caps_anomalous_home_credit_flag():
    """365243 days is Home Credit's well-known 'not currently employed' sentinel
    value for DAYS_EMPLOYED -- left unconverted, that's ~1000 years of employment.
    The mapping must cap it, not pass a nonsense number to the model."""
    df = pd.DataFrame({
        "AMT_INCOME_TOTAL": [100000.0], "AMT_CREDIT_x": [300000.0],
        "DAYS_EMPLOYED": [365243],
    })
    out = engineer_challenger_features(df)
    assert out["EmploymentYears"].iloc[0] <= 50


def test_challenger_credit_score_defaults_when_ext_source_missing():
    df = pd.DataFrame({"AMT_INCOME_TOTAL": [100000.0], "AMT_CREDIT_x": [300000.0]})
    out = engineer_challenger_features(df)
    assert out["CreditScore"].iloc[0] == 650.0


def test_challenger_credit_score_scales_ext_source_into_300_850_range():
    df = pd.DataFrame({
        "AMT_INCOME_TOTAL": [100000.0], "AMT_CREDIT_x": [300000.0],
        "EXT_SOURCE_1": [1.0], "EXT_SOURCE_2": [1.0], "EXT_SOURCE_3": [1.0],
    })
    out = engineer_challenger_features(df)
    assert out["CreditScore"].iloc[0] == pytest.approx(850.0)


def test_prepare_challenger_input_reorders_to_loaded_model_columns(monkeypatch):
    class StubModel:
        feature_names_in_ = np.array([
            "DTI", "Age", "Income", "LoanAmount", "EmploymentYears",
            "income_loan_ratio", "CreditScore", "loan_dti_ratio",
        ])
    monkeypatch.setattr(config, "GERMAN_MODEL", StubModel())
    df = pd.DataFrame({"AMT_INCOME_TOTAL": [100000.0], "AMT_CREDIT_x": [300000.0]})
    result = prepare_challenger_input(df)
    assert list(result.columns) == list(StubModel.feature_names_in_)


# --------------------------------------------------------------------
# get_risk_label
# --------------------------------------------------------------------

@pytest.mark.parametrize("probability,expected", [
    (0.0, "Low"),
    (0.29, "Low"),
    (0.3, "Medium"),
    (0.5, "Medium"),
    (0.69, "Medium"),
    (0.7, "High"),
    (1.0, "High"),
])
def test_risk_label_boundaries(probability, expected):
    assert get_risk_label(probability) == expected

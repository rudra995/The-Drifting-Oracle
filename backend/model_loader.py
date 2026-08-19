"""
Model and feature-order loading logic.
Called once at startup.
"""
import json
import os
import joblib
import config


def load_feature_order():
    """Read the expected feature order from features.txt."""
    for path in config.FEATURE_PATHS:
        if os.path.exists(path):
            with open(path, "r") as f:
                config.FEATURE_ORDER = [line.strip() for line in f if line.strip()]
            print(f"[loader] Feature order loaded from {path}: {config.FEATURE_ORDER}")
            return
    print("[loader] Warning: features.txt not found. Will use model's feature_names_in_ as fallback.")


def load_model():
    """Load the trained model from disk."""
    # Load primary model
    for path in config.MODEL_PATHS:
        if os.path.exists(path):
            try:
                config.MODEL = joblib.load(path)
                print(f"[loader] Model loaded successfully from {path} ({type(config.MODEL).__name__})")
                break
            except Exception as e:
                print(f"[loader] Error loading model from {path}: {e}")
    else:
        print("[loader] Warning: Model file missing or failed to load.")
        
    # Load fallback (German) model
    for path in config.GERMAN_MODEL_PATHS:
        if os.path.exists(path):
            try:
                config.GERMAN_MODEL = joblib.load(path)
                print(f"[loader] German model loaded successfully from {path} ({type(config.GERMAN_MODEL).__name__})")
                break
            except Exception as e:
                print(f"[loader] Error loading German model from {path}: {e}")
    else:
        print("[loader] Warning: German model file missing or failed to load.")

    load_model_metrics()


def load_model_metrics():
    """Load champion/challenger AUC/precision/recall/f1 written by scripts/train.py.

    Missing file (e.g. models shipped without a training run in this env)
    just leaves config.MODEL_METRICS empty -- /api/v1/models falls back to
    nulls rather than erroring.
    """
    for path in config.MODEL_METRICS_PATHS:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    config.MODEL_METRICS = json.load(f)
                print(f"[loader] Model metrics loaded from {path}: {config.MODEL_METRICS}")
                return
            except Exception as e:
                print(f"[loader] Error loading model metrics from {path}: {e}")
    print("[loader] Warning: model_metrics.json not found -- /api/v1/models will show null metrics.")

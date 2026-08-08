"""
Model and feature-order loading logic.
Called once at startup.
"""
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

"""
Builds real-world test fixtures from Kaggle's official application_test.csv
holdout set -- genuinely unseen applicants, never touched by training,
downloaded fresh via the Kaggle API for this test round.

Produces (in dataset/live_test/):
  real_applicants_batch.csv    -- 2,000-row realistic batch, cleaned schema
                                   (ready to upload as-is on the Upload page)
  real_applicants_small.csv    -- 20-row quick-smoke-test slice of the same
  raw_kaggle_schema_sample.csv -- 20 rows, UNTOUCHED Kaggle column names
                                   (AMT_CREDIT not AMT_CREDIT_x, CODE_GENDER
                                   not CODE_GENDER_M...) -- deliberately left
                                   raw to test how the app behaves on a CSV
                                   a schema-unaware user might actually upload
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

RAW_TEST_PATH = "dataset/raw/application_test.csv"
OUT_DIR = "dataset/live_test"

os.makedirs(OUT_DIR, exist_ok=True)

print(f"[build_live_test_dataset] Loading {RAW_TEST_PATH} ...")
df = pd.read_csv(RAW_TEST_PATH)
print(f"[build_live_test_dataset]   {len(df)} real, unseen applicants, {len(df.columns)} raw columns")

# ---- raw-schema sample (untouched) ----
raw_sample = df.sample(n=20, random_state=7)
raw_sample.to_csv(os.path.join(OUT_DIR, "raw_kaggle_schema_sample.csv"), index=False)
print(f"[build_live_test_dataset] Wrote raw_kaggle_schema_sample.csv ({len(raw_sample)} rows, untouched columns)")

# ---- cleaned schema (same reshape train.py applies) ----
df = df.rename(columns={"AMT_CREDIT": "AMT_CREDIT_x"})
df["CODE_GENDER_M"] = (df["CODE_GENDER"] == "M").astype(int)
df["CODE_GENDER_XNA"] = (df["CODE_GENDER"] == "XNA").astype(int)
df["FLAG_OWN_CAR_Y"] = (df["FLAG_OWN_CAR"] == "Y").astype(int)
df["FLAG_OWN_REALTY_Y"] = (df["FLAG_OWN_REALTY"] == "Y").astype(int)

full_batch = df.sample(n=2000, random_state=42)
full_batch.to_csv(os.path.join(OUT_DIR, "real_applicants_batch.csv"), index=False)
print(f"[build_live_test_dataset] Wrote real_applicants_batch.csv ({len(full_batch)} rows, cleaned schema)")

small = full_batch.sample(n=20, random_state=1)
small.to_csv(os.path.join(OUT_DIR, "real_applicants_small.csv"), index=False)
print(f"[build_live_test_dataset] Wrote real_applicants_small.csv ({len(small)} rows, cleaned schema)")

print("[build_live_test_dataset] Done.")

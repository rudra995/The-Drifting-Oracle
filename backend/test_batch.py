#!/usr/bin/env python
"""Test /predict_batch endpoint with file upload"""

import requests
import pandas as pd
import io

# Create test CSV data
csv_data = """external_source,external_source_0,days_birth,days_employed,income_total,income_type,family_status,housing_type,education_type
1,2,-10000,-5000,100000,Working,Married,House,Incomplete higher
1,2,-15000,-7000,150000,Working,Single,House,Secondary
1,2,-12000,-6000,120000,Retired,Married,Apartment,Tertiary"""

# Send as file
files = {'file': ('test.csv', io.BytesIO(csv_data.encode()), 'text/csv')}

try:
    response = requests.post('http://localhost:8000/predict_batch', files=files, timeout=60)
    result = response.json()
    
    print("=" * 60)
    print("✅ /predict_batch Response (SUCCESS)")
    print("=" * 60)
    print(f"Status: {result.get('status')}")
    print(f"Total Rows: {result.get('total_rows')}")
    print(f"Default Rate: {result.get('default_rate')}")
    print(f"Decision: {result.get('decision')}")
    print(f"LLM Used: {result.get('explanation_llm')}")
    print(f"Explanation Preview: {result.get('explanation', '')[:100]}...")
    print("\n✅ Batch prediction working correctly!")
    
except Exception as e:
    print(f"❌ Error: {str(e)[:200]}")

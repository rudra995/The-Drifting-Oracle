#!/usr/bin/env python
"""Test script for LLM clients"""

from llm_clients import call_gemini, call_llama
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("Testing Llama...")
print("=" * 60)
try:
    result, llm = call_llama("Say hello in 5 words")
    print(f"✅ Llama worked: {result[:100]}")
except Exception as e:
    print(f"❌ Llama failed: {str(e)[:200]}")

print("\n" + "=" * 60)
print("Testing Gemini...")
print("=" * 60)
try:
    result, llm = call_gemini("Say hello in 5 words")
    print(f"✅ Gemini worked: {result[:100]}")
except Exception as e:
    print(f"❌ Gemini failed: {str(e)[:200]}")

print("\n" + "=" * 60)
print("Testing generate_explanation...")
print("=" * 60)
from llm_explanation import generate_explanation
try:
    result = generate_explanation(0.75, 0.15, "no_drift")
    print(f"✅ generate_explanation worked:")
    print(f"   Explanation: {result['explanation'][:100]}")
    print(f"   LLM Used: {result['llm_used']}")
except Exception as e:
    print(f"❌ generate_explanation failed: {str(e)[:200]}")

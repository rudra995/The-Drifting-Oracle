"""
LLM Client Implementations
==========================

Low-level clients for Llama and Gemini APIs.
Handles HTTP communication, error handling, and response parsing.
Uses official Google Gemini API patterns from: https://ai.google.dev/gemini-api/docs
"""

from typing import Tuple
import requests
from google import genai
from google.genai import types

from llm_config import (
    LLAMA_ENDPOINT,
    LLAMA_MODEL,
    LLAMA_TIMEOUT,
    LLAMA_TEMPERATURE,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GEMINI_TEMPERATURE,
    GEMINI_MAX_TOKENS,
)

# Initialize Gemini client with API key
if GEMINI_API_KEY:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
else:
    gemini_client = None


def call_llama(prompt: str) -> Tuple[str, str]:
    """
    Call Llama via local endpoint (e.g., Ollama).
    
    Args:
        prompt: The prompt to send to Llama
    
    Returns:
        Tuple of (response_text, "llama")
    
    Raises:
        Exception: If API call fails or returns empty
    """
    try:
        payload = {
            "model": LLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "temperature": LLAMA_TEMPERATURE,
        }
        
        response = requests.post(LLAMA_ENDPOINT, json=payload, timeout=LLAMA_TIMEOUT)
        response.raise_for_status()
        
        result = response.json()
        explanation = result.get("response", "").strip()
        
        if explanation:
            print(f"[LLM] Used Llama successfully")
            return explanation, "llama"
        else:
            raise ValueError("Empty response from Llama")
            
    except Exception as e:
        error_msg = f"Llama endpoint '{LLAMA_ENDPOINT}' unreachable: {str(e)}"
        print(f"[LLM] {error_msg}")
        raise Exception(error_msg)


def call_gemini(prompt: str) -> Tuple[str, str]:
    """
    Call Gemini API as fallback using official Google Gemini SDK.
    Reference: https://ai.google.dev/gemini-api/docs/text-generation
    
    Args:
        prompt: The prompt to send to Gemini
    
    Returns:
        Tuple of (response_text, "gemini")
    
    Raises:
        Exception: If API call fails, returns empty, or API key not configured
    """
    try:
        if not gemini_client:
            raise ValueError("GEMINI_API_KEY not configured")
        
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=GEMINI_TEMPERATURE,
                max_output_tokens=GEMINI_MAX_TOKENS,
            ),
        )
        
        explanation = response.text.strip() if response.text else ""
        
        if explanation:
            print(f"[LLM] Used Gemini (fallback)")
            return explanation, "gemini"
        else:
            raise ValueError("Empty response from Gemini")
            
    except Exception as e:
        error_msg = f"Gemini API error: {str(e)}"
        if "GEMINI_API_KEY not configured" in str(e):
            error_msg = "Gemini API key not set. Set environment variable: GEMINI_API_KEY"
        print(f"[LLM] {error_msg}")
        raise Exception(error_msg)

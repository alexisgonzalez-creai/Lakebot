"""
Security Logic Module
Simple interface to local LLM for data masking and security analysis
"""

import pandas as pd
from typing import Dict, Any
import requests
import json
import subprocess
import os


def _find_ollama_path() -> str:
    """Find the Ollama executable path"""
    possible_paths = [
        'ollama',  # If in PATH
        os.path.expanduser('~/AppData/Local/Programs/Ollama/ollama.exe'),  # Windows default
        '/usr/local/bin/ollama',  # macOS/Linux
        '/usr/bin/ollama',  # Linux
    ]
    
    for path in possible_paths:
        try:
            result = subprocess.run([path, '--version'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                return path
        except:
            continue
    return None


def _ensure_ollama_ready() -> bool:
    """Ensure Ollama is running and llama2 model is available"""
    try:
        # Check if Ollama service is running
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            return False
            
        # Check if llama2 model is available
        models = response.json().get('models', [])
        model_names = [model['name'] for model in models]
        
        if not any('llama2' in name for name in model_names):
            # Try to pull the model
            ollama_path = _find_ollama_path()
            if ollama_path:
                subprocess.run([ollama_path, 'pull', 'llama2'], 
                             capture_output=True, text=True)
                return True
            return False
            
        return True
    except:
        return False


def _call_llm(prompt: str) -> str:
    """Call local LLM for analysis"""
    try:
        url = "http://localhost:11434/api/generate"
        data = {
            "model": "llama2",
            "prompt": prompt,
            "stream": False
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        return result.get('response', '')
    except:
        return ""


def mask_df(df: pd.DataFrame, prompt: str) -> pd.DataFrame:
    """
    Analyze DataFrame for sensitive information and mask sensitive columns
    
    Args:
        df: DataFrame to analyze and mask
        prompt: User prompt for context
        
    Returns:
        DataFrame with sensitive columns masked
    """
    # Check if Ollama is available
    if not _ensure_ollama_ready():
        print("⚠️  Ollama not available - returning original DataFrame")
        return df
    
    # Prepare data for analysis
    df_sample = df.head(3).to_string()
    columns_info = list(df.columns)
    
    # Create analysis prompt
    analysis_prompt = f"""
    Analyze this DataFrame for sensitive information:
    
    Columns: {columns_info}
    Sample data:
    {df_sample}
    User query context: {prompt}
    
    Identify sensitive columns (SSN, credit cards, emails, phone numbers, addresses, etc.)
    
    Respond with ONLY a JSON list of sensitive column names:
    ["column1", "column2", ...]
    
    If no sensitive columns found, respond with: []
    """
    
    # Get LLM analysis
    llm_response = _call_llm(analysis_prompt)
    
    # Parse response and mask columns
    df_masked = df.copy()
    sensitive_columns = []
    
    try:
        # Try to parse JSON response
        sensitive_columns = json.loads(llm_response.strip())
        if isinstance(sensitive_columns, list):
            for col in sensitive_columns:
                if col in df_masked.columns:
                    df_masked[col] = '[MASKED]'
                    print(f"🔒 Masked sensitive column: {col}")
    except:
        # Fallback: use simple keyword matching
        sensitive_keywords = ['ssn', 'social', 'credit', 'card', 'email', 'phone', 'address', 'password', 'secret']
        for col in df_masked.columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in sensitive_keywords):
                df_masked[col] = '[MASKED]'
                print(f"🔒 Masked potentially sensitive column: {col}")
    
    return df_masked


def analyze_query_security(query: str) -> Dict[str, Any]:
    """
    Analyze user query for sensitive information requests
    
    Args:
        query: User query to analyze
        
    Returns:
        Dictionary with analysis results
    """
    if not _ensure_ollama_ready():
        return {
            "risk_level": "low",
            "sanitized_query": query,
            "recommendations": ["Ollama not available - using fallback mode"]
        }
    
    prompt = f"""
    Analyze this user query for sensitive information requests:
    
    Query: "{query}"
    
    Identify:
    1. Sensitive keywords or phrases
    2. Intent to access sensitive data
    3. Risk level (low/medium/high)
    4. Recommended query sanitization
    
    Respond in JSON format:
    {{
        "sensitive_keywords": ["list of sensitive keywords found"],
        "intent_risk": "low/medium/high",
        "recommendations": ["list of recommended actions"],
        "sanitized_query": "suggested sanitized version of the query"
    }}
    """
    
    llm_response = _call_llm(prompt)
    
    try:
        analysis = json.loads(llm_response)
        return analysis
    except:
        return {
            "sensitive_keywords": [],
            "intent_risk": "low",
            "recommendations": ["LLM analysis failed - using default safe mode"],
            "sanitized_query": query
        }
"""
QA Agent Model Manager - Manages LLM models for QA graph generation
Simplified version of UNO's ModelManager focused on QA needs
"""

import os
import json
import yaml
from pathlib import Path
from google import genai
from google.genai import types
from dotenv import load_dotenv
import boto3
from botocore.config import Config
from pydantic import BaseModel
from typing import Dict, Any, Union, List

# Load environment variables
load_dotenv()

# Define paths
ROOT = Path(__file__).parent.parent
MODELS_JSON = ROOT / "config" / "models.json"
PROFILE_YAML = ROOT / "config" / "profiles.yaml"

class ModelManager:
    """
    Manages LLM model configuration and selection for QA Agent.
    Simplified version of UNO's ModelManager.
    """
    
    def __init__(self):
        """Initialize ModelManager by loading configurations"""
        self.config = json.loads(MODELS_JSON.read_text())
        self.profile = yaml.safe_load(PROFILE_YAML.read_text())
        
        self.text_model_key = self.profile["llm"]["text_generation"]
        self.model_info = self.config["models"][self.text_model_key]
        self.model_type = self.model_info["type"]
    
    def get_model_id(self) -> str:
        """Get the model ID"""
        return self.model_info["model"]

class Gemini:
    """
    Gemini LLM client for QA Agent.
    Simplified version of UNO's Gemini class with graph generation capabilities.
    """
    
    def __init__(self, model_id: str):
        """Initialize Gemini client"""
        apikey = os.environ.get("GEMINI_API_KEY")
        self.client = genai.Client(api_key=apikey)
        self.model_id = model_id
    
    def generate_content(self, system_prompt: str) -> Dict[str, Union[str, int]]:
        """
        Generate text content from Gemini model.
        
        Args:
            system_prompt: The prompt to send to the model
            
        Returns:
            Dict with content and token count
        """
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=[system_prompt]
            )
            return {
                "content": self._clean_response(response.text),
                "token_count": response.usage_metadata.total_token_count
            }
        except Exception as e:
            print(f"Gemini content generation failed: {e}")
            raise
    
    def generate_json(self, system_prompt: str, response_schema: BaseModel) -> Dict[str, Union[str, int]]:
        """
        Generate JSON content using Gemini with Pydantic schema.
        
        Args:
            system_prompt: The prompt for generation
            response_schema: Pydantic model schema
            
        Returns:
            Dict with content and token count
        """
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=[system_prompt],
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': response_schema,
                }
            )
            return {
                "content": response.text,
                "token_count": response.usage_metadata.total_token_count
            }
        except Exception as e:
            print(f"Gemini JSON generation failed: {e}")
            raise
    
    def _clean_response(self, text: str) -> str:
        """
        Clean response text by removing markdown code fences.
        
        Args:
            text: Raw response text
            
        Returns:
            Cleaned text
        """
        if text.startswith('```') and text.endswith('```'):
            lines = text.split('\n')
            if len(lines) > 2:
                return '\n'.join(lines[1:-1])
        return text

class Bedrock:
    """
    Bedrock LLM client for QA Agent.
    Simplified version of UNO's Bedrock class.
    """
    
    def __init__(self, model_id: str):
        """Initialize Bedrock client"""
        config = Config(read_timeout=900)
        self.client = boto3.client(
            service_name="bedrock-runtime",
            region_name=os.getenv("AWS_REGION"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            config=config
        )
        self.model_id = model_id
        
        # Also initialize Gemini for JSON generation (Bedrock fallback)
        apikey = os.environ.get("GEMINI_API_KEY")
        self.gclient = genai.Client(api_key=apikey)
    
    def generate_json(self, system_prompt: str, response_schema: BaseModel) -> Dict[str, Union[str, int]]:
        """
        Generate JSON content using Bedrock (with Gemini fallback).
        
        Args:
            system_prompt: The prompt for generation
            response_schema: Pydantic model schema
            
        Returns:
            Dict with content and token count
        """
        try:
            # Use Gemini for JSON generation (more reliable)
            response = self.gclient.models.generate_content(
                model="gemini-2.5-pro",
                contents=[system_prompt],
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': response_schema,
                }
            )
            return {
                "content": response.text,
                "token_count": response.usage_metadata.total_token_count
            }
        except Exception as e:
            print(f"Bedrock JSON generation failed: {e}")
            raise
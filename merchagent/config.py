"""
This module defines the model configurations used by the various agents
in the brand analysis system.
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Modelconfig:
    """Model configuration class for ADK agents"""
    
    # Default models - adjust these based on your available models
    flash_lite_model = "gemini-2.0-flash-lite-001"  # For fast, lightweight tasks
    pro_model = "gemini-2.5-pro"          # For complex analysis tasks
    flash_model ="gemini-2.5-flash"
    flash_image = "gemini-2.0-flash-preview-image-generation"
    imagen4_fast ="imagen-4.0-fast-generate-preview-06-06"
    imagen4_ultra ="imagen-4.0-ultra-generate-preview-06-06"
    imagen3 ="imagen-3.0-generate-002"
    

    # Model settings
    temperature = 0.1  # Low temperature for consistent analysis
    max_tokens = 8192  # Maximum output tokens
    

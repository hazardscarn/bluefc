import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class Modelconfig:
    """Configuration for Agent System"""
    
    # Google Cloud Configuration
    project_id: str = "bluefc"
    location: str = "us-central1"
    
    # Model Configuration
    flash_model: str = "gemini-2.5-flash" 
    pro_model: str = "gemini-2.5-pro"  
    flash_lite_model: str = "gemini-2.0-flash-lite-001"
    imagen_4_generate: str = "imagen-4.0-generate-preview-06-06"
    imagen_4_fast: str = "imagen-4.0-fast-generate-preview-06-06"

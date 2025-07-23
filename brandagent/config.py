"""
Model Configuration for Brand Analysis Agents

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
    
    # Alternative configurations if you have different models available
    @classmethod
    def get_flash_model(cls):
        """Get the flash model, with fallback options"""
        return os.getenv("FLASH_MODEL", cls.flash_lite_model)
    
    @classmethod 
    def get_pro_model(cls):
        """Get the pro model, with fallback options"""
        return os.getenv("PRO_MODEL", cls.pro_model)
    
    # Model settings
    temperature = 0.1  # Low temperature for consistent analysis
    max_tokens = 8192  # Maximum output tokens
    
    # Usage guidelines:
    # - flash_lite_model: Brand detection, simple analysis, coordination
    # - pro_model: Complex report generation, detailed analysis
    
    @classmethod
    def print_config(cls):
        """Print current model configuration"""
        print("🔧 MODEL CONFIGURATION")
        print("-" * 30)
        print(f"Flash Model: {cls.get_flash_model()}")
        print(f"Pro Model: {cls.get_pro_model()}")
        print(f"Temperature: {cls.temperature}")
        print(f"Max Tokens: {cls.max_tokens}")
        print()

# For backward compatibility
flash_lite_model = Modelconfig.flash_lite_model
pro_model = Modelconfig.pro_model

if __name__ == "__main__":
    Modelconfig.print_config()
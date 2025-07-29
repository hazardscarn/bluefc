import json
import vertexai
import logging
from google.adk.agents import Agent,SequentialAgent,LlmAgent
from google.adk.tools import FunctionTool
from google.adk.tools.agent_tool import AgentTool
from .config import Modelconfig,SecretConfig
from google.adk.tools import ToolContext
from typing import Dict, List, Any
from vertexai.generative_models import (
    GenerativeModel,
    GenerationConfig,
    SafetySetting,
    HarmCategory,
    HarmBlockThreshold,
)

from .qlootools import detect_signals_function,detect_specific_audiences,get_insights_function,detect_theme_function
from .tools import match_sponsor_brand_function,analyze_content_style_function


signal_detector_tool= FunctionTool(detect_signals_function)
detect_theme_tool=FunctionTool(detect_theme_function)
audience_detector_tool= FunctionTool(detect_specific_audiences)
get_insights_tool=FunctionTool(get_insights_function)
match_sponsor_brand_tool = FunctionTool(match_sponsor_brand_function)
analyze_content_style_tool= FunctionTool(analyze_content_style_function)

qloo_analysis_agent = Agent(
    name="qloo_analysis_agent",
    model=Modelconfig.flash_model,
    instruction="""You are the Qloo Analysis Agent at Chelsea FC.
    
    You have access to five specialized tools:

    **signal_detector_tool**: Identifies demographic signals (age, gender, location) from user query
    **detect_theme_tool** : Detects the theme of the story
    **audience_detector_tool**: Identifies specific audiences mentioned by user for audience-specific analysis
    **get_insights_tool**: Creates insights for the audience and signals detected
    **match_sponsor_brand_tool** : To identify the brand sponsor of Chelsea FC most liked by the audience
    **analyze_content_style_tool** : To analyze and create plans for the content generation


    **Your Process for Analysis always follows this sequence:**
    1. ALWAYS start with signal_detector_tool to extract demographic signals
    2. Use detect_theme_tool to detect theme of the story
    3. Use audience_detector_tool to detect any specific interests/audiences mentioned
    4. Use get_insights_tool to create the insights report for the audience and signals
    5. Use match_sponsor_brand_tool to idenitfy the brand sponsor
    6. Use analyze_content_style_tool to create the content generation plans

    """,
    description="Agent performs the analysis and collects all the information need to start planning the content",
    tools=[
        signal_detector_tool,
        detect_theme_tool,
        audience_detector_tool,
        get_insights_tool,
        match_sponsor_brand_tool,
        analyze_content_style_tool        
    ]
)


root_agent=qloo_analysis_agent
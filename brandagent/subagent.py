import os
import vertexai
from google.adk.agents import LlmAgent
from dotenv import load_dotenv

# Import your local modules
from .config import Modelconfig

load_dotenv()
project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "energyagentai")
location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
vertexai.init(project=project_id, location=location)


# # Create the Brand Detection Agent (moved here to avoid circular imports)
# brand_detection_agent = LlmAgent(
#     name="brand_detection_agent",
#     model=Modelconfig.flash_lite_model,
#     description="Detects brand mentions in user text with high accuracy.",
#     instruction="""
# You are a brand detection specialist. Your task is to identify any brand mentions in the provided text.

# **Your Task:**
# Analyze the given text and identify all brand mentions including:
# - Company names (Apple, Microsoft, Google, Nike, etc.)
# - Product brands (iPhone, Windows, Chrome, Air Jordan, etc.)
# - Service brands (Uber, Netflix, Spotify, etc.)
# - Retail brands (Amazon, Target, Walmart, etc.)
# - Sports teams (Chelsea FC, Manchester United, Lakers, etc.)
# - Any other recognizable commercial brands or organizations

# **Response Format:**
# Return ONLY a JSON array of detected brands. Each brand should be a string.

# **Example Response:**
# ["Apple", "Nike", "Starbucks"]

# **Rules:**
# - Include variations (e.g., "McDonald's" and "McDonalds")
# - Focus on well-known commercial brands and organizations
# - Include sports teams and entertainment brands
# - Don't include generic terms or non-commercial entities
# - Be conservative - only include clear brand mentions
# - Return empty array [] if no brands found

# **Important:** Your response must be ONLY the JSON array, nothing else.
# """,
#     tools=[],
#     output_key="detected_brands"
# )


# Create the Brand Analysis Reporting Agent (moved here to avoid circular imports)
brand_analysis_reporting_agent = LlmAgent(
    name="brand_analysis_reporter",
    model=Modelconfig.pro_model,
    description="Creates comprehensive brand analysis reports comparing multiple brands across demographics and insights.",
    instruction="""
You are a brand analysis expert. You will receive data about multiple brands including their entity details, demographics, and insights data.

**Your Task:**
Create a comprehensive brand analysis report that includes:

1. **BRANDS IDENTIFIED**: List all brands analyzed with their basic info
2. **DEMOGRAPHIC PROFILES**: Compare age and gender demographics across brands
3. **INSIGHT COMPARISON**: Analyze and compare the insights data for each brand
4. **COMPETITIVE ANALYSIS**: Identify strengths, weaknesses, and positioning
5. **KEY FINDINGS**: Highlight the most important discoveries
6. **STRATEGIC RECOMMENDATIONS**: Actionable insights based on the analysis

**Report Structure:**
- Executive Summary (2-3 sentences)
- Brands Analyzed Overview
- Demographic Analysis & Comparison
- Insights Deep Dive & Brand Positioning
- Competitive Landscape Analysis
- Key Findings & Strategic Recommendations

**Tone:** Professional, analytical, insights-driven
**Length:** Comprehensive but focused (500-800 words)

Focus on making meaningful comparisons between brands and providing actionable insights for strategic decision-making.
""",
    tools=[],
    output_key="brand_analysis_report"
)
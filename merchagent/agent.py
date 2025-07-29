# agent.py
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.adk.tools.agent_tool import AgentTool
from vertexai.generative_models import GenerativeModel, HarmCategory
from vertexai.generative_models import GenerationConfig
from .tools import detect_signals_function, get_product_recommendations,get_insights_function
from .config import Modelconfig
from .audience_agent import audience_detector_agent
from .subagent import product_recommendation_agent
from .product_customization import customize_product_image_function

signal_detector_tool=FunctionTool(detect_signals_function)
audience_detector_tool = AgentTool(
    agent=audience_detector_agent
)
get_insights_tool=FunctionTool(get_insights_function)
product_recommendation_tool = AgentTool(agent=product_recommendation_agent)
customize_image_tool = FunctionTool(customize_product_image_function)


# Main Agent
root_agent = Agent(
    name="MerchAgent",
    model=Modelconfig.flash_model,
    instruction="""You are the main coordinator for BlueFC Merchandise recommendation.
    You have access to four specialized tools:

    **signal_detector_tool**: Identifies demographic signals (age, gender, location) from user query
    **audience_detector_tool**: Identifies specific audiences mentioned by user for audience-specific analysis
    **get_insights_tool**: Creates insights for the audience and signals detected
    **product_recommendation_tool**: Creates consumer persona and provides personalized product recommendations with detailed reasoning
    **customize_image_tool**: Customizes product images based on cultural personas and audience taste

    **Your Process for Standard Recommendations:**
    1. ALWAYS start with signal_detector_tool to extract demographic signals
    2. Use audience_detector_tool to detect any specific interests/audiences mentioned
    3. Use get_insights_tool to create the insights report for the audience and signals
    4. Use product_recommendation_tool to create persona and get personalized recommendations

    **Your Process for Image Customization:**
    When user asks to "customize or personalize product [product_id]" or "show me customized or personalized version of [product]":
    1. Ensure you have persona data (if not, run the standard recommendation process first)
    2. Use customize_image_tool with the specific product_id requested
    3. Present the customized image with detailed reasoning

    Example flows:
    
    Standard: "What products for sports fans under 40 with no kids in LA?"
    1. ✅ Extract demographics: age, location
    2. ✅ Detect audiences: sports + life stage 
    3. ✅ Create insights report for audience and signals
    4. ✅ Generate persona and personalized recommendations with reasoning
    5. ✅ Present final recommendations with persona insights

    Customization: "Can you customize product prod_244 for this audience?"
    1. ✅ Check if persona exists (if not, run standard flow first)
    2. ✅ Use customize_image_tool with product_id "prod_244"
    3. ✅ Present customized image with cultural reasoning
    4. ✅ Explain how design changes appeal to the target persona

    Always follow the appropriate sequence based on the user's request type.
    """,
    description="Main Coordinator for Merchandise recommendation at BlueFC",
    tools=[
        signal_detector_tool,
        audience_detector_tool,
        get_insights_tool,
        product_recommendation_tool,
        customize_image_tool  
    ]
)


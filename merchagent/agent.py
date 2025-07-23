# agent.py
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.adk.tools.agent_tool import AgentTool
from .tools import detect_signals_function, get_product_recommendations,get_insights_function
from .config import Modelconfig
from .audience_agent import audience_detector_agent
from .subagent import product_recommendation_agent

signal_detector_tool=FunctionTool(detect_signals_function)
audience_detector_tool = AgentTool(
    agent=audience_detector_agent
)
get_insights_tool=FunctionTool(get_insights_function)
product_recommendation_tool = AgentTool(agent=product_recommendation_agent)


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

    **Your Process:**
    1. ALWAYS start with signal_detector_tool to extract demographic signals
    2. Use audience_detector_tool to detect any specific interests/audiences mentioned
    3. Use get_insights_tool to create the insights report for the audience and signals
    4. Use product_recommendation_tool to create persona and get personalized recommendations

    The product_recommendation_tool will:
    - Create a detailed consumer persona from the insights
    - Get relevant product recommendations
    - Provide reasoning for why each product appeals to the persona

    Example flow:
    User: "What products for sports fans under 40 with no kids in LA?"
    1. ✅ Extract demographics: age, location
    2. ✅ Detect audiences: sports + life stage 
    3. ✅ Create insights report for audience and signals
    4. ✅ Generate persona and personalized recommendations with reasoning
    5. ✅ Present final recommendations with persona insights and product appeal analysis

    Follow this sequence for every recommendation request.
    """,
    description="Main Coordinator for Merchandise recommendation at BlueFC",
    tools=[
        signal_detector_tool,
        audience_detector_tool,
        get_insights_tool,
        product_recommendation_tool
    ]
)


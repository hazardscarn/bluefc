# product_recommendation_agent.py
from google.adk.agents import Agent,SequentialAgent,LlmAgent
from google.adk.tools import FunctionTool
from google.adk.tools.agent_tool import AgentTool
from .config import Modelconfig
from .tools import get_product_recommendations
from google.adk.tools import ToolContext
from typing import Dict, List, Any
import json
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
import logging
from vertexai.generative_models import (
    GenerativeModel,
    GenerationConfig,
    SafetySetting,
    HarmCategory,
    HarmBlockThreshold,
)
from vertexai.generative_models import GenerationConfig

step_logger = logging.getLogger("AGENT_STEPS")


def create_persona_function(tool_context: ToolContext) -> Dict[str, Any]:
    """Create a comprehensive consumer persona from audience insights for Chelsea FC merchandise recommendations.
    
    This function analyzes cultural preference data, demographic signals, and audience insights to create
    a detailed consumer persona that will guide merchandise recommendations. The persona includes 
    demographic profiles, cultural values, economic behaviors, and Chelsea-specific preferences.
    
    Args:
        tool_context (ToolContext): ADK tool context containing session state with required insights data.
                                  Expected state keys:
                                  - 'brand_insight': Brand preference insights
                                  - 'tag_insight': Lifestyle tag insights
                                  - 'movie_insight': Entertainment preferences
                                  - 'artist_insight': Music preferences
                                  - 'podcast_insight': Audio content preferences
                                  - 'person_insight': Public figure preferences
                                  - 'detected_signals': Demographic signals (age, gender, location)
                                  - 'detected_audience_names': List of detected audience segments
    
    Returns:
        Dict[str, Any]: Result dictionary containing:
            - 'success' (bool): True if persona creation succeeded
            - 'persona_created' (bool): True if persona was successfully created
            - 'persona_name' (str): Generated persona name
            - 'message' (str): Status message
            - 'error' (str): Error message if creation failed
    
    State Updates:
        Updates tool_context.state with the following keys:
        - 'persona_name': Creative name for the persona
        - 'persona_description': 2-3 sentence persona summary
        - 'audience_profile': Demographics, lifestyle, and values
        - 'cultural_values': Entertainment preferences and brand affinities
        - 'economic_values': Spending patterns and price sensitivity
        - 'merchandise_preferences': Chelsea product preferences
        - 'purchase_motivations': Key buying decision factors
    
    Raises:
        Exception: If LLM generation fails or JSON parsing fails
    
    Example:
        >>> result = create_persona_function(tool_context)
        >>> if result['success']:
        ...     persona_name = tool_context.state['persona_name']
        ...     print(f"Created persona: {persona_name}")
    
    Note:
        Requires brand_insight and tag_insight to be present in tool_context.state.
        Uses Gemini 2.5 Flash model for persona generation with JSON output format.
    """
    step_logger.info("STEP 4a: 👤 Creating consumer persona from insights...")
    
    # Check for insights
    brand_insight = tool_context.state.get('brand_insight', '')
    tag_insight = tool_context.state.get('tag_insight', '')
    
    if not brand_insight or not tag_insight:
        step_logger.error("   ❌ Missing required insights for persona creation")
        return {"error": "Missing insights"}
    
    step_logger.info(f"   📝 Using {len(brand_insight)} chars of brand data, {len(tag_insight)} chars of tag data")
    
    # Gather all insights
    insights_data = {
        "brand_insights": tool_context.state.get('brand_insight', ''),
        "movie_insights": tool_context.state.get('movie_insight', ''),
        "artist_insights": tool_context.state.get('artist_insight', ''),
        "podcast_insights": tool_context.state.get('podcast_insight', ''),
        "person_insights": tool_context.state.get('person_insight', ''),
        "tag_insights": tool_context.state.get('tag_insight', ''),
        "detected_signals": tool_context.state.get('detected_signals', {}),
        "detected_audiences": tool_context.state.get('detected_audience_names', [])
    }
    
    # Enhanced prompt using best practices (Persona + Task + Context + Format)
    prompt = f"""You are a consumer insights specialist at Chelsea FC with expertise in fan behavior and merchandise psychology.

TASK: Create a comprehensive consumer persona for Chelsea FC merchandise targeting based on the provided audience insights.

CONTEXT: You have detailed audience signals and cultural preference data showing what this audience likes in terms of brands, movies, music, and lifestyle tags. This persona will guide our merchandise recommendations to maximize fan engagement and purchase likelihood.

INSIGHTS DATA:
{json.dumps(insights_data, indent=2)}

REQUIRED OUTPUT FORMAT (JSON):
{{
    "persona_name": "Creative name that captures the essence of this fan segment",
    "persona_description": "2-3 sentence summary of who this person is",
    "audience_profile": {{
        "demographics": "Age, gender, location characteristics",
        "lifestyle": "How they live, work, and spend leisure time",
        "values": "What matters most to them as people and fans"
    }},
    "cultural_values": {{
        "entertainment_preferences": "What movies, music, shows they enjoy and why",
        "brand_affinities": "Types of brands they connect with and values they represent",
        "social_behaviors": "How they interact with communities and express identity"
    }},
    "economic_values": {{
        "spending_patterns": "How they approach purchases and what drives buying decisions",
        "value_perception": "What makes them feel a purchase is worthwhile",
        "price_sensitivity": "Their relationship with pricing and premium products"
    }},
    "chelsea_merchandise_preferences": {{
        "product_categories": "Types of Chelsea FC products they'd be most interested in",
        "design_preferences": "Visual styles, colors, fits that appeal to them",
        "functional_needs": "How they'd use products in their daily life",
        "emotional_drivers": "What Chelsea products mean to them beyond functionality"
    }},
    "purchase_motivations": [
        "Key factors that would drive them to buy Chelsea merchandise",
        "Emotional and rational triggers for purchase decisions"
    ]
}}

GUIDELINES:
- Base insights on the actual data provided, not assumptions
- Focus on how cultural preferences translate to merchandise appeal
- Consider both rational and emotional purchase drivers
- Keep descriptions specific and actionable for product recommendations
- Ensure persona aligns with Chelsea FC brand values and fan culture
- You will always create persona from the insights and signals and demographics provided
"""

    try:
        model = GenerativeModel(
            Modelconfig.flash_model,
            generation_config=GenerationConfig(
                temperature=0.2,
                max_output_tokens=20000,
                response_mime_type="application/json"
            ),
            safety_settings={
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        )
        
        response = model.generate_content(prompt)
        persona_data = json.loads(response.text.strip())
        
        # Store different components in state as requested
        tool_context.state['persona_name'] = persona_data.get('persona_name', '')
        tool_context.state['persona_description'] = persona_data.get('persona_description', '')
        tool_context.state['audience_profile'] = persona_data.get('audience_profile', {})
        tool_context.state['cultural_values'] = persona_data.get('cultural_values', {})
        tool_context.state['economic_values'] = persona_data.get('economic_values', {})
        tool_context.state['merchandise_preferences'] = persona_data.get('chelsea_merchandise_preferences', {})
        tool_context.state['purchase_motivations'] = persona_data.get('purchase_motivations', [])
        #tool_context.state['full_persona'] = persona_data
        step_logger.info(f"   ✅ Created persona: '{persona_data.get('persona_name', '')}'")
        
        return {
            "success": True,
            "persona_created": True,
            "persona_name": persona_data.get('persona_name', ''),
            "message": "Consumer persona created and stored in state"
        }
        
    except Exception as e:
        return {"error": f"Persona creation failed: {str(e)}"}


def generate_product_reasoning_function(tool_context: ToolContext) -> Dict[str, Any]:
    """Generate detailed reasoning for why recommended products appeal to a specific consumer persona.
    
    This function analyzes the relationship between a consumer persona and Chelsea FC product 
    recommendations, providing strategic insights into why each product would appeal to the target
    audience. The analysis covers cultural connections, functional benefits, and purchase triggers.
    
    Args:
        tool_context (ToolContext): ADK tool context containing session state with required data.
                                  Expected state keys:
                                  - 'persona_name': Name of the consumer persona
                                  - 'persona_description': Description of the persona
                                  - 'audience_profile': Demographic and lifestyle profile
                                  - 'cultural_values': Entertainment and brand preferences
                                  - 'economic_values': Spending patterns and price sensitivity
                                  - 'merchandise_preferences': Chelsea product preferences
                                  - 'purchase_motivations': Key buying decision factors
                                  - 'recommendations': List of product recommendations
    
    Returns:
        Dict[str, Any]: Result dictionary containing:
            - 'success' (bool): True if reasoning generation succeeded
            - 'reasoning_generated' (bool): True if reasoning was successfully generated
            - 'products_analyzed' (int): Number of products analyzed
            - 'message' (str): Status message
            - 'error' (str): Error message if generation failed
    
    State Updates:
        Updates tool_context.state with:
        - 'product_reasoning': Dictionary containing detailed reasoning for each product
          with structure:
          {
              "product_reasoning": [
                  {
                      "product_rank": int,
                      "product_name": str,
                      "appeal_factors": List[str],
                      "persona_alignment": str,
                      "purchase_triggers": str
                  }
              ]
          }
    
    Raises:
        Exception: If LLM generation fails or JSON parsing fails
    
    Example:
        >>> result = generate_product_reasoning_function(tool_context)
        >>> if result['success']:
        ...     reasoning = tool_context.state['product_reasoning']
        ...     for product in reasoning['product_reasoning']:
        ...         print(f"Product: {product['product_name']}")
        ...         print(f"Why it appeals: {product['appeal_factors']}")
    
    Note:
        Requires persona data and product recommendations to be present in tool_context.state.
        Analyzes up to 6 products. Uses Gemini 2.0 Flash Lite model for efficient reasoning generation.
    """
    step_logger.info("STEP 4c: 🛍️  Getting product reasoning...")
    
    # Check for required data
    persona = {
        "persona_name": tool_context.state.get('persona_name', ''),
        "persona_description": tool_context.state.get('persona_description', ''),
        "audience_profile": tool_context.state.get('audience_profile', {}),
        "cultural_values": tool_context.state.get('cultural_values', {}),
        "economic_values": tool_context.state.get('economic_values', {}),
        # "merchandise_preferences": tool_context.state.get('merchandise_preferences', {}),
        # "purchase_motivations": tool_context.state.get('purchase_motivations', [])
    }
    recommendations = tool_context.state.get('recommendations')
    
    if not persona:
        step_logger.info("No Persona Found")
        return {"error": "No persona found. Create persona first."}
    
    if not recommendations:
        step_logger.info("No recommendations Found")
        return {"error": "No product recommendations found. Get recommendations first."}
    
    # Prepare product data for analysis
    products_summary = []
    for i, product in enumerate(recommendations[:6], 1):  # Limit to top 6
        products_summary.append({
            "rank": i,
            "name": product.get('title', ''),
            "description": product.get('description', ''),
            "category": product.get('category', ''),
            "price_range": product.get('price_tier', ''),
            "key_features": product.get('features', [])
        })
    
    # Enhanced reasoning prompt
    prompt = f"""You are a merchandise strategist at Chelsea FC specializing in fan psychology and product appeal analysis.

TASK: Analyze why each recommended product would appeal to our target persona and provide compelling short reasoning for each recommendation.

CONTEXT: 
PERSONA: {json.dumps(persona, indent=2)}

PRODUCTS TO ANALYZE: {json.dumps(products_summary, indent=2)}

REQUIRED OUTPUT FORMAT (JSON):
{{
    "product_reasoning": [
        {{
            "product_rank": 1,
            "product_name": "Product name",
            "persona_alignment": "How this product matches their persona, cultural values and preferences",
        }}
    ]
}}

GUIDELINES:
- Connect product features to persona's cultural and economic values
- Reference specific insights from the persona data
- Provide actionable insights for marketing and sales"""

    try:
        model = GenerativeModel(
            Modelconfig.flash_lite_model,
            generation_config=GenerationConfig(
                temperature=0.3,
                max_output_tokens=8000,
                response_mime_type="application/json"
            ),            safety_settings={
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        )
        
        response = model.generate_content(prompt)
        reasoning_data = json.loads(response.text.strip())
        
        # Store reasoning in state
        tool_context.state['product_reasoning'] = reasoning_data
        
        return {
            "success": True,
            "reasoning_generated": True,
            "products_analyzed": len(reasoning_data.get('product_reasoning', [])),
            "message": "Product reasoning analysis completed"
        }
        
    except Exception as e:
        return {"error": f"Reasoning generation failed: {str(e)}"}


# # Create the persona agent
# persona_agent = Agent(
#     name="PersonaAgent",
#     model=Modelconfig.flash_model,
#     instruction="""You are a consumer insights specialist at Chelsea FC.
    
#     Your role is to analyze audience insights and create detailed consumer personas that will guide merchandise recommendations.
    
#     Use create_persona_tool to build comprehensive personas from cultural insights data.
#     Focus on understanding what drives this audience's purchasing decisions and how they connect with Chelsea FC.
#     You will create a persona using create_persona_tool always. You don't say I can't create a persona.
#     """,
#     description="Creates consumer personas from audience insights for merchandise targeting",
#     tools=[create_persona_tool]
# )
create_persona_tool=FunctionTool(create_persona_function)
get_product_recommendations_subtool=FunctionTool(get_product_recommendations)
generate_product_reasoning_tool=FunctionTool(generate_product_reasoning_function)


# persona_agent = LlmAgent(
#     name="PersonaCreator",
#     model=Modelconfig.flash_model,
#     instruction="Use the create_persona_tool to create a consumer persona. Call the tool with no parameters." \
#     "Your task is to use create_persona_tool to create a consumer persona.",
#     description="Creates consumer personas from audience insights",
#     tools=[create_persona_tool]
# )

# recommendations_agent = LlmAgent(
#     name="RecommendationsFetcher", 
#     model=Modelconfig.flash_model,
#     instruction="Use the get_product_recommendations tool to get product recommendations. Call the tool with no parameters.",
#     description="Fetches product recommendations based on persona",
#     tools=[get_product_recommendations_subtool]
# )

# reasoning_agent = LlmAgent(
#     name="ReasoningGenerator",
#     model=Modelconfig.flash_model, 
#     instruction="Use the generate_product_reasoning_tool to analyze why each product appeals to the persona. Call the tool with no parameters.",
#     description="Generates reasoning for product recommendations",
#     tools=[generate_product_reasoning_tool]
# )

# product_recommendation_agent = SequentialAgent(
#     name="ProductRecommendationAgent",
#     description="Coordinates persona creation, product recommendations, and reasoning generation in sequence",
#     sub_agents=[           # NOTE: sub_agents, not tools
#         persona_agent,           # Step 1: Create persona
#         recommendations_agent,   # Step 2: Get recommendations  
#         reasoning_agent         # Step 3: Generate reasoning
#     ]
# )


# Create the main product recommendation agent
product_recommendation_agent = Agent(
    name="ProductRecommendationAgent",
    model=Modelconfig.flash_model,
    instruction="""You are the Product Recommendation Coordinator at Chelsea FC.
    
    Your process:
    1. Use create_persona_tool to create a detailed consumer persona for the signals
    2. Get product recommendations using get_product_recommendations tool
    3. Generate reasoning for why each product appeals to the persona using generate_product_reasoning_tool
    
    Always follow this sequence to provide comprehensive, insight-driven product recommendations.
     
    IMPORTANT: All tools get their data from the shared state context. Do not pass any parameters to these tools.
    """,
    description="Coordinates persona creation and product recommendations",
    tools=[
        #AgentTool(agent=persona_agent)
        create_persona_tool
        ,get_product_recommendations_subtool,
        generate_product_reasoning_tool
        
    ]
)
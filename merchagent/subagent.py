# product_recommendation_agent.py
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.adk.tools.agent_tool import AgentTool
from .config import Modelconfig
from .tools import get_product_recommendations
from google.adk.tools import ToolContext
from typing import Dict, List, Any
import json
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig

def create_persona_function(tool_context: ToolContext) -> Dict[str, Any]:
    """Create consumer persona from insights report"""
    
    # Check for required insights
    required_insights = ['tag_insight','brand_insight']
    missing_insights = []
    
    for insight in required_insights:
        if not tool_context.state.get(insight):
            missing_insights.append(insight)
    
    if missing_insights:
        return {"error": f"Missing required insights: {', '.join(missing_insights)}. Run insights generation first."}
    
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

CONTEXT: You have detailed cultural preference data from Qloo API showing what this audience likes in terms of brands, movies, music, and lifestyle tags. This persona will guide our merchandise recommendations to maximize fan engagement and purchase likelihood.

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
- Ensure persona aligns with Chelsea FC brand values and fan culture"""

    try:
        model = GenerativeModel(
            Modelconfig.flash_model,
            generation_config=GenerationConfig(
                temperature=0.2,
                max_output_tokens=6000,
                response_mime_type="application/json"
            )
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
        
        return {
            "success": True,
            "persona_created": True,
            "persona_name": persona_data.get('persona_name', ''),
            "message": "Consumer persona created and stored in state"
        }
        
    except Exception as e:
        return {"error": f"Persona creation failed: {str(e)}"}


def generate_product_reasoning_function(tool_context: ToolContext) -> Dict[str, Any]:
    """Generate reasoning for why recommended products appeal to the persona"""
    
    # Check for required data
    persona = {
        "persona_name": tool_context.state.get('persona_name', ''),
        "persona_description": tool_context.state.get('persona_description', ''),
        "audience_profile": tool_context.state.get('audience_profile', {}),
        "cultural_values": tool_context.state.get('cultural_values', {}),
        "economic_values": tool_context.state.get('economic_values', {}),
        "merchandise_preferences": tool_context.state.get('merchandise_preferences', {}),
        "purchase_motivations": tool_context.state.get('purchase_motivations', [])
    }
    recommendations = tool_context.state.get('recommendations')
    
    if not persona:
        return {"error": "No persona found. Create persona first."}
    
    if not recommendations:
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
            "appeal_factors": [
                "Specific reasons why this product fits the persona",
                "Cultural/emotional connections",
                "Functional benefits that match their lifestyle"
            ],
            "persona_alignment": "How this product matches their values and preferences",
            "purchase_triggers": "What would motivate them to buy this specific item",
        }}
    ]
}}

GUIDELINES:
- Connect product features to persona's cultural and economic values
- Reference specific insights from the persona data
- Focus on both rational and emotional appeal
- Consider how products fit their lifestyle and Chelsea fandom
- Provide actionable insights for marketing and sales"""

    try:
        model = GenerativeModel(
            Modelconfig.flash_lite_model,
            generation_config=GenerationConfig(
                temperature=0.3,
                max_output_tokens=2000,
                response_mime_type="application/json"
            )
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


# Create the persona agent
persona_agent = Agent(
    name="PersonaAgent",
    model=Modelconfig.flash_model,
    instruction="""You are a consumer insights specialist at Chelsea FC.
    
    Your role is to analyze audience insights and create detailed consumer personas that will guide merchandise recommendations.
    
    Use create_persona_function to build comprehensive personas from cultural insights data.
    Focus on understanding what drives this audience's purchasing decisions and how they connect with Chelsea FC.
    """,
    description="Creates consumer personas from audience insights for merchandise targeting",
    tools=[FunctionTool(create_persona_function)]
)

# Create the main product recommendation agent
product_recommendation_agent = Agent(
    name="ProductRecommendationAgent",
    model=Modelconfig.flash_model,
    instruction="""You are the Product Recommendation Coordinator at Chelsea FC.
    
    Your process:
    1. Use persona_agent to create a detailed consumer persona from insights
    2. Get product recommendations using get_product_recommendations 
    3. Generate reasoning for why each product appeals to the persona using generate_product_reasoning_function
    
    Always follow this sequence to provide comprehensive, insight-driven product recommendations.
    
    Present your final recommendations with clear reasoning that connects persona insights to product appeal.
    """,
    description="Coordinates persona creation and product recommendations with detailed reasoning",
    tools=[
        AgentTool(agent=persona_agent),
        FunctionTool(get_product_recommendations),
        FunctionTool(generate_product_reasoning_function)
    ]
)
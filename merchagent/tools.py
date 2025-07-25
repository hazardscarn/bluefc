
import os
import json
from datetime import datetime
from typing import Optional, Dict, List, Any
from pydantic import BaseModel
import vertexai
from vertexai.generative_models import GenerativeModel
from google.adk.tools import ToolContext
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from vertexai.generative_models import GenerativeModel,GenerationConfig
from vertexai.generative_models import (
    GenerativeModel,
    GenerationConfig,
    SafetySetting,
    HarmCategory,
    HarmBlockThreshold,
)


import json
from dotenv import load_dotenv
import logging
from .config import Modelconfig,SecretConfig

# Import your local modules
from src.qloo import QlooAPIClient, QlooSignals, QlooAudience
from .subtools import create_qloo_signals,convert_and_create_signals
from .subtools import get_entity_brand_insights,get_entity_movie_insights,get_entity_podcast_insights,get_tag_insights,get_entity_artist_insights,get_entity_people_insights
from .merchstore import ChelseaMerchandise
import logging


load_dotenv()
# # Initialize Vertex AI
# project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "energyagentai")
# location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
# vertexai.init(project=project_id, location=location)

# # Initialize Qloo client
# client = QlooAPIClient(api_key=os.getenv("QLOO_API_KEY"))
# merch_client = ChelseaMerchandise()
# step_logger = logging.getLogger("AGENT_STEPS")


# Initialize Vertex AI with Secret Manager
project_id = SecretConfig.get_google_cloud_project()
location = SecretConfig.get_google_cloud_location()
print(f"prohect id {project_id}")
print(f"location id {location}")
vertexai.init(project=project_id, location=location)

# Initialize Qloo client with Secret Manager
qloo_api_key = SecretConfig.get_qloo_api_key()
client = QlooAPIClient(api_key=qloo_api_key)

merch_client = ChelseaMerchandise()
step_logger = logging.getLogger("AGENT_STEPS")



def detect_signals_function(request: str, tool_context: ToolContext) -> Dict[str, Any]:
    """Direct signal detection function using Gemini API"""
    
    step_logger.info("STEP 1: 🎯 Detecting demographic signals...")
    model = GenerativeModel(
        Modelconfig.flash_model,
        generation_config=GenerationConfig(
            temperature=0.1,
            max_output_tokens=2000,
            response_mime_type="application/json"  # Force JSON response
        ),
                    safety_settings={
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

    )
    
    # Double all curly braces to escape them, then use format for the request
    prompt = """Extract Qloo signals from user queries and respond ONLY with valid JSON.

    Detect and return JSON with these fields as arrays:
    - age: array of age ranges that match the query
    - gender: array of genders mentioned 
    - location: array of locations/regions mentioned

    Valid age ranges: 35_and_younger, 36_to_55, 55_and_older

    Age mapping examples:
    - "young fans" → ["35_and_younger"]
    - "under 50" → ["35_and_younger", "36_to_55"]
    - "teenagers" → ["35_and_younger"]

    Gender examples:
    - "men" → ["male"]
    - "women" → ["female"]

    Example outputs:
    {{"age": ["36_to_55"], "gender": ["male"], "location": ["New York"]}}
    {{"age": ["55_and_older"], "gender": ["male"], "location": ["south Texas"]}}

    user_query: {}
    """.format(request)  # Only the request gets formatted
    
    try:
        response = model.generate_content(prompt)
        
        if not response.text:
            return {"error": "Empty response from model"}
            
        signals = json.loads(response.text.strip())
        tool_context.state['detected_signals'] = signals
        # Clean result logging
        age_groups = ', '.join(signals.get('age', []))
        location = ', '.join(signals.get('location', []))
        step_logger.info(f"   ✅ Found: Age({age_groups}) Location({location})")
        
        return {
            "success": True,
            "detected_signals": signals,
            "message": "Signals detected successfully"
        }
        
    except Exception as e:
        return {"error": f"Detection failed: {str(e)}"}


    
def get_product_recommendations(tool_context: ToolContext) -> Dict[str, Any]:
    """Product recommendation function with signal processing"""
    
    user_query = f"{tool_context.state['persona_description']} {tool_context.state['merchandise_preferences']}"
    recommendations= merch_client.search_similar_products(query=user_query,match_count=6,match_threshold=0.3,diverse=True)
    
    ##Save recommendation to State
    tool_context.state['recommendations']=recommendations
    try:
        return {
            "success": True,
            "recommendations": recommendations,
            #"signals_processed": tool_context.state['qloo_signal'],
            "signals_processed":"Success",
            "message": "Product recommendations for the user query"
        }
    except:
        return {"error": f"No insights report found. CReate an insights report for the signals and audience first"}




def get_insights_function(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Get insights for the signals provided.
    
    ["movie", "podcast", "videogame", "tv_show", "artist", "people", "tag"]
    :return: Formatted string containing insights
    """
    step_logger.info("STEP 3: 🧠 Collecting cultural insights from Qloo...")
    insight_summary = []
    # Check if we have detected signals
    detected_signals = tool_context.state.get('detected_signals')
    if not detected_signals:
        step_logger.error("   ❌ No signals found")
        return {"error": "No signals detected. Run signal detection first."}
    
    # Get detected audiences (if any)
    audience_ids = tool_context.state.get('detected_audience_ids', [])
    if not audience_ids:
        step_logger.error("   ❌ No audiences  found")
        return {"error": "Audience detection is not done. Run Audience detection detection first."}
    step_logger.info(f"   📊 Working with {len(audience_ids)} audiences")
    # Convert and create QlooSignals
    # Add Qloo signal to state context
    qloo_result = convert_and_create_signals(tool_context)  # Fixed: Added tool_context
    #tool_context.state['qloo_signal'] = qloo_result.get('qloo_signal')

    signals=qloo_result.get('qloo_signal')
    result = get_entity_brand_insights(signals,limit=8)
    tool_context.state['brand_insight']=result
    if result:
        insight_summary.append(result)
        step_logger.info("✅ Brand insights collected")
    else:
        step_logger.warning(" ⚠️ No Brand insights found")
            
    result = get_entity_movie_insights(signals,limit=5)
    tool_context.state['movie_insight']=result
    if result:
        insight_summary.append(result)
        step_logger.info("✅ Movie insights collected")
    else:
        step_logger.warning(" ⚠️  No movie insights found")

            
    result = get_entity_podcast_insights(signals,limit=5)
    tool_context.state['podcast_insight']=result
    if result:
        insight_summary.append(result)
        step_logger.info("✅ Podcast insights collected")
            
    # result = get_entity_videogame_insights(signals)
    # if result:
    #     insight_summary.append(result)
            
    # result = get_entity_tv_show_insights(signals)
    # if result:
    #     insight_summary.append(result)
            
    result = get_entity_artist_insights(signals,limit=4)
    tool_context.state['artist_insight']=result
    if result:
        insight_summary.append(result)
        step_logger.info("✅ Artist insights collected")
    else:
        step_logger.warning(" ⚠️ No Artist insights found")
            
    result = get_entity_people_insights(signals,limit=4)
    tool_context.state['person_insight']=result
    if result:
        insight_summary.append(result)
        step_logger.info("✅ person insights collected")
    else:
        step_logger.warning(" ⚠️ No person insights found")
            
    result = get_tag_insights(signals,limit=10)
    tool_context.state['tag_insight']=result
    if result:
        insight_summary.append(result)
        step_logger.info("✅ tag insights collected")
    else:
        step_logger.warning(" ⚠️ No tag insights found")
            
    # result = get_entity_place_insights(signals)  # Fixed: should be place insights
    # if result:
    #     insight_summary.append(result)
    step_logger.info(f"Insights Summary:{insight_summary}")
    if insight_summary:
    
        # Join all results with separators
        separator = f"\n\n{'='*80}\n\n"
        insight_report=separator.join(insight_summary)

        ##Add the report to state context
        # tool_context.state['insight_summary']= insight_report
        return {
                "success": True,
                "message": "Insight report created for audience"
            }
    else:
        return "No insights available for the selected entity."


import os
import json
from datetime import datetime
from typing import Optional, Dict, List, Any
from pydantic import BaseModel
import vertexai
from vertexai.generative_models import GenerativeModel
from google.adk.tools import ToolContext
from dotenv import load_dotenv
import logging
from .config import Modelconfig

# Import your local modules
from src.qloo import QlooAPIClient, QlooSignals, QlooAudience
from .subtools import get_insights_tool

load_dotenv()
# Initialize Vertex AI
project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "energyagentai")
location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
vertexai.init(project=project_id, location=location)

# Initialize Qloo client
client = QlooAPIClient(api_key=os.getenv("QLOO_API_KEY"))


# Pydantic model for structured brand detection output
class BrandDetectionResult(BaseModel):
    """Structured output for brand detection"""
    brands: List[str]
    confidence: float
    message: str

def detect_brands_in_text(user_message: str, tool_context: ToolContext = None) -> Dict[str, Any]:
    """
    Uses a direct LLM call to detect brand mentions in user text with structured output.
    
    Args:
        user_message (str): The user's message to analyze for brand mentions
        tool_context (ToolContext): ADK tool context for state management
    
    Returns:
        Dict with detected brands and analysis
    """
    logging.info(f"🔍 [TOOL] detect_brands_in_text: Starting brand detection for message: '{user_message}'")
    
    try:
        # Initialize the model
        model = GenerativeModel(model_name="gemini-2.0-flash-lite-001")
        
        # Create the prompt for brand detection
        brand_detection_prompt = f"""
You are a brand detection expert. Your task is to identify any brand mentions in the provided text.

**Text to analyze:** "{user_message}"

**Your Task:**
Analyze the text and identify all brand mentions including:
- Company names (Apple, Microsoft, Google, Nike, etc.)
- Product brands (iPhone, Windows, Chrome, Air Jordan, etc.)
- Service brands (Uber, Netflix, Spotify, etc.)
- Retail brands (Amazon, Target, Walmart, etc.)
- Sports teams (Chelsea FC, Manchester United, Lakers, Arsenal FC, etc.)
- Entertainment brands (Disney, Marvel, etc.)
- Any other recognizable commercial brands or organizations

**Rules:**
- Include variations (e.g., "McDonald's" and "McDonalds")
- Focus on well-known commercial brands and organizations
- Include sports teams and entertainment brands
- Don't include generic terms or non-commercial entities
- Be conservative - only include clear brand mentions
- If no brands are found, return empty list

**Output Format:**
Return a JSON object with:
- "brands": array of detected brand names (strings)
- "confidence": confidence score between 0.0 and 1.0
- "message": brief explanation of what was detected

**Example Output:**
{{
    "brands": ["Chelsea FC", "Arsenal FC"],
    "confidence": 0.95,
    "message": "Detected 2 football club brands"
}}
"""

        logging.info(f"🤖 [TOOL] detect_brands_in_text: Calling model for brand detection")
        
        # Generate response with JSON output
        response = model.generate_content(
            brand_detection_prompt,
            generation_config={
                "temperature": 0.1,  # Low temperature for consistent results
                "max_output_tokens": 1024,
                "response_mime_type": "application/json"
            }
        )
        
        # Parse the structured response
        response_text = response.text.strip()
        logging.info(f"📄 [TOOL] detect_brands_in_text: Raw response: {response_text}")
        
        try:
            detection_result = json.loads(response_text)
            brands = detection_result.get("brands", [])
            confidence = detection_result.get("confidence", 0.8)  # Default to reasonable confidence
            message = detection_result.get("message", "Brand detection completed")
            
            # Validate that brands is a list
            if not isinstance(brands, list):
                logging.info(f"⚠️ [TOOL] detect_brands_in_text: brands field is not a list, converting")
                brands = [str(brands)] if brands else []
                
        except json.JSONDecodeError as e:
            logging.info(f"⚠️ [TOOL] detect_brands_in_text: Failed to parse JSON response: {e}")
            logging.info(f"    Raw response was: {response_text}")
            
            # Fallback: try to extract brands manually using simple patterns
            brands = []
            confidence = 0.5
            message = "Brand detection completed with parsing issues"
            
            # Simple fallback extraction - look for common brand patterns
            if "Chelsea FC" in user_message or "Chelsea" in user_message:
                brands.append("Chelsea FC")
            if "Arsenal FC" in user_message or "Arsenal" in user_message:
                brands.append("Arsenal FC")
            if "LA Dodgers" in user_message or "Dodgers" in user_message:
                brands.append("LA Dodgers")
            if "Nike" in user_message:
                brands.append("Nike")
            if "Apple" in user_message:
                brands.append("Apple")
            # Add more fallback patterns as needed
            
            if brands:
                message = f"Detected {len(brands)} brands using fallback method"
                confidence = 0.7
        
        logging.info(f"✅ [TOOL] detect_brands_in_text: Detected {len(brands)} brands: {brands}")
        
        # Store in session state
        if tool_context and hasattr(tool_context, 'state'):
            tool_context.state['detected_brands'] = {
                'brands': brands,
                'original_message': user_message,
                'detected_at': datetime.now().isoformat(),
                'confidence': confidence,
                'detection_message': message
            }
            logging.info(f"💾 [TOOL] detect_brands_in_text: Stored in session state")
        
        return {
            "success": True,
            "brands_detected": brands,
            "total_brands": len(brands),
            "confidence": confidence,
            "message": f"Detected {len(brands)} brand(s): {', '.join(brands) if brands else 'none'}"
        }
        
    except Exception as e:
        logging.info(f"❌ [TOOL] detect_brands_in_text: Error - {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "brands_detected": [],
            "total_brands": 0,
            "confidence": 0.0,
            "message": "Failed to detect brands"
        }


def get_entity_ids_with_context(queries: List[str], tool_context: ToolContext = None) -> Dict[str, Any]:
    """
    Get entity IDs for a list of brand queries with state context management.
    
    Args:
        queries (List[str]): List of brand names to search for
        tool_context (ToolContext): ADK tool context for state management
        
    Returns:
        Dict with entity details and IDs
    """
    logging.info(f"🔗 [TOOL] get_entity_ids_with_context: Starting entity search for queries: {queries}")
    
    if not client:
        logging.info(f"❌ [TOOL] get_entity_ids_with_context: Qloo client not available")
        return {
            "success": False,
            "error": "Qloo client not available",
            "entity_details": {}
        }
    
    try:
        all_entity_details = {}
        
        logging.info("🔍 [TOOL] get_entity_ids_with_context: Searching for brand entities to get IDs...")
        for query in queries:
            logging.info(f"📍 [TOOL] get_entity_ids_with_context: Searching: '{query}'")
            
            result = client.search_entities(
                query=query,
                limit=2  # Get top 1 per query for better matching
            )
            
            if result['success'] and result['entities']:
                # Take the top result that's most likely a brand
                for entity in result['entities']:
                    if entity.entity_type.lower() in ['brand', 'company', 'product']:
                        all_entity_details[entity.id] = {
                            'name': entity.name,
                            'type': entity.entity_type,
                            'type_urn': entity.type_urn,
                            'popularity': entity.popularity,
                            'query': query,
                            'entity_id': entity.id
                        }
                        logging.info(f"✅ [TOOL] get_entity_ids_with_context: Found brand - {entity.name} (ID: {entity.id})")
                        break
                else:
                    # If no explicit brand type found, take the first result
                    entity = result['entities'][0]
                    all_entity_details[entity.id] = {
                        'name': entity.name,
                        'type': entity.entity_type,
                        'type_urn': entity.type_urn,
                        'popularity': entity.popularity,
                        'query': query,
                        'entity_id': entity.id
                    }
                    logging.info(f"✅ [TOOL] get_entity_ids_with_context: Found entity - {entity.name} (Type: {entity.entity_type}, ID: {entity.id})")
            else:
                logging.info(f"⚠️ [TOOL] get_entity_ids_with_context: No entities found for '{query}'")
        
        # Store in session state
        if tool_context and hasattr(tool_context, 'state'):
            tool_context.state['brand_entity_details'] = {
                'entities': all_entity_details,
                'queries_searched': queries,
                'search_timestamp': datetime.now().isoformat()
            }
            logging.info(f"💾 [TOOL] get_entity_ids_with_context: Stored {len(all_entity_details)} entities in session state")
        
        return {
            "success": True,
            "entity_details": all_entity_details,
            "total_entities_found": len(all_entity_details),
            "message": f"Found {len(all_entity_details)} brand entities"
        }
        
    except Exception as e:
        logging.info(f"❌ [TOOL] get_entity_ids_with_context: Error - {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "entity_details": {},
            "message": "Failed to get entity IDs"
        }


def get_demographics_insights_with_context(tool_context: ToolContext = None) -> Dict[str, Any]:
    """
    Get demographics insights for brand entities stored in session state.
    
    Args:
        tool_context (ToolContext): ADK tool context for state management
        
    Returns:
        Dict with demographics insights for all brands
    """
    logging.info(f"📊 [TOOL] get_demographics_insights_with_context: Starting demographics analysis")
    
    if not client:
        logging.info(f"❌ [TOOL] get_demographics_insights_with_context: Qloo client not available")
        return {
            "success": False,
            "error": "Qloo client not available",
            "demographics_data": {}
        }
    
    try:
        if not tool_context or not hasattr(tool_context, 'state') or 'brand_entity_details' not in tool_context.state:
            logging.info(f"❌ [TOOL] get_demographics_insights_with_context: No brand entities found in session state")
            return {
                "success": False,
                "error": "No brand entities found in session state. Please detect brands first.",
                "demographics_data": {}
            }
        
        entity_details = tool_context.state['brand_entity_details']['entities']
        entity_ids = list(entity_details.keys())
        
        logging.info(f"🔍 [TOOL] get_demographics_insights_with_context: Analyzing demographics for {len(entity_ids)} entities")
        
        if not entity_ids:
            logging.info(f"❌ [TOOL] get_demographics_insights_with_context: No entity IDs available")
            return {
                "success": False,
                "error": "No entity IDs available",
                "demographics_data": {}
            }
        
        demographics_result = client.get_demographics_analysis(
            entity_ids=entity_ids,
            signals=None,  # No additional signals for pure brand demographics
            limit=10
        )
        
        demographics_data = demographics_result.get('results', {}).get('demographics', [])
        
        if not demographics_data:
            logging.info(f"⚠️ [TOOL] get_demographics_insights_with_context: No demographics results found")
            return {
                "success": False,
                "error": "No demographics results found",
                "demographics_data": {}
            }
        
        logging.info(f"✅ [TOOL] get_demographics_insights_with_context: Processing {len(demographics_data)} demographic results")
        
        # Process and format demographics data
        formatted_demographics = {}
        for demo in demographics_data:
            entity_id = demo.get("entity_id")
            if entity_id in entity_details:
                brand_name = entity_details[entity_id]['name']
                query_data = demo.get("query", {})
                
                formatted_demographics[entity_id] = {
                    'brand_name': brand_name,
                    'entity_id': entity_id,
                    'age_demographics': query_data.get("age", {}),
                    'gender_demographics': query_data.get("gender", {}),
                    'dominant_age': None,
                    'dominant_gender': None,
                    'demographic_summary': ""
                }
                
                # Determine dominant demographics
                age_data = query_data.get("age", {})
                if age_data:
                    dominant_age = max(age_data.items(), key=lambda x: x[1])
                    formatted_demographics[entity_id]['dominant_age'] = {
                        'group': dominant_age[0].replace('_', ' ').title(),
                        'score': dominant_age[1]
                    }
                
                gender_data = query_data.get("gender", {})
                if gender_data:
                    dominant_gender = max(gender_data.items(), key=lambda x: x[1])
                    formatted_demographics[entity_id]['dominant_gender'] = {
                        'gender': dominant_gender[0].title(),
                        'score': dominant_gender[1]
                    }
                
                logging.info(f"📈 [TOOL] get_demographics_insights_with_context: Processed demographics for {brand_name}")
        
        # Store in session state
        if tool_context and hasattr(tool_context, 'state'):
            tool_context.state['brand_demographics'] = {
                'demographics': formatted_demographics,
                'analysis_timestamp': datetime.now().isoformat(),
                'total_brands_analyzed': len(formatted_demographics)
            }
            logging.info(f"💾 [TOOL] get_demographics_insights_with_context: Stored demographics for {len(formatted_demographics)} brands")
        
        return {
            "success": True,
            "demographics_data": formatted_demographics,
            "total_brands_analyzed": len(formatted_demographics),
            "message": f"Demographics analysis completed for {len(formatted_demographics)} brands"
        }
        
    except Exception as e:
        logging.info(f"❌ [TOOL] get_demographics_insights_with_context: Error - {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "demographics_data": {},
            "message": "Failed to get demographics insights"
        }


def get_individual_brand_insights(entity_id: str, tool_context: ToolContext = None) -> Dict[str, Any]:
    """
    Get insights for a single brand entity using entity ID as interest signal.
    
    Args:
        entity_id (str): The entity ID to get insights for
        tool_context (ToolContext): ADK tool context for state management
        
    Returns:
        Dict with brand insights
    """
    logging.info(f"🎯 [TOOL] get_individual_brand_insights: Getting insights for entity {entity_id}")
    
    if not client:
        logging.info(f"❌ [TOOL] get_individual_brand_insights: Qloo client not available")
        return {
            "success": False,
            "error": "Qloo client not available",
            "insights": ""
        }
    
    try:
        # Get insights using the brand entity insights collection logic
        insights_result = collect_brand_entity_insights(entity_id)
        
        logging.info(f"✅ [TOOL] get_individual_brand_insights: Collected insights for entity {entity_id}")
        
        return {
            "success": True,
            "entity_id": entity_id,
            "insights": insights_result,
            "message": f"Insights collected for entity {entity_id}"
        }
        
    except Exception as e:
        logging.info(f"❌ [TOOL] get_individual_brand_insights: Error - {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "insights": "",
            "message": f"Failed to get insights for entity {entity_id}"
        }


def collect_brand_entity_insights(entity_id: str, signals: QlooSignals = None) -> str:
    """
    Collect insights for a brand entity across multiple categories using rich subtools functions.
    
    Args:
        entity_id (str): The entity ID to analyze
        signals (QlooSignals): Optional signals object (not used in this function)
        
    Returns:
        Formatted string with rich insights across categories
    """
    logging.info(f"🔍 [TOOL] collect_brand_entity_insights: Collecting rich insights for entity {entity_id}")
    
    try:
        insight_results = []
        
        # Create a QlooSignals object with the entity as interest
        entity_signals = QlooSignals(
            demographics=None,
            location=None,
            entity_ids=[entity_id],  # This gets mapped to signal.interests.entities
            entity_queries=None,
            tag_ids=None
        )
        
        logging.info(f"📊 [TOOL] collect_brand_entity_insights: Created signals with entity_id {entity_id}")
        
        # Use rich subtools functions instead of basic client calls for detailed descriptions
        logging.info(f"🎵 [TOOL] collect_brand_entity_insights: Getting rich artist insights for entity {entity_id}")
        try:
            from .subtools import get_entity_artist_insights
            artist_insights = get_entity_artist_insights(signals=entity_signals)
            if artist_insights and "No artist results found" not in artist_insights:
                insight_results.append(f"\n=== MUSIC/ARTIST CULTURAL INSIGHTS FOR ENTITY {entity_id} ===")
                insight_results.append(artist_insights)
                logging.info(f"✅ [TOOL] collect_brand_entity_insights: Got rich artist insights")
        except Exception as e:
            logging.info(f"❌ [TOOL] collect_brand_entity_insights: Failed to get artist insights: {str(e)}")
        
        logging.info(f"🎬 [TOOL] collect_brand_entity_insights: Getting rich movie insights for entity {entity_id}")
        try:
            from .subtools import get_entity_movie_insights
            movie_insights = get_entity_movie_insights(signals=entity_signals)
            if movie_insights and "No movie results found" not in movie_insights:
                insight_results.append(f"\n=== MOVIE CULTURAL INSIGHTS FOR ENTITY {entity_id} ===")
                insight_results.append(movie_insights)
                logging.info(f"✅ [TOOL] collect_brand_entity_insights: Got rich movie insights")
        except Exception as e:
            logging.info(f"❌ [TOOL] collect_brand_entity_insights: Failed to get movie insights: {str(e)}")
        
        # logging.info(f"📺 [TOOL] collect_brand_entity_insights: Getting rich TV show insights for entity {entity_id}")
        # try:
        #     from .subtools import get_entity_tv_show_insights
        #     tv_insights = get_entity_tv_show_insights(signals=entity_signals)
        #     if tv_insights and "No TV show results found" not in tv_insights:
        #         insight_results.append(f"\n=== TV SHOW CULTURAL INSIGHTS FOR ENTITY {entity_id} ===")
        #         insight_results.append(tv_insights)
        #         logging.info(f"✅ [TOOL] collect_brand_entity_insights: Got rich TV show insights")
        # except Exception as e:
        #     logging.info(f"❌ [TOOL] collect_brand_entity_insights: Failed to get TV show insights: {str(e)}")
        
        # logging.info(f"📍 [TOOL] collect_brand_entity_insights: Getting rich place insights for entity {entity_id}")
        # try:
        #     from .subtools import get_entity_place_insights
        #     place_insights = get_entity_place_insights(signals=entity_signals)
        #     if place_insights and "No place results found" not in place_insights:
        #         insight_results.append(f"\n=== PLACE CULTURAL INSIGHTS FOR ENTITY {entity_id} ===")
        #         insight_results.append(place_insights)
        #         logging.info(f"✅ [TOOL] collect_brand_entity_insights: Got rich place insights")
        # except Exception as e:
        #     logging.info(f"❌ [TOOL] collect_brand_entity_insights: Failed to get place insights: {str(e)}")
        
        logging.info(f"🎧 [TOOL] collect_brand_entity_insights: Getting rich podcast insights for entity {entity_id}")
        try:
            from .subtools import get_entity_podcast_insights
            podcast_insights = get_entity_podcast_insights(signals=entity_signals)
            if podcast_insights and "No podcast results found" not in podcast_insights:
                insight_results.append(f"\n=== PODCAST CULTURAL INSIGHTS FOR ENTITY {entity_id} ===")
                insight_results.append(podcast_insights)
                logging.info(f"✅ [TOOL] collect_brand_entity_insights: Got rich podcast insights")
        except Exception as e:
            logging.info(f"❌ [TOOL] collect_brand_entity_insights: Failed to get podcast insights: {str(e)}")
        
        # logging.info(f"👥 [TOOL] collect_brand_entity_insights: Getting rich people insights for entity {entity_id}")
        # try:
        #     from .subtools import get_entity_people_insights
        #     people_insights = get_entity_people_insights(signals=entity_signals)
        #     if people_insights and "No people results found" not in people_insights:
        #         insight_results.append(f"\n=== PEOPLE CULTURAL INSIGHTS FOR ENTITY {entity_id} ===")
        #         insight_results.append(people_insights)
        #         logging.info(f"✅ [TOOL] collect_brand_entity_insights: Got rich people insights")
        # except Exception as e:
        #     logging.info(f"❌ [TOOL] collect_brand_entity_insights: Failed to get people insights: {str(e)}")
        
        # Handle tags separately using get_tag_insights
        logging.info(f"🏷️ [TOOL] collect_brand_entity_insights: Getting rich tag insights for entity {entity_id}")
        try:
            from .subtools import get_tag_insights
            tag_insights = get_tag_insights(signals=entity_signals)
            if tag_insights and "No tag results found" not in tag_insights:
                insight_results.append(f"\n=== LIFESTYLE TAG INSIGHTS FOR ENTITY {entity_id} ===")
                insight_results.append(tag_insights)
                logging.info(f"✅ [TOOL] collect_brand_entity_insights: Got rich tag insights")
        except Exception as e:
            logging.info(f"❌ [TOOL] collect_brand_entity_insights: Failed to get tag insights: {str(e)}")
        
        if insight_results:
            logging.info(f"✅ [TOOL] collect_brand_entity_insights: Collected {len(insight_results)} rich category insights")
            return f"\n\n{'='*80}\n\n".join(insight_results)
        else:
            logging.info(f"⚠️ [TOOL] collect_brand_entity_insights: No insights available for entity {entity_id}")
            return f"No insights available for entity {entity_id}"
            
    except Exception as e:
        logging.info(f"❌ [TOOL] collect_brand_entity_insights: Error - {str(e)}")
        return f"Error collecting insights for entity {entity_id}: {str(e)}"



def analyze_all_brands_with_context(tool_context: ToolContext = None) -> Dict[str, Any]:
    """
    Analyze all detected brands with demographics and insights comparison.
    
    Args:
        tool_context (ToolContext): ADK tool context for state management
        
    Returns:
        Dict with comprehensive brand analysis
    """
    logging.info(f"📝 [TOOL] analyze_all_brands_with_context: Starting comprehensive brand analysis")
    
    try:
        if not tool_context or not hasattr(tool_context, 'state'):
            logging.info(f"❌ [TOOL] analyze_all_brands_with_context: No tool context available")
            return {
                "success": False,
                "error": "No tool context available",
                "analysis": ""
            }
        
        # Check if we have all required data
        brand_entities = tool_context.state.get('brand_entity_details', {})
        demographics_data = tool_context.state.get('brand_demographics', {})
        
        if not brand_entities or not demographics_data:
            logging.info(f"❌ [TOOL] analyze_all_brands_with_context: Missing brand data")
            return {
                "success": False,
                "error": "Missing brand data. Please run the complete brand analysis workflow first.",
                "analysis": ""
            }
        
        entities = brand_entities.get('entities', {})
        demographics = demographics_data.get('demographics', {})
        
        if not entities:
            logging.info(f"❌ [TOOL] analyze_all_brands_with_context: No brand entities to analyze")
            return {
                "success": False,
                "error": "No brand entities to analyze",
                "analysis": ""
            }
        
        logging.info(f"🔍 [TOOL] analyze_all_brands_with_context: Collecting insights for {len(entities)} brands")
        
        # Collect insights for each brand
        all_brand_insights = {}
        for entity_id in entities.keys():
            logging.info(f"🎯 [TOOL] analyze_all_brands_with_context: Getting insights for entity {entity_id}")
            insights_result = get_individual_brand_insights(entity_id, tool_context)
            if insights_result['success']:
                all_brand_insights[entity_id] = insights_result['insights']
        
        # Store all insights in session state
        if tool_context and hasattr(tool_context, 'state'):
            tool_context.state['all_brand_insights'] = {
                'insights': all_brand_insights,
                'analysis_timestamp': datetime.now().isoformat()
            }
            logging.info(f"💾 [TOOL] analyze_all_brands_with_context: Stored insights for {len(all_brand_insights)} brands")
        
        # Generate comprehensive analysis using direct model call
        analysis_data = {
            'entities': entities,
            'demographics': demographics,
            'insights': all_brand_insights
        }
        
        logging.info(f"🤖 [TOOL] analyze_all_brands_with_context: Generating comprehensive analysis report")
        
        # Create analysis report using direct model call
        analysis_report = generate_brand_analysis_report(analysis_data)
        
        # Store final report in session state
        if tool_context and hasattr(tool_context, 'state') and analysis_report:
            tool_context.state['brand_analysis_report'] = {
                'report': analysis_report,
                'generated_at': datetime.now().isoformat(),
                'brands_analyzed': list(entities.keys())
            }
            logging.info(f"💾 [TOOL] analyze_all_brands_with_context: Stored final analysis report")
        
        logging.info(f"✅ [TOOL] analyze_all_brands_with_context: Comprehensive analysis completed")
        
        return {
            "success": True,
            "analysis": analysis_report,
            "brands_analyzed": len(entities),
            "message": "Comprehensive brand analysis completed"
        }
        
    except Exception as e:
        logging.info(f"❌ [TOOL] analyze_all_brands_with_context: Error - {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "analysis": "",
            "message": "Failed to complete brand analysis"
        }

def generate_brand_analysis_report(analysis_data: Dict[str, Any]) -> str:
    """
    Generate comprehensive brand analysis by passing the already-good data directly to the model.
    """
    logging.info(f"📊 [TOOL] generate_brand_analysis_report: Creating comprehensive report")
    
    try:
        entities = analysis_data.get('entities', {})
        demographics = analysis_data.get('demographics', {})
        insights = analysis_data.get('insights', {})
        
        if not entities:
            return "Error: No brand entities provided for analysis"
        
        brand_names = [details['name'] for details in entities.values()]
        
        # Build the prompt with raw data - no processing needed!
        prompt_parts = []
        
        # Add brand info
        prompt_parts.append("BRANDS BEING ANALYZED:")
        for entity_id, details in entities.items():
            prompt_parts.append(f"- {details['name']} (Entity ID: {entity_id})")
        
        # Add demographics data as-is
        prompt_parts.append("\nDEMOGRAPHICS DATA:")
        for entity_id, demo_data in demographics.items():
            prompt_parts.append(f"\n{demo_data['brand_name']}:")
            prompt_parts.append(f"Age Demographics: {demo_data.get('age_demographics', {})}")
            prompt_parts.append(f"Gender Demographics: {demo_data.get('gender_demographics', {})}")
        
        # Add the rich insights data EXACTLY as collected - it's already perfect!
        prompt_parts.append("\nCULTURAL INSIGHTS:")
        for entity_id, insight_text in insights.items():
            brand_name = entities.get(entity_id, {}).get('name', 'Unknown')
            prompt_parts.append(f"\n=== {brand_name} CULTURAL INSIGHTS ===")
            prompt_parts.append(insight_text)
        # Create focused analysis prompt with corrected data
        analysis_prompt = f"""
You are a cultural anthropologist analyzing brand audiences. Create a comprehensive comparison of these brands.

BRANDS: {', '.join(brand_names)}

{chr(10).join(prompt_parts)}

IMPORTANT NOTES ABOUT THE DATA:
- Age/Gender scores are AFFINITY SCORES (positive = higher affinity, negative = lower affinity)
- Higher positive scores indicate stronger audience concentration in that demographic
- Cultural insights show the top entities each audience has affinity for

CREATE A FOCUSED 4-SECTION ANALYSIS:

**1. DEMOGRAPHIC COMPARISON**
Compare the demographic profiles. Which age groups and genders show highest affinity for each brand? What does this reveal about the audience composition?

**2. CULTURAL IDENTITY ANALYSIS** 
Analyze the cultural preferences. Focus mainly on tags. What do these preferences reveal about each audience's cultural identity, values, and lifestyle?

**3. Audience INTERESTS**
What are the top interests and affinities for each brand's audience? 
Use movies, artists, podcasts etc to understand what their likes are

**4. BRAND POSITIONING INSIGHTS**
Based on demographics and cultural data, how should each brand position itself?
Where can they grow and what niches can they target?


REQUIREMENTS:
- Use the actual data provided (don't say data is missing)
- Focus on insights and comparisons, not data repetition
- Professional but engaging tone
- 600-800 words

ANALYZE NOW:
"""

        logging.info(f"🤖 [TOOL] generate_brand_analysis_report: Calling model for cultural analysis")
        
        # Use Pro model for complex analysis
        model = GenerativeModel(model_name=Modelconfig.get_flash_model())
        
        # Generate the analysis report
        response = model.generate_content(
            analysis_prompt,
            generation_config={
                "temperature": 0.3,
                "max_output_tokens": 4096,  # Sufficient for comprehensive analysis
                "top_p": 0.8,
                "top_k": 40
            }
        )
        
        analysis_report = response.text.strip() if response.text else ""
        
        if analysis_report:
            logging.info(f"✅ [TOOL] generate_brand_analysis_report: Generated {len(analysis_report)} character cultural analysis")
            return analysis_report
        else:
            logging.info(f"⚠️ [TOOL] generate_brand_analysis_report: Empty response from model")
            return "Unable to generate cultural analysis report - empty model response"
            
    except Exception as e:
        logging.info(f"❌ [TOOL] generate_brand_analysis_report: Error - {str(e)}")
        return f"Error generating cultural analysis report: {str(e)}"
    

def get_brand_analysis_summary(tool_context: ToolContext = None) -> Dict[str, Any]:
    """
    Get a summary of all brand analysis data in the session.
    """
    logging.info(f"📊 [TOOL] get_brand_analysis_summary: Getting session summary")
    
    try:
        if not tool_context or not hasattr(tool_context, 'state'):
            logging.info(f"❌ [TOOL] get_brand_analysis_summary: No tool context available")
            return {
                "success": False,
                "error": "No tool context available",
                "summary": {}
            }
        
        state = tool_context.state
        
        summary = {
            "brands_detected": bool('detected_brands' in state),
            "entity_ids_found": bool('brand_entity_details' in state),
            "demographics_analyzed": bool('brand_demographics' in state),
            "insights_collected": bool('all_brand_insights' in state),
            "final_report_generated": bool('brand_analysis_report' in state)
        }
        
        # Add detailed info if available
        if 'detected_brands' in state:
            detected = state['detected_brands']
            summary["detected_brands_info"] = {
                "brands": detected.get('brands', []),
                "total": len(detected.get('brands', []))
            }
        
        if 'brand_entity_details' in state:
            entities = state['brand_entity_details']
            summary["entity_details_info"] = {
                "total_entities": len(entities.get('entities', {})),
                "entity_names": [details['name'] for details in entities.get('entities', {}).values()]
            }
        
        if 'brand_demographics' in state:
            demo = state['brand_demographics']
            summary["demographics_info"] = {
                "brands_analyzed": demo.get('total_brands_analyzed', 0)
            }
        
        logging.info(f"✅ [TOOL] get_brand_analysis_summary: Summary generated")
        
        return {
            "success": True,
            "summary": summary,
            "message": "Brand analysis summary retrieved successfully"
        }
        
    except Exception as e:
        logging.info(f"❌ [TOOL] get_brand_analysis_summary: Error - {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "summary": {},
            "message": "Failed to get brand analysis summary"
        }


def run_brand_analysis(user_message: str, tool_context: ToolContext = None) -> Dict[str, Any]:
    """
    Runs the complete brand analysis workflow using the Brand Analysis Agent.
    
    Args:
        user_message (str): User's message to analyze for brands
        tool_context (ToolContext): ADK tool context for state management
        
    Returns:
        Dict with brand analysis results
    """
    logging.info(f"🚀 [TOOL] run_brand_analysis: Starting complete workflow for message: '{user_message}'")
    
    try:
        # Import from agent (this is ok, no circular import here)
        from .agent import brand_analysis_agent
        
        logging.info(f"🤖 [TOOL] run_brand_analysis: Calling brand_analysis_agent")
        
        # Call the brand analysis agent with the user message
        result = brand_analysis_agent.run(
            input_text=user_message,
            context=tool_context
        )
        
        analysis_response = result.get('brand_analysis_response', result.get('output', ''))
        
        logging.info(f"✅ [TOOL] run_brand_analysis: Brand analysis workflow completed")
        
        return {
            "success": True,
            "analysis": analysis_response,
            "agent_used": "Brand Analysis Agent",
            "message": "Brand analysis completed successfully"
        }
        
    except Exception as e:
        logging.info(f"❌ [TOOL] run_brand_analysis: Error - {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "analysis": "",
            "message": "Failed to run brand analysis"
        }


def get_coordinator_session_summary(tool_context: ToolContext = None) -> Dict[str, Any]:
    """
    Get comprehensive summary of all agent activities in the current session.
    """
    logging.info(f"📋 [TOOL] get_coordinator_session_summary: Getting coordinator session summary")
    
    try:
        if not tool_context or not hasattr(tool_context, 'state'):
            logging.info(f"❌ [TOOL] get_coordinator_session_summary: No tool context available")
            return {
                "success": False,
                "error": "No tool context available",
                "summary": {}
            }
        
        state = tool_context.state
        state_keys = list(state.keys()) if hasattr(state, 'keys') else []
        
        summary = {
            "agents_used": [],
            "brand_analysis_completed": False,
            "merch_analysis_completed": False,  # For future use
            "total_state_keys": len([k for k in state_keys if k.startswith(('brand_', 'detected_', 'qloo_'))]),
            "session_data": {}
        }
        
        # Check Brand Analysis Agent activity
        if any(key.startswith('brand_') or key.startswith('detected_') for key in state_keys):
            summary["agents_used"].append("Brand Analysis Agent")
            summary["brand_analysis_completed"] = 'brand_analysis_report' in state
            
            summary["session_data"]["brand_analysis"] = {
                "brands_detected": bool('detected_brands' in state),
                "entities_resolved": bool('brand_entity_details' in state),
                "demographics_analyzed": bool('brand_demographics' in state),
                "insights_collected": bool('all_brand_insights' in state),
                "final_report": bool('brand_analysis_report' in state)
            }
            
            if 'detected_brands' in state:
                detected = state['detected_brands']
                summary["session_data"]["detected_brands"] = detected.get('brands', [])
        
        logging.info(f"✅ [TOOL] get_coordinator_session_summary: Session summary generated")
        
        return {
            "success": True,
            "summary": summary,
            "message": "Multi-agent session summary retrieved successfully"
        }
        
    except Exception as e:
        logging.info(f"❌ [TOOL] get_coordinator_session_summary: Error - {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "summary": {},
            "message": "Failed to get session summary"
        }
    

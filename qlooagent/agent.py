import os
import json
from datetime import datetime
from typing import Optional, Dict, List, Any
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool, ToolContext
from dotenv import load_dotenv
import vertexai
import logging

# Import your local modules
from .config import Modelconfig
from src.qloo import QlooAPIClient, QlooSignals, QlooAudience

load_dotenv()
project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "energyagentai")
location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
vertexai.init(project=project_id, location=location)

# Initialize Qloo client
client = QlooAPIClient(api_key=os.getenv("QLOO_API_KEY"))

def create_qloo_signals(
    demographics: str, 
    location: str, 
    tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Creates QlooSignals object with only demographics and location.
    
    Args:
        demographics (str): JSON string with demographic information
        location (str): JSON string with location information  
        tool_context (ToolContext): ADK tool context for state management
    
    Returns:
        Dict with created signals and validation status
    """
    if not client:
        return {
            "success": False,
            "error": "Qloo client not available. Check QLOO_API_KEY configuration.",
            "message": "Failed to create QlooSignals - client not initialized"
        }
    
    try:
        # Parse input parameters
        demo_dict = json.loads(demographics) if demographics else {}
        location_dict = json.loads(location) if location else {}
        
        # Create QlooSignals object - NO entity_queries!
        signals = QlooSignals(
            demographics=demo_dict if demo_dict else None,
            location=location_dict if location_dict else None,
            entity_queries=None  # Keep this None to avoid issues
        )
        
        # Store signals in ADK session state
        if tool_context and hasattr(tool_context, 'state'):
            tool_context.state['qloo_signals'] = {
                'demographics': demo_dict,
                'location': location_dict,
                'created_at': datetime.now().isoformat()
            }
            tool_context.state['qloo_signals_object'] = signals
        
        return {
            "success": True,
            "signals_created": True,
            "demographics_provided": bool(demo_dict),
            "location_provided": bool(location_dict),
            "demographics": demo_dict,
            "location": location_dict,
            "message": "QlooSignals object created successfully",
            "stored_in_state": bool(tool_context)
        }
        
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"JSON parsing error: {str(e)}",
            "message": "Failed to parse input parameters"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to create QlooSignals object"
        }

def find_qloo_audiences(limit: int = 20, tool_context: ToolContext = None) -> Dict[str, Any]:
    """
    Uses QlooSignals from session state to find audiences.
    
    Args:
        limit (int): Maximum number of audiences to return
        tool_context (ToolContext): ADK tool context for state management
        
    Returns:
        Dict with audience search results
    """
    if not client:
        return {
            "success": False,
            "error": "Qloo client not available",
            "audiences": []
        }
    
    try:
        if not tool_context or not hasattr(tool_context, 'state') or 'qloo_signals_object' not in tool_context.state:
            return {
                "success": False,
                "error": "No QlooSignals found in session state. Please create signals first.",
                "audiences": []
            }
        
        signals = tool_context.state['qloo_signals_object']
        result = client.find_audiences(signals=signals, limit=limit)
        
        logging.info(f"🔍 Qloo API returned: {result['total_found']} audiences")
        
        # Format results for the agent
        audiences_info = []
        for audience in result['audiences']:
            audiences_info.append({
                "id": audience.id,
                "name": audience.name,
                "type": audience.parent_type,
                "entity_id": audience.entity_id
            })
        
        # Store audience results in session state
        if tool_context and hasattr(tool_context, 'state'):
            tool_context.state['qloo_audiences'] = {
                'audiences': audiences_info,
                'total_found': result['total_found'],
                'resolved_entities': result.get('resolved_entities', []),
                'search_timestamp': datetime.now().isoformat()
            }
        
        return {
            "success": True,
            "total_found": result['total_found'],
            "audiences": audiences_info,
            "resolved_entities": result.get('resolved_entities', []),
            "message": f"Found {result['total_found']} audiences matching your criteria"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "audiences": [],
            "message": "Failed to find audiences"
        }

def get_qloo_insights(
    entity_type: str = "brand", 
    limit: int = 10, 
    tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Gets entity insights using audiences and signals from session state.
    
    Args:
        entity_type (str): Type of entities to get insights for
        limit (int): Maximum number of insights to return
        tool_context (ToolContext): ADK tool context for state management
        
    Returns:
        Dict with entity insights
    """
    if not client:
        return {
            "success": False,
            "error": "Qloo client not available",
            "insights": []
        }
    
    try:
        if not tool_context or not hasattr(tool_context, 'state'):
            return {
                "success": False,
                "error": "No tool context available",
                "insights": []
            }
        
        signals = tool_context.state.get('qloo_signals_object')
        audience_data = tool_context.state.get('qloo_audiences')
        
        if not signals:
            return {
                "success": False,
                "error": "No QlooSignals found in session state. Please create signals first.",
                "insights": []
            }
        
        # Try to get audiences from state first, or find them if not available
        if not audience_data:
            audience_result = find_qloo_audiences(limit=10, tool_context=tool_context)
            if not audience_result['success']:
                return {
                    "success": False,
                    "error": "Could not find or retrieve audiences",
                    "insights": []
                }
            audience_data = tool_context.state.get('qloo_audiences')
        
        if not audience_data or len(audience_data['audiences']) == 0:
            return {
                "success": False,
                "error": "No audiences available to get insights for",
                "insights": []
            }
        
        # Extract audience IDs
        audience_ids = [aud['id'] for aud in audience_data['audiences'][:5]]
        
        logging.info(f"🎯 Getting {entity_type} insights for {len(audience_ids)} audiences")
        
        # Get insights using Qloo client
        insights = client.get_entity_insights(
            audience_ids=audience_ids,
            entity_type=entity_type,
            signals=signals,
            limit=limit
        )
        
        if insights['success']:
            # Format insights for the agent
            entities_info = []
            for entity in insights.get('results', {}).get('entities', []):
                entities_info.append({
                    "name": entity['name'],
                    "entity_id": entity['entity_id'],
                    "affinity": round(entity['query']['affinity'], 3),
                    "popularity": round(entity['popularity'], 3),
                    "description": entity.get('properties', {}).get('short_description', 'No description')[:200]
                })
            
            # Store insights in session state
            insights_key = f'qloo_insights_{entity_type}'
            if tool_context and hasattr(tool_context, 'state'):
                tool_context.state[insights_key] = {
                    'entity_type': entity_type,
                    'insights': entities_info,
                    'request_method': insights.get('request_method', 'Unknown'),
                    'timestamp': datetime.now().isoformat(),
                    'audience_ids_used': audience_ids
                }
            
            return {
                "success": True,
                "entity_type": entity_type,
                "insights": entities_info,
                "request_method": insights.get('request_method', 'Unknown'),
                "message": f"Found {len(entities_info)} {entity_type} insights"
            }
        else:
            return {
                "success": False,
                "error": insights.get('error', 'Unknown error'),
                "insights": [],
                "message": f"Failed to get {entity_type} insights"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "insights": [],
            "message": f"Failed to get {entity_type} insights"
        }

def get_session_summary(tool_context: ToolContext = None) -> Dict[str, Any]:
    """
    Provides a summary of all Qloo data stored in the current session state.
    """
    try:
        if not tool_context or not hasattr(tool_context, 'state'):
            return {
                "success": False,
                "error": "No tool context or state available",
                "summary": {}
            }
        
        state = tool_context.state
        if hasattr(state, 'keys'):
            state_keys = list(state.keys())
        else:
            state_keys = []
            state = {}
        
        summary = {
            "signals_created": 'qloo_signals' in state,
            "audiences_found": 'qloo_audiences' in state,
            "insights_available": [],
            "reports_generated": {
                "segment_profile": 'segment_profile_report' in state,
                "content_guide": 'content_personalization_guide' in state
            },
            "total_state_keys": len([k for k in state_keys if k.startswith('qloo_')])
        }
        
        # Check for different types of insights
        for key in state_keys:
            if key.startswith('qloo_insights_'):
                entity_type = key.replace('qloo_insights_', '')
                insight_data = state.get(key, {})
                summary["insights_available"].append({
                    "entity_type": entity_type,
                    "count": len(insight_data.get('insights', [])),
                    "timestamp": insight_data.get('timestamp', 'Unknown')
                })
        
        # Add detailed info if available
        if 'qloo_signals' in state:
            summary["signals_info"] = state['qloo_signals']
        
        if 'qloo_audiences' in state:
            audience_data = state['qloo_audiences']
            summary["audience_info"] = {
                "total_found": audience_data.get('total_found', 0),
                "audiences_stored": len(audience_data.get('audiences', [])),
                "resolved_entities": audience_data.get('resolved_entities', [])
            }
        
        return {
            "success": True,
            "summary": summary,
            "message": "Session state summary retrieved successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "summary": {},
            "message": "Failed to get session summary"
        }

def gather_insights_for_report(tool_context: ToolContext = None) -> Dict[str, Any]:
    """
    Gathers all insights data and formats it for report generation.
    """
    try:
        if not tool_context or not hasattr(tool_context, 'state'):
            return {
                "success": False,
                "error": "No tool context or state available",
                "insights_data": ""
            }
        
        state = tool_context.state
        
        # Gather all data
        signals_info = state.get('qloo_signals', {})
        audience_info = state.get('qloo_audiences', {})
        
        # Collect all insights
        all_insights = {}
        for key in state.keys():
            if key.startswith('qloo_insights_'):
                entity_type = key.replace('qloo_insights_', '')
                all_insights[entity_type] = state[key].get('insights', [])
        
        if not all_insights:
            return {
                "success": False,
                "error": "No insights available. Please collect insights first.",
                "insights_data": ""
            }
        
        # Format data for report generation
        formatted_data = []
        
        # Demographics and Location
        formatted_data.append("=== DEMOGRAPHIC & LOCATION SIGNALS ===")
        demo = signals_info.get('demographics', {})
        location = signals_info.get('location', {})
        
        if demo:
            formatted_data.append(f"Demographics: {json.dumps(demo)}")
        if location:
            formatted_data.append(f"Location: {json.dumps(location)}")
        
        # Audience Information
        formatted_data.append(f"\n=== AUDIENCE DATA ===")
        formatted_data.append(f"Total audiences found: {audience_info.get('total_found', 0)}")
        formatted_data.append(f"Audiences analyzed: {len(audience_info.get('audiences', []))}")
        
        # Insights by category
        for entity_type, insights in all_insights.items():
            formatted_data.append(f"\n=== {entity_type.upper()} INSIGHTS ===")
            for insight in insights:
                formatted_data.append(f"- {insight['name']} (Affinity: {insight['affinity']}, Popularity: {insight['popularity']})")
                if insight['description']:
                    formatted_data.append(f"  Description: {insight['description']}")
        
        insights_data = "\n".join(formatted_data)
        
        return {
            "success": True,
            "insights_data": insights_data,
            "entity_types": list(all_insights.keys()),
            "total_insights": sum(len(insights) for insights in all_insights.values()),
            "message": "Insights data gathered successfully for report generation"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "insights_data": "",
            "message": "Failed to gather insights data"
        }

def create_segment_profile_report(insights_data: str, tool_context: ToolContext = None) -> Dict[str, Any]:
    """
    Creates segment profile report using the segment_profile_agent.
    """
    try:
        if not insights_data:
            return {
                "success": False,
                "error": "No insights data provided",
                "report": ""
            }
        
        # Call the segment profile agent with the insights data
        result = segment_profile_agent.run(
            input_text=f"Create a comprehensive segment profile report based on this Qloo insights data:\n\n{insights_data}",
            context=tool_context
        )
        
        report = result.get('segment_profile_report', result.get('output', ''))
        
        # Store in session state
        if tool_context and hasattr(tool_context, 'state') and report:
            tool_context.state['segment_profile_report'] = {
                'report': report,
                'generated_at': datetime.now().isoformat()
            }
        
        return {
            "success": True,
            "report": report,
            "message": "Segment profile report generated successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "report": "",
            "message": "Failed to generate segment profile report"
        }

def create_content_guide_report(insights_data: str, tool_context: ToolContext = None) -> Dict[str, Any]:
    """
    Creates content personalization guide using the content_guide_agent.
    """
    try:
        if not insights_data:
            return {
                "success": False,
                "error": "No insights data provided",
                "guide": ""
            }
        
        # Call the content guide agent with the insights data
        result = content_guide_agent.run(
            input_text=f"Create a comprehensive content personalization guide based on this Qloo insights data:\n\n{insights_data}",
            context=tool_context
        )
        
        guide = result.get('content_personalization_guide', result.get('output', ''))
        
        # Store in session state
        if tool_context and hasattr(tool_context, 'state') and guide:
            tool_context.state['content_personalization_guide'] = {
                'guide': guide,
                'generated_at': datetime.now().isoformat()
            }
        
        return {
            "success": True,
            "guide": guide,
            "message": "Content personalization guide generated successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "guide": "",
            "message": "Failed to generate content personalization guide"
        }

# Create the Segment Profile Report Agent
segment_profile_agent = LlmAgent(
    name="segment_profile_reporter",
    model=Modelconfig.pro_model,
    description="Creates comprehensive segment profiles analyzing who the audience is, their cultural identity, and what they want in products.",
    instruction="""
You are a segment profiling expert. You will receive Qloo insights data and create a comprehensive profile of the target segment.

**Your Task:**
Analyze the provided Qloo insights data and create a detailed profile report covering:

1. **WHO THEY ARE**: Demographics, psychographics, lifestyle characteristics
2. **CULTURAL IDENTITY**: Values, interests, cultural touchpoints, social identity  
3. **WHAT THEY WANT**: Product preferences, decision-making factors, key motivators
4. **BEHAVIORAL PATTERNS**: How they engage with brands, entertainment, locations

**Report Structure:**
- Segment Overview (2-3 sentences about who this group is)
- Demographic & Geographic Profile 
- Cultural Identity & Values
- Product & Service Preferences  
- Key Behavioral Insights
- Strategic Implications

**Tone:** Professional but engaging, insights-driven, actionable
**Length:** Comprehensive but concise (300-500 words)

Focus on painting a clear picture of this segment as real people with specific needs, preferences, and characteristics based on the provided Qloo insights data.
""",
    tools=[],
    output_key="segment_profile_report"
)

# Create the Content Personalization Guide Agent  
content_guide_agent = LlmAgent(
    name="content_personalization_guide",
    model=Modelconfig.pro_model,
    description="Creates actionable content personalization strategies based on audience insights for creating personalized content.",
    instruction="""
You are a content personalization strategist. You will receive Qloo insights data and create an actionable guide for personalizing content for this specific audience segment.

**Your Task:**
Analyze the provided Qloo insights data and create a practical guide covering:

1. **CONTENT STRATEGY**: Tone, formats, messaging approach for this segment
2. **ENTITY REFERENCES**: Which brands, artists, movies, places, shows to reference and how
3. **PERSONALIZATION TACTICS**: Specific ways to customize content
4. **TESTING RECOMMENDATIONS**: What to A/B test for optimization
5. **SUCCESS METRICS**: How to measure personalized content performance

**Guide Structure:**
- Content Strategy Framework
- High-Affinity Entity References (brands, artists, places, etc.)
- Personalization Approach by Category
- Content Testing Strategy  
- Key Performance Indicators

**Tone:** Practical, strategic, actionable
**Length:** Detailed but focused (400-600 words)

Focus on specific, implementable tactics for content creators and marketers to personalize content for this exact audience segment based on their demonstrated affinities.
""",
    tools=[],
    output_key="content_personalization_guide"
)

# Create the main Qloo insights agent
root_agent = LlmAgent(
    name="qloo_insights_agent",
    model=Modelconfig.flash_lite_model,
    description="Qloo API specialist that gathers audience insights and coordinates report generation.",
    instruction="""
You are a Qloo API specialist that helps users analyze audiences based on demographics and location, then generates specialized reports.

**IMPORTANT: You only work with demographics and location signals. No entity queries or interests.**

**Your Workflow:**
1. Extract demographic and location signals from user input
2. Create QlooSignals using create_qloo_signals tool
3. Find audiences using find_qloo_audiences tool
4. Collect insights using get_qloo_insights for relevant entity types (brand, artist, movie, place, tv_show, podcast)
5. Call the appropriate report agents to generate specialized reports

**Signal Extraction Rules:**
For DEMOGRAPHICS:
- Age: "young/millennials/gen z" → "35_and_younger", "middle aged/gen x" → "36_to_55", "older/seniors/boomers" → "55_and_older"
- Gender: "male" or "female" (only if explicitly mentioned)

For LOCATION:
- Any location mentions: cities, states, countries, regions

**Report Generation:**
After collecting insights, generate reports using this process:
1. Call gather_insights_for_report to collect all session data into formatted string
2. Call create_segment_profile_report with the insights_data to generate WHO they are report
3. Call create_content_guide_report with the insights_data to generate HOW to personalize content

**Example Workflow:**
1. Extract: demographics='{"age": "35_and_younger", "gender": "female"}', location='{"query": "Los Angeles"}'
2. Call create_qloo_signals → find_qloo_audiences → get_qloo_insights for multiple entity types
3. Call gather_insights_for_report to format all data
4. Call create_segment_profile_report with insights_data for demographic profile
5. Call create_content_guide_report with insights_data for personalization strategy
6. Present both reports to user

**Response Guidelines:**
- Always explain what signals you extracted
- Provide clear summaries of insights collected
- Generate both reports unless user requests specific one
- Focus on actionable recommendations
""",
    tools=[
        FunctionTool(create_qloo_signals),
        FunctionTool(find_qloo_audiences), 
        FunctionTool(get_qloo_insights),
        FunctionTool(get_session_summary),
        FunctionTool(gather_insights_for_report),
        FunctionTool(create_segment_profile_report),
        FunctionTool(create_content_guide_report)
    ],
    output_key="qloo_agent_response"
)
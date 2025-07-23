import os
import vertexai
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from dotenv import load_dotenv
import logging

# Import your local modules
from .config import Modelconfig
from .tools import (
    detect_brands_in_text,
    get_entity_ids_with_context,
    get_demographics_insights_with_context,
    get_individual_brand_insights,
    analyze_all_brands_with_context,
    get_brand_analysis_summary,
    run_brand_analysis,
    get_coordinator_session_summary
)
from .subagent import brand_analysis_reporting_agent

load_dotenv()
project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "energyagentai")
location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
vertexai.init(project=project_id, location=location)

logging.info(f"🔧 [AGENT] Initialized Vertex AI - Project: {project_id}, Location: {location}")

# ==============================================================================
# MAIN BRAND ANALYSIS AGENT (This becomes the root_agent)
# ==============================================================================

brand_analysis_agent = LlmAgent(
    name="brand_analysis_agent",
    model=Modelconfig.flash_lite_model,
    description="Comprehensive brand analysis system that detects brands and provides detailed demographic and competitive insights.",
    instruction="""
You are a Brand Analysis specialist that helps users analyze brands mentioned in their messages.

**Your Workflow:**
1. Detect brands mentioned in user input using brand detection
2. Get entity IDs for all detected brands
3. Analyze demographics for all brand entities
4. Collect detailed insights for each brand individually
5. Generate comprehensive comparative analysis report

**Step-by-Step Process:**
1. **Brand Detection**: Use detect_brands_in_text to identify all brands in user message
2. **Entity Resolution**: Use get_entity_ids_with_context to find Qloo entity IDs for detected brands
3. **Demographics Analysis**: Use get_demographics_insights_with_context to analyze age/gender profiles
4. **Individual Insights**: Collect insights for each brand using their entity IDs as interest signals
5. **Comprehensive Report**: Use analyze_all_brands_with_context to generate final comparative analysis

**If No Brands Detected:**
- Inform user that no brands were found
- Ask them to mention specific brands they want to analyze

**CRITICAL: PRESENT COMPLETE REPORTS**
When analyze_all_brands_with_context returns a detailed analysis:
- Present the ENTIRE report exactly as provided
- DO NOT create summaries or shortened versions
- DO NOT regenerate or retry if the report seems long
- If a report appears to be cut off, present what was provided and note it may be truncated

**Response Format:**
- Brief explanation of what was analyzed
- Present the complete detailed cultural analysis report
- Do not add your own interpretation or summary after presenting the report
- If the report was created successfully, make sure you display it fully instead of adding your input
- When report is created your job is just to present it as is



Always run the complete workflow and present full detailed analysis reports.
""",
    tools=[
        FunctionTool(detect_brands_in_text),
        FunctionTool(get_entity_ids_with_context),
        FunctionTool(get_demographics_insights_with_context),
        FunctionTool(get_individual_brand_insights),
        FunctionTool(analyze_all_brands_with_context),
        FunctionTool(get_brand_analysis_summary)
    ],
    output_key="brand_analysis_response"
)

logging.info(f"🤖 [AGENT] Created brand_analysis_agent")

# ==============================================================================
# MULTI-AGENT COORDINATOR
# ==============================================================================

multi_agent_coordinator = LlmAgent(
    name="multi_agent_coordinator",
    model=Modelconfig.flash_lite_model,
    description="Main coordinator that routes requests to specialized agents: Brand Analysis Agent and future Merch Recommendation Agent.",
    instruction="""
You are the Multi-Agent Coordinator that manages specialized analysis agents.

**Available Agents:**
1. **Brand Analysis Agent**: Detects brands in user messages and provides comprehensive competitive analysis including demographics, insights, and strategic recommendations.

**Future Agents (Coming Soon):**
2. **Merch Recommendation Agent**: Will provide merchandise recommendations based on brand analysis.

**Your Role:**
- Analyze user requests to determine which agent(s) to activate
- Coordinate between agents when needed
- Present results in a clear, organized manner
- Manage session state across different agent workflows

**Routing Logic:**
- **Brand Analysis**: Trigger when user mentions brands or asks for brand analysis
- **General Analysis**: If user message contains brand mentions, automatically run brand analysis
- **Multi-Agent Workflows**: When analysis from one agent should inform another

**Response Structure:**
1. Briefly explain what analysis you're performing
2. Call the appropriate agent(s)
3. Present the results clearly
4. Offer follow-up actions or additional analysis

**Example Triggers for Brand Analysis:**
- "Compare Apple and Samsung"
- "Analyze Nike's demographics" 
- "I'm interested in Tesla and BMW"
- "Compare Chelsea FC with Liverpool FC"
- Any message containing recognizable brand names

Always start with brand detection when user input might contain brands.
""",
    tools=[
        FunctionTool(run_brand_analysis),
        FunctionTool(get_coordinator_session_summary)
    ],
    output_key="coordinator_response"
)

logging.info(f"🤖 [AGENT] Created multi_agent_coordinator")

# ==============================================================================
# ROOT AGENT (Required by ADK)
# ==============================================================================

# ADK looks for 'root_agent' specifically
root_agent = brand_analysis_agent

logging.info(f"✅ [AGENT] Set root_agent = brand_analysis_agent")



logging.info(f"📦 [AGENT] Imported sub-agents from subagent.py")

# ==============================================================================
# ADK CONFIGURATION
# ==============================================================================

APP_NAME = "BrandAnalysisAgent"
USER_ID = "test_user"
SESSION_ID = "test_session"

def initialize_session_state():
    """Initialize the session state with default values for brand analysis."""
    return {
        "user_name": "Brand Analyst",
        "analysis_history": [],
        "detected_brands": None,
        "brand_entity_details": None,
        "brand_demographics": None,
        "all_brand_insights": None,
        "brand_analysis_report": None
    }

# ==============================================================================
# RUNNER AND SESSION SETUP
# ==============================================================================

def create_runner():
    """Create and configure the ADK runner with session management."""
    logging.info(f"🏗️ [RUNNER] Creating ADK runner for {APP_NAME}")
    
    # Create session service
    session_service = InMemorySessionService()
    
    # Create a new session with initial state
    session = session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        state=initialize_session_state(),
    )
    
    logging.info(f"📝 [RUNNER] Created session - ID: {session.id}, User: {session.user_id}")
    
    # Create the runner
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )
    
    logging.info(f"✅ [RUNNER] Runner created successfully")
    
    return runner, session

# ==============================================================================
# TEST RUNNER
# ==============================================================================

async def run_test():
    """Test the brand analysis system."""
    
    
    logging.info("🚀 [TEST] Starting Brand Analysis Test")
    logging.info("=" * 80)
    
    # Create runner and session
    runner, session = create_runner()
    
    # Test message
    test_message = "Compare Chelsea Football Club with Arsenal FC"
    logging.info(f"📝 [TEST] Test message: '{test_message}'")
    
    # Create content
    content = types.Content(role='user', parts=[types.Part(text=test_message)])
    
    logging.info(f"🤖 [TEST] Running agent...")
    
    # Run the agent
    events_async = runner.run_async(
        session_id=session.id,
        user_id=session.user_id,
        new_message=content
    )
    
    # Process events
    final_response = None
    async for event in events_async:
        logging.info(f"📡 [TEST] Event: {event}")
        if hasattr(event, 'final_response') and event.final_response:
            if hasattr(event, 'content') and event.content:
                final_response = event.content
    
    if final_response:
        logging.info(f"✅ [TEST] Final response received")
        logging.info(f"📊 [TEST] Response: {final_response}")
    else:
        logging.info(f"⚠️ [TEST] No final response received")
    
    logging.info("=" * 80)
    logging.info("✅ [TEST] Test completed")

def get_system_status():
    """Get current system status for monitoring."""
    logging.info("📊 [STATUS] Getting system status")
    
    try:
        from src.qloo import QlooAPIClient
        
        # Check Qloo client
        qloo_key = os.getenv("QLOO_API_KEY")
        qloo_available = bool(qloo_key)
        
        if qloo_available:
            client = QlooAPIClient(api_key=qloo_key)
            logging.info("✅ [STATUS] Qloo client initialized successfully")
        else:
            logging.info("❌ [STATUS] QLOO_API_KEY not found")
        
        status = {
            "app_name": APP_NAME,
            "vertex_ai_initialized": bool(project_id and location),
            "qloo_api_available": qloo_available,
            "root_agent_available": root_agent is not None,
            "agents_loaded": {
                "brand_analysis_agent": brand_analysis_agent is not None,
                "multi_agent_coordinator": multi_agent_coordinator is not None,
                "brand_detection_agent": brand_detection_agent is not None,
                "brand_analysis_reporting_agent": brand_analysis_reporting_agent is not None
            },
            "tools_count": len(root_agent.tools) if root_agent else 0,
            "project_id": project_id,
            "location": location
        }
        
        logging.info(f"✅ [STATUS] System status retrieved")
        return status
        
    except Exception as e:
        logging.info(f"❌ [STATUS] Error getting system status: {e}")
        return {
            "error": str(e),
            "vertex_ai_initialized": False,
            "qloo_api_available": False
        }

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

if __name__ == "__main__":
    import asyncio
    
    logging.info("🏃 [MAIN] Executing agent.py directly")
    
    # Run system checks
    status = get_system_status()
    logging.info(f"\n📊 [MAIN] System Status: {status}")
    
    logging.info(f"\n🎯 [MAIN] ADK Configuration:")
    logging.info(f"   App Name: {APP_NAME}")
    logging.info(f"   Root Agent: {root_agent.name if root_agent else 'None'}")
    logging.info(f"   Tools Available: {len(root_agent.tools) if root_agent else 0}")
    
    # Run async test
    logging.info(f"\n🧪 [MAIN] Running async test...")
    try:
        asyncio.run(run_test())
    except Exception as e:
        logging.info(f"❌ [MAIN] Test failed: {e}")
    
    logging.info("\n✅ [MAIN] Brand Analysis Agent ready for ADK!")
    logging.info("   - root_agent is available")
    logging.info("   - Session management configured")
    logging.info("   - Runner setup complete")
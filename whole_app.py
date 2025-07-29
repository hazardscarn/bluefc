# whole_app.py - Enhanced Chelsea FC App with Fixed Content Creation
import streamlit as st
import time
import uuid
import json
import tempfile
import os
from typing import Dict, List, Any, Optional
import requests

# Import the modular content creation functionality
from junk.content_creation_module import (
    connect_to_content_agent,
    run_content_creation_workflow,
    display_final_video,
    get_default_form_values,
    get_form_help_text,
    create_user_query,
    validate_user_inputs,
    reset_content_creation_state,
    get_content_creation_status,
    render_content_creation_form,
    render_content_creation_progress_section
)

# Agent Engine imports
try:
    from vertexai import agent_engines
    AGENT_ENGINE_AVAILABLE = True
except ImportError:
    AGENT_ENGINE_AVAILABLE = False

# ============================================================================
# CONFIGURATION
# ============================================================================
PROJECT_ID = "energyagentai"
LOCATION = "us-central1" 
RESOURCE_ID = "7774435613771563008"
RESOURCE_NAME = f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{RESOURCE_ID}"

# Content Creation Agent
CONTENT_AGENT_RESOURCE_ID = "7019519726233583616"
CONTENT_AGENT_RESOURCE_NAME = f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{CONTENT_AGENT_RESOURCE_ID}"

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Chelsea FC Merchandise Agent",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# MODERN STYLING
# ============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* Hide Streamlit elements */
.stApp > header {background-color: transparent;}
.stApp > header [data-testid="stHeader"] {display: none;}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display:none;}

/* Global styling */
html, body, [class*="st"] {
    font-family: 'Inter', sans-serif;
    color: #1a1a1a;
}

.stApp {
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
}

/* Navigation */
.nav-header {
    background: white;
    padding: 1.5rem 2rem;
    margin: -1rem -1rem 2rem -1rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    border-radius: 0 0 16px 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.nav-logo {
    font-size: 1.8rem;
    font-weight: 800;
    color: #034694;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.status-indicator {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-size: 0.9rem;
    font-weight: 500;
}

.status-connected {
    background: linear-gradient(135deg, #d1fae5, #10b981);
    color: #065f46;
    border: 1px solid #059669;
}

.status-disconnected {
    background: linear-gradient(135deg, #fef3c7, #f59e0b);
    color: #92400e;
    border: 1px solid #d97706;
}

/* Hero Section */
.hero-section {
    background: linear-gradient(135deg, #034694 0%, #1e3c72 100%);
    color: white;
    padding: 3rem;
    border-radius: 20px;
    text-align: center;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}

.hero-title {
    font-size: 2.8rem;
    font-weight: 800;
    margin-bottom: 1rem;
    text-shadow: 0 4px 8px rgba(0,0,0,0.3);
}

.hero-subtitle {
    font-size: 1.2rem;
    opacity: 0.9;
    max-width: 600px;
    margin: 0 auto;
    line-height: 1.6;
}

/* Cards */
.content-card {
    background: white;
    border-radius: 16px;
    padding: 2rem;
    margin: 1rem 0;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    border: 1px solid #e2e8f0;
    transition: all 0.3s ease;
}

.content-card:hover {
    box-shadow: 0 8px 32px rgba(0,0,0,0.12);
    transform: translateY(-2px);
}

/* Feature Cards */
.feature-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    margin: 2rem 0;
}

.feature-card {
    background: white;
    border-radius: 16px;
    padding: 2rem;
    text-align: center;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    border: 1px solid #e2e8f0;
    transition: all 0.3s ease;
    cursor: pointer;
}

.feature-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.15);
}

.feature-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
}

.feature-title {
    font-size: 1.3rem;
    font-weight: 600;
    color: #034694;
    margin-bottom: 1rem;
}

.feature-description {
    color: #64748b;
    line-height: 1.6;
    margin-bottom: 1.5rem;
}

/* Status tracking */
.status-pill {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    border-radius: 12px;
    font-size: 0.9rem;
    font-weight: 500;
    transition: all 0.3s ease;
    margin: 0.25rem 0;
}

.status-pending {
    background: #f1f5f9;
    color: #64748b;
    border: 1px solid #e2e8f0;
}

.status-running {
    background: linear-gradient(135deg, #fef3c7, #fbbf24);
    color: #92400e;
    border: 1px solid #f59e0b;
    animation: pulse 2s infinite;
}

.status-completed {
    background: linear-gradient(135deg, #d1fae5, #10b981);
    color: #065f46;
    border: 1px solid #059669;
}

.status-error {
    background: linear-gradient(135deg, #fee2e2, #ef4444);
    color: #991b1b;
    border: 1px solid #dc2626;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.8; }
}

/* Product card styling */
.product-card {
    background: white;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    transition: all 0.3s ease;
    margin: 0.5rem 0;
}

.product-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.12);
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #16a34a 0%, #15803d 100%) !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 0.75rem 2rem !important;
    border-radius: 12px !important;
    border: none !important;
    transition: all 0.3s ease !important;
    font-size: 1rem !important;
    box-shadow: 0 4px 12px rgba(22, 163, 74, 0.3) !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #15803d 0%, #166534 100%) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(22, 163, 74, 0.4) !important;
}

/* Customization button variant */
.stButton.customization-button > button {
    background: linear-gradient(135deg, #034694 0%, #1e3c72 100%) !important;
    box-shadow: 0 4px 12px rgba(3, 70, 148, 0.3) !important;
}

.stButton.customization-button > button:hover {
    background: linear-gradient(135deg, #1e3c72 0%, #034694 100%) !important;
    box-shadow: 0 6px 20px rgba(3, 70, 148, 0.4) !important;
}

/* Loading animation */
.loading-animation {
    display: inline-block;
    width: 20px;
    height: 20px;
    border: 3px solid #f3f3f3;
    border-top: 3px solid #16a34a;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Success callout */
.success-callout {
    background: linear-gradient(135deg, #d1fae5, #a7f3d0);
    border: 1px solid #059669;
    border-radius: 12px;
    padding: 1rem;
    margin: 1rem 0;
    color: #065f46;
}

/* Error callout */
.error-callout {
    background: linear-gradient(135deg, #fee2e2, #fecaca);
    border: 1px solid #dc2626;
    border-radius: 12px;
    padding: 1rem;
    margin: 1rem 0;
    color: #991b1b;
}

/* Video container */
.video-container {
    background: white;
    border-radius: 16px;
    padding: 2rem;
    margin: 2rem 0;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    border: 1px solid #e2e8f0;
    text-align: center;
}

/* Download button */
.download-button {
    background: linear-gradient(135deg, #7c3aed 0%, #5b21b6 100%) !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 0.75rem 2rem !important;
    border-radius: 12px !important;
    border: none !important;
    text-decoration: none !important;
    display: inline-block !important;
    margin-top: 1rem !important;
    transition: all 0.3s ease !important;
}

.download-button:hover {
    background: linear-gradient(135deg, #5b21b6 0%, #4c1d95 100%) !important;
    transform: translateY(-1px) !important;
}

/* Responsive */
@media (max-width: 768px) {
    .hero-title { font-size: 2rem; }
    .feature-grid { grid-template-columns: 1fr; }
}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

def initialize_session_state():
    """Initialize all session state variables"""
    if "current_page" not in st.session_state:
        st.session_state.current_page = "home"
    
    if "user_id" not in st.session_state:
        st.session_state.user_id = f"user_{uuid.uuid4().hex[:8]}"
    
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"session_{uuid.uuid4().hex[:8]}"
    
    # Analysis state
    if "agent_running" not in st.session_state:
        st.session_state.agent_running = False
    
    if "analysis_started" not in st.session_state:
        st.session_state.analysis_started = False
    
    if "results" not in st.session_state:
        st.session_state.results = {}
    
    if "step_status" not in st.session_state:
        st.session_state.step_status = {}
    
    if "query_to_run" not in st.session_state:
        st.session_state.query_to_run = None
    
    if "analysis_events" not in st.session_state:
        st.session_state.analysis_events = []
    
    if "current_step" not in st.session_state:
        st.session_state.current_step = 0
    
    # Customization state
    if "customization_running" not in st.session_state:
        st.session_state.customization_running = False
    
    if "customization_results" not in st.session_state:
        st.session_state.customization_results = {}
    
    if "customization_status" not in st.session_state:
        st.session_state.customization_status = ""
    
    # Content Creation state
    if "content_creation_running" not in st.session_state:
        st.session_state.content_creation_running = False
    
    if "content_creation_results" not in st.session_state:
        st.session_state.content_creation_results = {}
    
    if "content_creation_status" not in st.session_state:
        st.session_state.content_creation_status = ""
    
    if "content_creation_step_status" not in st.session_state:
        st.session_state.content_creation_step_status = {}
    
    if "final_video_url" not in st.session_state:
        st.session_state.final_video_url = None
    
    if "downloaded_video_path" not in st.session_state:
        st.session_state.downloaded_video_path = None
    
    # Agent Engine
    if "agent_app" not in st.session_state:
        st.session_state.agent_app = None
    
    if "agent_session" not in st.session_state:
        st.session_state.agent_session = None
    
    if "content_agent_app" not in st.session_state:
        st.session_state.content_agent_app = None
    
    if "content_agent_session" not in st.session_state:
        st.session_state.content_agent_session = None

# ============================================================================
# AGENT ENGINE MANAGER
# ============================================================================

def connect_to_agent_engine():
    """Connect to the deployed Agent Engine"""
    if not AGENT_ENGINE_AVAILABLE:
        st.error("❌ Vertex AI not available. Please install: pip install google-cloud-aiplatform[adk,agent_engines]")
        return False
    
    try:
        if st.session_state.agent_app is None:
            st.session_state.agent_app = agent_engines.get(RESOURCE_NAME)
        
        if st.session_state.agent_session is None:
            session = st.session_state.agent_app.create_session(user_id=st.session_state.user_id)
            st.session_state.agent_session = session
        
        return True
    except Exception as e:
        st.error(f"Failed to connect to Agent Engine: {e}")
        return False

def connect_to_content_agent():
    """Connect to content creation agent"""
    if not AGENT_ENGINE_AVAILABLE:
        return False
    
    try:
        if st.session_state.content_agent_app is None:
            st.session_state.content_agent_app = agent_engines.get(CONTENT_AGENT_RESOURCE_NAME)
        
        if st.session_state.content_agent_session is None:
            session = st.session_state.content_agent_app.create_session(user_id=st.session_state.user_id)
            st.session_state.content_agent_session = session
        
        return True
    except Exception as e:
        return False

def create_video(location, age, hobbies, additional_details, theme):
    """Create video - simple version"""
    if not connect_to_content_agent():
        st.session_state.content_creating = False
        return
    
    query = f"Age: {age}, Location: {location}, Hobbies: {hobbies}, Additional Details: {additional_details}, Theme: {theme}"
    
    try:
        for event in st.session_state.content_agent_app.stream_query(
            user_id=st.session_state.user_id,
            session_id=st.session_state.content_agent_session["id"],
            message=query
        ):
            if "state_delta" in event.get("actions", {}):
                state_delta = event["actions"]["state_delta"]
                if state_delta:
                    video_url = state_delta.get("final_video_url") or state_delta.get("output_video_url")
                    if video_url:
                        st.session_state.video_url = video_url
                        break
        
        st.session_state.content_creating = False
        st.rerun()
        
    except Exception as e:
        st.error(f"Video creation failed: {e}")
        st.session_state.content_creating = False

def download_video(video_url):
    """Download video from URL"""
    try:
        temp_dir = tempfile.mkdtemp()
        video_filename = f"chelsea_video_{uuid.uuid4().hex[:8]}.mp4"
        local_path = os.path.join(temp_dir, video_filename)
        
        response = requests.get(video_url, stream=True, timeout=60)
        response.raise_for_status()
        
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        return local_path if os.path.exists(local_path) and os.path.getsize(local_path) > 0 else None
    except:
        return None

def connect_to_content_agent():
    """Connect to the content creation agent"""
    if not AGENT_ENGINE_AVAILABLE:
        return False
    
    try:
        if st.session_state.content_agent_app is None:
            st.session_state.content_agent_app = agent_engines.get(CONTENT_AGENT_RESOURCE_NAME)
        
        if st.session_state.content_agent_session is None:
            session = st.session_state.content_agent_app.create_session(user_id=st.session_state.user_id)
            st.session_state.content_agent_session = session
        
        return True
    except Exception as e:
        st.error(f"Failed to connect to Content Agent: {e}")
        return False

def create_video_content(location: str, age: int, hobbies: str, additional_details: str, theme: str):
    """Create video content - simple version"""
    if not connect_to_content_agent():
        st.session_state.content_creating = False
        return
    
    # Create query
    query = f"Age: {age}, Location: {location}, Hobbies: {hobbies}, Additional Details: {additional_details}, Theme: {theme}"
    
    try:
        # Stream query and wait for final video URL
        for event in st.session_state.content_agent_app.stream_query(
            user_id=st.session_state.user_id,
            session_id=st.session_state.content_agent_session["id"],
            message=query
        ):
            # Look for final video URL in state
            if "state_delta" in event.get("actions", {}):
                state_delta = event["actions"]["state_delta"]
                if state_delta:
                    final_url = state_delta.get("final_video_url") or state_delta.get("output_video_url")
                    if final_url:
                        st.session_state.final_video_url = final_url
                        break
        
        st.session_state.content_creating = False
        st.rerun()
        
    except Exception as e:
        st.error(f"Video creation failed: {e}")
        st.session_state.content_creating = False

def download_video(video_url: str) -> Optional[str]:
    """Download video from URL"""
    if not video_url:
        return None
    
    try:
        temp_dir = tempfile.mkdtemp()
        video_filename = f"chelsea_video_{uuid.uuid4().hex[:8]}.mp4"
        local_video_path = os.path.join(temp_dir, video_filename)
        
        response = requests.get(video_url, stream=True, timeout=60)
        response.raise_for_status()
        
        with open(local_video_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        if os.path.exists(local_video_path) and os.path.getsize(local_video_path) > 0:
            return local_video_path
        
        return None
    except Exception:
        return None

# ============================================================================
# CONTENT CREATION PAGE (Uses Modular Functions)
# ============================================================================

def content_creation_page():
    """Enhanced content creation page with video generation using modular functions"""
    st.markdown("# 📝 Personalized Content Creation")
    st.markdown("Create AI-generated personalized Chelsea FC videos based on your preferences")
    
    # Check current status
    status = get_content_creation_status()
    
    # Debug information
    st.sidebar.markdown("### 🐛 Debug Info")
    st.sidebar.json({
        "running": status["running"],
        "has_results": status["has_results"], 
        "has_video": status["has_video"],
        "agent_connected": status["agent_connected"],
        "session_keys": list(st.session_state.keys())
    })
    
    # Display completed video if available
    if status["has_video"] and not status["running"]:
        display_final_video()
        return
    
    # Display progress if creation is running
    if status["running"]:
        st.success("🎬 Content creation is running!")
        render_content_creation_progress_section()
        return
    
    # Input form for user preferences
    render_content_creation_form()

# ============================================================================
# EXISTING FUNCTIONS (Keep all your existing functions)
# ============================================================================

def run_customization_query(product_id: str, customization_prompt: str):
    """Run product customization using Agent Engine with proper state tracking"""
    if not connect_to_agent_engine():
        return
    
    try:
        st.session_state.customization_status = "🔍 Validating product and context..."
        
        # Create customization query
        query = f'Customize product_id: "{product_id}" with the following instructions: {customization_prompt}'
        
        # Track state changes specifically for customization
        customization_state = {}
        event_count = 0
        
        st.session_state.customization_status = "🎨 Generating customized product..."
        
        # Stream the customization query
        for event in st.session_state.agent_app.stream_query(
            user_id=st.session_state.user_id,
            session_id=st.session_state.agent_session["id"],
            message=query
        ):
            event_count += 1
            
            # Track state changes
            if "state_delta" in event.get("actions", {}):
                state_delta = event["actions"]["state_delta"]
                if state_delta:
                    for key, value in state_delta.items():
                        customization_state[key] = value
                        
                        # Update status based on what we're receiving
                        if key == "customized_image_url":
                            st.session_state.customization_status = "🖼️ Image generated successfully!"
                        elif key == "customization_reasoning":
                            st.session_state.customization_status = "🧠 Analyzing customization rationale..."
            
            # Check for agent responses (including error messages)
            if "content" in event:
                for part in event["content"].get("parts", []):
                    if "text" in part:
                        text = part["text"]
                        # Check for error messages
                        if "unable to customize" in text.lower() or "failed" in text.lower():
                            st.session_state.customization_status = "❌ Customization failed"
                            st.session_state.customization_results = {
                                "error": text,
                                "suggestions": [
                                    "Check that the product ID exists in recommendations",
                                    "Ensure persona data is available from previous analysis",
                                    "Try a different product from the recommendations list"
                                ]
                            }
                            st.session_state.customization_running = False
                            return
        
        # Process final results
        if customization_state.get("customized_image_url"):
            st.session_state.customization_results = {
                "success": True,
                "customized_image_url": customization_state.get("customized_image_url", ""),
                "customization_reasoning": customization_state.get("customization_reasoning", ""),
                "original_product": customization_state.get("original_product", {}),
                "product_id": product_id
            }
            st.session_state.customization_status = "✅ Customization completed successfully!"
        else:
            # No customization results - likely an error
            st.session_state.customization_results = {
                "error": "No customized image was generated. This could be due to missing context or product not found.",
                "suggestions": [
                    f"Verify product ID '{product_id}' exists in your recommendations",
                    "Ensure you've run a product recommendation analysis first",
                    "Check that persona and audience data is available",
                    "Try with a different product ID from the recommendations list"
                ]
            }
            st.session_state.customization_status = "❌ Customization failed"
        
        st.session_state.customization_running = False
        
    except Exception as e:
        st.session_state.customization_results = {
            "error": f"Customization failed with error: {str(e)}",
            "suggestions": [
                "Check your internet connection",
                "Verify Agent Engine is accessible", 
                "Try again in a few moments"
            ]
        }
        st.session_state.customization_status = f"❌ Error: {str(e)}"
        st.session_state.customization_running = False

def render_real_time_progress(results: Dict):
    """Render real-time progress updates in center"""
    
    col1, col2 = st.columns([1, 1])
    
    # Left column - Detected Information
    with col1:
        st.markdown("### 🎯 Detected Information")
        
        # Show detected signals
        if results.get("detected_signals") and any(results["detected_signals"].values()):
            st.markdown("#### 📍 Demographic Signals")
            signals = results["detected_signals"]
            
            if signals.get("age"):
                st.markdown("**👥 Age Groups**")
                for age in signals["age"]:
                    st.markdown(f'<div style="background: #f8fafc; padding: 0.4rem 0.8rem; border-radius: 8px; margin: 0.25rem 0; font-size: 0.8rem; color: #475569; border-left: 3px solid #034694;">{age.replace("_", " ").title()}</div>', unsafe_allow_html=True)
            
            if signals.get("location"):
                st.markdown("**📍 Locations**")
                for location in signals["location"]:
                    st.markdown(f'<div style="background: #f8fafc; padding: 0.4rem 0.8rem; border-radius: 8px; margin: 0.25rem 0; font-size: 0.8rem; color: #475569; border-left: 3px solid #034694;">{location}</div>', unsafe_allow_html=True)
        
        # Show detected audiences
        if results.get("detected_audience_names"):
            st.markdown("#### 🎯 Target Audiences")
            for audience in results["detected_audience_names"][:4]:
                st.markdown(f'<div style="background: #f8fafc; padding: 0.4rem 0.8rem; border-radius: 8px; margin: 0.25rem 0; font-size: 0.8rem; color: #475569; border-left: 3px solid #034694;">{audience}</div>', unsafe_allow_html=True)
            
            if len(results["detected_audience_names"]) > 4:
                st.caption(f"+ {len(results['detected_audience_names']) - 4} more audiences")
        
        # Show persona if available
        if results.get("persona_name"):
            st.markdown("#### 👤 Generated Persona")
            st.markdown(f'<div style="background: #f0f9ff; padding: 0.6rem 0.8rem; border-radius: 8px; margin: 0.25rem 0; font-size: 0.9rem; color: #0c4a6e; border-left: 3px solid #0ea5e9; font-weight: 600;">{results["persona_name"]}</div>', unsafe_allow_html=True)
        
        # Show placeholder if nothing detected yet
        if not any([results.get("detected_signals"), results.get("detected_audience_names"), results.get("persona_name")]):
            st.info("🔍 Detected information will appear here during analysis")
    
    # Right column - Analysis Status
    with col2:
        st.markdown("### 📊 Analysis Progress")
        
        analysis_steps = [
            "🔍 Detecting demographic signals...",
            "👥 Finding target audiences...",
            "🧠 Generating cultural insights...",
            "👤 Creating consumer persona...",
            "🛍️ Finding perfect products...",
            "✅ Analysis complete!"
        ]
        
        # Progress bar
        completed = sum(1 for step in analysis_steps if st.session_state.step_status.get(step) == "completed")
        progress = completed / len(analysis_steps)
        st.progress(progress)
        st.caption(f"{completed}/{len(analysis_steps)} steps completed")
        
        # Status pills
        for step in analysis_steps:
            status = st.session_state.step_status.get(step, "pending")
            
            if status == "pending":
                icon, css_class = "⚪", "status-pending"
            elif status == "running":
                icon, css_class = "🔄", "status-running"
            elif status == "completed":
                icon, css_class = "✅", "status-completed"
            else:
                icon, css_class = "❌", "status-error"
            
            step_name = step.replace("🔍", "").replace("👥", "").replace("🧠", "").replace("👤", "").replace("🛍️", "").replace("✅", "").strip()
            
            st.markdown(f'''
            <div class="status-pill {css_class}">
                <span>{icon}</span>
                <span>{step_name}</span>
            </div>
            ''', unsafe_allow_html=True)
        
        # Show live data count
        if results:
            data_items = [
                ("Audiences", len(results.get("detected_audience_names", []))),
                ("Insights", sum(1 for key in ["brand_insight", "movie_insight", "artist_insight"] if results.get(key))),
                ("Products", len(results.get("recommendations", [])))
            ]
            
            st.markdown("#### 📈 Live Data")
            for item_name, count in data_items:
                if count > 0:
                    st.markdown(f'<div style="background: #ecfdf5; padding: 0.3rem 0.6rem; border-radius: 6px; margin: 0.2rem 0; font-size: 0.8rem; color: #065f46; display: inline-block; margin-right: 0.5rem;">{item_name}: {count}</div>', unsafe_allow_html=True)

def check_step_completion(step_idx: int, state: Dict) -> bool:
    """Check if analysis step is complete based on state"""
    if step_idx == 0:  # Signals
        return bool(state.get("detected_signals"))
    elif step_idx == 1:  # Audiences
        return bool(state.get("detected_audience_names"))
    elif step_idx == 2:  # Cultural insights
        return bool(state.get("brand_insight"))
    elif step_idx == 3:  # Persona
        return bool(state.get("persona_name"))
    elif step_idx == 4:  # Products
        return bool(state.get("recommendations"))
    return False

# ============================================================================
# UI COMPONENTS
# ============================================================================

def render_navigation():
    """Render navigation header"""
    # Status check for both agents
    product_connected = st.session_state.agent_app is not None
    content_connected = st.session_state.content_agent_app is not None
    
    # Determine overall status
    if product_connected and content_connected:
        status_text = "Both Connected"
        status_class = "status-connected"
        status_icon = "🟢"
    elif product_connected or content_connected:
        status_text = "Partially Connected"
        status_class = "status-disconnected"
        status_icon = "🟡"
    else:
        status_text = "Disconnected"
        status_class = "status-disconnected"
        status_icon = "🔴"
    
    st.markdown(f"""
    <div class="nav-header">
        <div class="nav-logo">⚽ Chelsea FC Merchandise Agent</div>
        <div class="status-indicator {status_class}">
            {status_icon} Agent Engine {status_text}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation pills
    pages = ["🏠 Home", "🎯 Product Recommendation", "🎨 Product Customization", "📝 Personalized Content", "ℹ️ About"]
    
    selected = st.pills("Navigate", pages, selection_mode="single")
    
    if selected:
        page_map = {
            "🏠 Home": "home",
            "🎯 Product Recommendation": "recommendation", 
            "🎨 Product Customization": "customization",
            "📝 Personalized Content": "content",
            "ℹ️ About": "about"
        }
        
        new_page = page_map[selected]
        if new_page != st.session_state.current_page:
            st.session_state.current_page = new_page
            st.rerun()

def render_hero():
    """Render hero section"""
    st.markdown("""
    <div class="hero-section">
        <div class="hero-title">⚽ Chelsea FC Merchandise Agent</div>
        <div class="hero-subtitle">
            AI-powered personalized merchandise recommendations and video content creation using Google's Agent Engine and cultural intelligence
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_analysis_results():
    """Render analysis results"""
    results = st.session_state.results
    
    if not results:
        return
    
    # Persona section
    if results.get("persona_name"):
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown(f"### 👤 Persona: {results['persona_name']}")
        if results.get("persona_description"):
            st.markdown(results["persona_description"])
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Product recommendations in 3x2 grid
    if results.get("recommendations"):
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown("### 🛍️ Product Recommendations")
        
        recommendations = results["recommendations"]
        
        # Create 3x2 grid (3 columns, 2 rows)
        for row in range(2):  # 2 rows
            cols = st.columns(3)  # 3 columns
            for col in range(3):
                product_idx = row * 3 + col
                if product_idx < len(recommendations):
                    product = recommendations[product_idx]
                    
                    with cols[col]:
                        # Product image
                        st.image(
                            product.get('image_url', 'https://via.placeholder.com/300/034694/FFFFFF?text=Product'), 
                            use_container_width=True
                        )
                        
                        # Product name
                        st.markdown(f"**{product.get('name', 'Unknown Product')}**")
                        
                        # Product ID (smaller font)
                        product_id = product.get('product_id', 'N/A')
                        st.markdown(f'<p style="font-size: 0.8rem; color: #64748b; margin: 0.25rem 0;">{product_id}</p>', 
                                   unsafe_allow_html=True)
                        
                        # Price
                        st.markdown(f'<div style="font-size: 1.1rem; font-weight: 700; color: #034694; margin: 0.5rem 0;">${product.get("price", 0)}</div>', 
                                   unsafe_allow_html=True)
                        
                        # Match percentage
                        if product.get('similarity'):
                            match_percent = int(product['similarity'] * 100)
                            st.markdown(f'<div style="background: linear-gradient(135deg, #dbeafe, #3b82f6); color: #1e40af; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.8rem; font-weight: 500; display: inline-block; margin: 0.5rem 0;">{match_percent}% Match</div>', 
                                       unsafe_allow_html=True)
                        
                        # Description
                        if product.get('description'):
                            st.markdown(f'<p style="color: #64748b; font-size: 0.85rem; line-height: 1.4; margin-top: 0.5rem;">{product["description"][:80]}{"..." if len(product["description"]) > 80 else ""}</p>', 
                                       unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

def render_cultural_insights():
    """Render cultural insights in expandable sections"""
    results = st.session_state.results
    
    if any([results.get("brand_insight"), results.get("movie_insight"), results.get("artist_insight"), results.get("podcast_insight"), results.get("tag_insight")]):
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown("### 🧠 Cultural Insights")
        
        # Brand insights
        if results.get("brand_insight"):
            with st.expander("🏷️ **Brand Affinities**", expanded=False):
                st.markdown(results["brand_insight"])
        
        # Movie insights
        if results.get("movie_insight"):
            with st.expander("🎬 **Movie Preferences**", expanded=False):
                st.markdown(results["movie_insight"])
        
        # Artist insights
        if results.get("artist_insight"):
            with st.expander("🎵 **Music & Artists**", expanded=False):
                st.markdown(results["artist_insight"])
        
        # Podcast insights
        if results.get("podcast_insight"):
            with st.expander("🎧 **Podcast Preferences**", expanded=False):
                st.markdown(results["podcast_insight"])
        
        # Tag insights
        if results.get("tag_insight"):
            with st.expander("🏷️ **Cultural Tags**", expanded=False):
                st.markdown(results["tag_insight"])
        
        st.markdown('</div>', unsafe_allow_html=True)

def render_customization_results():
    """Render customization results with enhanced error handling"""
    results = st.session_state.customization_results
    
    if not results:
        return
    
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    
    # Check for errors first
    if results.get("error"):
        st.markdown("### ❌ Customization Failed")
        
        st.markdown(f'<div class="error-callout">{results["error"]}</div>', unsafe_allow_html=True)
        
        if results.get("suggestions"):
            st.markdown("#### 💡 Suggestions to fix this:")
            for suggestion in results["suggestions"]:
                st.markdown(f"• {suggestion}")
        
        # Helpful links
        st.markdown("#### 🔗 Quick Actions")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎯 Run Product Analysis", use_container_width=True):
                st.session_state.current_page = "recommendation"
                st.rerun()
        
        with col2:
            if st.button("🔄 Try Different Product", use_container_width=True):
                st.session_state.customization_results = {}
                st.rerun()
    
    else:
        # Success case
        st.markdown("### ✅ Customization Successful")
        
        # Before and After comparison
        if results.get('original_product') and results.get('customized_image_url'):
            col1, col2 = st.columns(2)
            
            # Original product
            with col1:
                st.markdown("#### 📦 Original Product")
                original = results['original_product']
                
                if original.get('image_url'):
                    st.image(original['image_url'], use_container_width=True)
                
                st.markdown(f"**{original.get('name', 'Unknown Product')}**")
                st.markdown(f"Product ID: `{original.get('product_id', 'N/A')}`")
                st.markdown(f"💰 ${original.get('price', 0)}")
                
                if original.get('description'):
                    st.caption(original['description'])
            
            # Customized product
            with col2:
                st.markdown("#### ✨ Customized Version")
                
                st.image(results['customized_image_url'], use_container_width=True)
                st.markdown("🎯 **Culturally Optimized**")
                st.caption("Designed for your target audience")
                
                # Success indicator
                st.markdown(f'<div class="success-callout">🎉 Successfully customized for persona: <strong>{st.session_state.results.get("persona_name", "Unknown")}</strong></div>', unsafe_allow_html=True)
        
        # Customization reasoning
        if results.get('customization_reasoning'):
            st.markdown("---")
            st.markdown("### 🧠 Customization Reasoning")
            st.markdown(results['customization_reasoning'])
        
        # Action buttons
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🎨 Customize Another Product", use_container_width=True):
                st.session_state.customization_results = {}
                st.rerun()
        
        with col2:
            if st.button("🛍️ View All Products", use_container_width=True):
                st.session_state.current_page = "recommendation"
                st.rerun()
        
        with col3:
            if st.button("🏠 Back to Home", use_container_width=True):
                st.session_state.current_page = "home"
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# PAGES
# ============================================================================

def home_page():
    """Home page with feature overview"""
    render_hero()
    
    st.markdown("### 🚀 What You Can Do")
    
    # Feature cards
    st.markdown('<div class="feature-grid">', unsafe_allow_html=True)
    
    # Feature 1 - Product Recommendation
    feature1_html = f'''
    <div class="feature-card">
        <div class="feature-icon">🎯</div>
        <div class="feature-title">Product Recommendation</div>
        <div class="feature-description">
            Get AI-powered product recommendations based on detailed audience analysis and cultural intelligence.
        </div>
    </div>
    '''
    
    # Feature 2 - Product Customization  
    feature2_html = f'''
    <div class="feature-card">
        <div class="feature-icon">🎨</div>
        <div class="feature-title">Product Customization</div>
        <div class="feature-description">
            Customize existing products based on cultural insights and audience preferences.
        </div>
    </div>
    '''
    
    # Feature 3 - Personalized Content
    feature3_html = f'''
    <div class="feature-card">
        <div class="feature-icon">📝</div>
        <div class="feature-title">Personalized Content Creation</div>
        <div class="feature-description">
            Generate AI-powered personalized Chelsea FC videos with custom scenes, audio, and visuals.
        </div>
    </div>
    '''
    
    st.markdown(feature1_html + feature2_html + feature3_html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Quick navigation buttons
    st.markdown("### 🚀 Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎯 Start Product Recommendation", type="primary", use_container_width=True):
            st.session_state.current_page = "recommendation"
            st.rerun()
    
    with col2:
        if st.button("🎨 Customize Products", use_container_width=True):
            st.session_state.current_page = "customization"
            st.rerun()
    
    with col3:
        if st.button("📝 Create Personalized Video", use_container_width=True):
            st.session_state.current_page = "content"
            st.rerun()

def recommendation_page():
    """Product recommendation page with real-time updates"""
    st.markdown("# 🎯 Product Recommendation")
    st.markdown("Get AI-powered product recommendations based on audience analysis")
    
    # Analysis interface
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown("### 🎯 Audience Analysis")
    
    # Input field (full width)
    query = st.text_area(
        "Describe your target audience:",
        placeholder="e.g., Young Chelsea fans in London aged 25-35 who love technology and fashion",
        height=120,
        key="audience_query"
    )
    
    # Centered button
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.session_state.agent_running:
            st.markdown('''
            <div style="text-align: center; padding: 10px;">
                <div class="loading-animation"></div>
                <p style="margin-top: 10px; color: #64748b; font-size: 0.9rem;">Analysis Running...</p>
            </div>
            ''', unsafe_allow_html=True)
        else:
            if st.button("🚀 Analyze", type="primary", use_container_width=True):
                if query.strip():
                    # Initialize analysis
                    st.session_state.query_to_run = query
                    st.session_state.agent_running = True
                    st.session_state.results = {}
                    st.session_state.step_status = {}
                    st.session_state.analysis_started = True
                    st.session_state.current_step = 0
                    
                    # Initialize step tracking
                    analysis_steps = [
                        "🔍 Detecting demographic signals...",
                        "👥 Finding target audiences...",
                        "🧠 Generating cultural insights...",
                        "👤 Creating consumer persona...",
                        "🛍️ Finding perfect products...",
                        "✅ Analysis complete!"
                    ]
                    
                    for step in analysis_steps:
                        st.session_state.step_status[step] = "pending"
                    
                    st.rerun()
                else:
                    st.error("Please enter an audience description!")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Start analysis after button click
    if st.session_state.get('analysis_started', False) and st.session_state.agent_running:
        st.session_state.analysis_started = False
        
        # Create progress containers
        st.markdown("### 📊 Analysis Progress")
        progress_container = st.empty()
        
        # Run analysis with real-time updates
        run_agent_query_with_progress(st.session_state.query_to_run, progress_container)
    
    # Show results if available and analysis complete
    if st.session_state.results and not st.session_state.agent_running:
        render_analysis_results()
        render_cultural_insights()


def run_agent_query_with_progress(query: str, progress_container):
    """Run agent query with live progress updates"""
    if not connect_to_agent_engine():
        st.session_state.agent_running = False
        st.error("Failed to connect to Agent Engine")
        return
    
    analysis_steps = [
        "🔍 Detecting demographic signals...",
        "👥 Finding target audiences...",
        "🧠 Generating cultural insights...",
        "👤 Creating consumer persona...",
        "🛍️ Finding perfect products...",
        "✅ Analysis complete!"
    ]
    
    try:
        # Track current step
        current_step_idx = 0
        full_state = {}
        
        # Initial progress display
        with progress_container.container():
            render_real_time_progress(full_state)
        
        # Stream the query
        for event in st.session_state.agent_app.stream_query(
            user_id=st.session_state.user_id,
            session_id=st.session_state.agent_session["id"],
            message=query
        ):
            # Process state changes from the agent
            if "state_delta" in event.get("actions", {}):
                state_delta = event["actions"]["state_delta"]
                if state_delta:
                    # Update our full state with new data
                    for key, value in state_delta.items():
                        full_state[key] = value
                    
                    # Save to session state
                    st.session_state.results = full_state
                    
                    # Update step progress
                    for step_idx, step_name in enumerate(analysis_steps):
                        if check_step_completion(step_idx, full_state):
                            st.session_state.step_status[step_name] = "completed"
                            current_step_idx = max(current_step_idx, step_idx + 1)
                        elif step_idx == current_step_idx:
                            st.session_state.step_status[step_name] = "running"
                    
                    # Refresh progress display
                    with progress_container.container():
                        render_real_time_progress(full_state)
        
        # Mark as complete
        st.session_state.step_status["✅ Analysis complete!"] = "completed"
        st.session_state.agent_running = False
        
        # Final progress update
        with progress_container.container():
            render_real_time_progress(full_state)
        
        # Clear progress container after a moment
        time.sleep(1)
        progress_container.empty()
        
        # Trigger rerun to show final results
        st.rerun()
        
    except Exception as e:
        st.session_state.agent_running = False
        progress_container.empty()
        st.error(f"Analysis failed: {e}")

def customization_page():
    """Product customization page with improved UX"""
    st.markdown("# 🎨 Product Customization")
    st.markdown("Customize products based on audience insights")
    
    # Check if we have prerequisite data
    if not st.session_state.results.get("recommendations"):
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown("### ⚠️ Prerequisites Required")
        st.info("💡 Please run a product recommendation analysis first to see customization options.")
        
        if st.button("🎯 Go to Product Recommendation", type="primary", use_container_width=True):
            st.session_state.current_page = "recommendation"
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    # Show available context
    persona_name = st.session_state.results.get("persona_name", "Unknown")
    audience_count = len(st.session_state.results.get("detected_audience_names", []))
    product_count = len(st.session_state.results.get("recommendations", []))
    
    st.markdown(f'<div class="success-callout">✅ <strong>Ready for customization!</strong><br>Persona: {persona_name} | Audiences: {audience_count} | Products: {product_count}</div>', unsafe_allow_html=True)
    
    # Customization interface
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown("### 🎨 Product Customization")
    
    # Get list of available product IDs for validation
    available_products = st.session_state.results.get("recommendations", [])
    available_product_ids = [p.get("product_id", "") for p in available_products]
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        # Product ID selector with helpful UI
        st.markdown("**Select Product to Customize:**")
        
        # Option 1: Dropdown selector
        if available_products:
            product_options = [f"{p.get('product_id', 'N/A')} - {p.get('name', 'Unknown')[:50]}..." for p in available_products]
            selected_option = st.selectbox(
                "Choose from your recommendations:",
                options=product_options,
                index=0,
                help="Select a product from your recommendation analysis"
            )
            
            # Extract product ID
            if selected_option:
                product_id = selected_option.split(" - ")[0]
            else:
                product_id = ""
        
        # Option 2: Manual entry (with validation)
        manual_product_id = st.text_input(
            "Or enter Product ID manually:",
            placeholder="e.g., prod_244",
            help="Enter the exact product ID you want to customize"
        )
        
        if manual_product_id.strip():
            product_id = manual_product_id.strip()
        
        # Validation
        if product_id and product_id not in available_product_ids:
            st.warning(f"⚠️ Product ID '{product_id}' not found in your recommendations. Available IDs: {', '.join(available_product_ids[:3])}{'...' if len(available_product_ids) > 3 else ''}")
        
        customization_prompt = st.text_area(
            "Customization instructions:",
            value="Customize the product to make it more appealing to the target audience",
            height=80,
            help="Describe how you want the product customized for your target persona"
        )
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Show customization status
        if st.session_state.customization_running:
            st.markdown(f'''
            <div style="text-align: center; padding: 20px;">
                <div class="loading-animation"></div>
                <p style="margin-top: 10px; color: #64748b; font-size: 0.9rem;">{st.session_state.customization_status}</p>
            </div>
            ''', unsafe_allow_html=True)
        else:
            # Customization button
            button_disabled = not product_id or not customization_prompt.strip()
            
            if st.button("🎨 Customize Product", 
                        type="primary", 
                        use_container_width=True,
                        disabled=button_disabled):
                
                if not product_id.strip():
                    st.error("Please select or enter a product ID!")
                elif not customization_prompt.strip():
                    st.error("Please enter customization instructions!")
                else:
                    st.session_state.customization_running = True
                    st.session_state.customization_results = {}
                    st.session_state.customization_status = "🚀 Starting customization..."
                    run_customization_query(product_id, customization_prompt)
                    st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Display customization results if available
    if st.session_state.customization_results:
        render_customization_results()
    
    # Show all available products for reference
    st.markdown("### 🛍️ Available Products for Customization")
    
    recommendations = st.session_state.results.get("recommendations", [])
    
    # Show all products in 3x2 grid
    for row in range(2):  # 2 rows
        cols = st.columns(3)  # 3 columns
        for col in range(3):
            product_idx = row * 3 + col
            if product_idx < len(recommendations):
                product = recommendations[product_idx]
                
                with cols[col]:
                    with st.container():
                        st.markdown('<div style="border: 1px solid #e2e8f0; border-radius: 12px; padding: 1rem; margin: 0.5rem 0; background: white;">', unsafe_allow_html=True)
                        
                        # Product image (smaller)
                        st.image(
                            product.get('image_url', 'https://via.placeholder.com/200/034694/FFFFFF?text=Product'), 
                            width=180
                        )
                        
                        # Product name
                        st.markdown(f"**{product.get('name', 'Unknown Product')}**")
                        
                        # Product ID (highlighted for easy copying)
                        product_id_display = product.get('product_id', 'N/A')
                        st.markdown(f'<p style="background: #f1f5f9; padding: 0.25rem 0.5rem; border-radius: 6px; font-family: monospace; font-size: 0.85rem; color: #034694; margin: 0.5rem 0;"><strong>{product_id_display}</strong></p>', 
                                   unsafe_allow_html=True)
                        
                        # Price and match
                        st.markdown(f"💰 ${product.get('price', 0)}")
                        if product.get('similarity'):
                            match_percent = int(product['similarity'] * 100)
                            st.markdown(f"🎯 {match_percent}% Match")
                        
                        st.markdown('</div>', unsafe_allow_html=True)

def about_page():
    """About page"""
    st.markdown("# ℹ️ About")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🚀 Technology Stack")
        st.markdown("- **Google Cloud Agent Engine** - Scalable AI deployment")
        st.markdown("- **Gemini 2.0 Flash** - Advanced language model with image generation")
        st.markdown("- **Qloo Cultural Intelligence** - Cultural insights platform") 
        st.markdown("- **Real-time Streaming** - Live analysis updates")
        st.markdown("- **Video Generation** - AI-powered content creation")
        st.markdown("- **MoviePy** - Video assembly and processing")
        st.markdown("- **Google Cloud Storage** - Asset storage and delivery")
        st.markdown("- **Streamlit** - Modern web interface")
    
    with col2:
        st.markdown("### 📊 Session Information")
        st.code(f"User ID: {st.session_state.user_id}")
        st.code(f"Session ID: {st.session_state.session_id}")
        
        # Product recommendation agent status
        if st.session_state.agent_app:
            st.success("✅ Product Recommendation Agent Connected")
        else:
            st.warning("⚠️ Product Recommendation Agent Disconnected")
        
        # Content creation agent status
        if st.session_state.content_agent_app:
            st.success("✅ Content Creation Agent Connected")
        else:
            st.warning("⚠️ Content Creation Agent Disconnected")
        
        # Reconnect button
        if st.button("🔄 Reconnect All Agents"):
            st.session_state.agent_app = None
            st.session_state.agent_session = None
            st.session_state.content_agent_app = None
            st.session_state.content_agent_session = None
            st.rerun()
        
        # Show current content creation status
        status = get_content_creation_status()
        if status["has_video"]:
            st.info("📹 Video available in Content Creation page")
        elif status["running"]:
            st.info("🎬 Video creation in progress...")
        elif status["has_results"]:
            st.info("📊 Content creation data available")

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application logic"""
    initialize_session_state()
    
    # Navigation
    render_navigation()
    
    # Route to pages
    if st.session_state.current_page == "home":
        home_page()
    elif st.session_state.current_page == "recommendation":
        recommendation_page()
    elif st.session_state.current_page == "customization":
        customization_page()
    elif st.session_state.current_page == "content":
        content_creation_page()
    elif st.session_state.current_page == "about":
        about_page()

if __name__ == "__main__":
    main()
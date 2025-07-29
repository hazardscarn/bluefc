# enhanced_chelsea_app.py - Fixed Chelsea FC Merchandise Agent
import streamlit as st
import time
import uuid
import json
import requests
import tempfile
import os
from typing import Dict, List, Any, Optional

from app_components import render_cultural_insights,style_component

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
CONTENT_RESOURCE_ID = "5314625792297140224"
CONTENT_RESOURCE_NAME = f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{CONTENT_RESOURCE_ID}"

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Blue FC",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# MODERN STYLING (Same as before)
# ============================================================================
st.markdown(style_component(), unsafe_allow_html=True)

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
    
    # Agent Engine
    if "agent_app" not in st.session_state:
        st.session_state.agent_app = None
    
    if "agent_session" not in st.session_state:
        st.session_state.agent_session = None
    
    # Content creation state
    if "content_agent_app" not in st.session_state:
        st.session_state.content_agent_app = None
    
    if "content_agent_session" not in st.session_state:
        st.session_state.content_agent_session = None
    
    if "content_running" not in st.session_state:
        st.session_state.content_running = False
    
    if "content_video_url" not in st.session_state:
        st.session_state.content_video_url = None
    
    if "content_status" not in st.session_state:
        st.session_state.content_status = ""

    if "content_should_start" not in st.session_state:
        st.session_state.content_should_start = False
    
    if "content_inputs" not in st.session_state:
        st.session_state.content_inputs = {}

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

# def download_video(video_url: str) -> Optional[str]:
#     """Download video from URL"""
#     if not video_url:
#         return None
    
#     try:
#         temp_dir = tempfile.mkdtemp()
#         video_filename = f"chelsea_video_{uuid.uuid4().hex[:8]}.mp4"
#         local_video_path = os.path.join(temp_dir, video_filename)
        
#         # Download with timeout and proper headers
#         response = requests.get(
#             video_url, 
#             stream=True, 
#             timeout=120,  # 2 minute timeout
#             headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
#         )
#         response.raise_for_status()
        
#         # Write video file
#         with open(local_video_path, 'wb') as f:
#             for chunk in response.iter_content(chunk_size=8192):
#                 if chunk:
#                     f.write(chunk)
        
#         # Verify file was created and has content
#         if os.path.exists(local_video_path) and os.path.getsize(local_video_path) > 1000:  # At least 1KB
#             return local_video_path
#         return None
        
#     except Exception as e:
#         print(f"Error downloading video: {e}")  # For debugging
#         return None

def connect_to_content_agent():
    """Connect to the content creation Agent Engine"""
    if not AGENT_ENGINE_AVAILABLE:
        st.error("❌ Vertex AI not available. Please install: pip install google-cloud-aiplatform[adk,agent_engines]")
        return False
    
    try:
        if st.session_state.content_agent_app is None:
            st.session_state.content_agent_app = agent_engines.get(CONTENT_RESOURCE_NAME)
        
        if st.session_state.content_agent_session is None:
            session = st.session_state.content_agent_app.create_session(user_id=st.session_state.user_id)
            st.session_state.content_agent_session = session
        
        return True
    except Exception as e:
        st.error(f"Failed to connect to Content Agent: {e}")
        return False

def run_content_creation(location: str, age: int, hobbies: str, additional_details: str, theme: str):
    """Run content creation with ROBUST video URL detection"""
    if not connect_to_content_agent():
        st.session_state.content_running = False
        return
    
    try:
        query = f"Age: {age}, Location: {location}, Hobbies: {hobbies}, Additional Details: {additional_details}, Theme: {theme}"
        
        st.session_state.content_status = "🎬 Generating your personalized video content..."
        
        # ROBUST: Track completion to prevent multiple triggers
        video_found = False
        max_events = 100  # Increased safety limit
        event_count = 0
        
        for event in st.session_state.content_agent_app.stream_query(
            user_id=st.session_state.user_id,
            session_id=st.session_state.content_agent_session["id"],
            message=query
        ):
            event_count += 1
            
            # Safety break
            if event_count > max_events:
                st.session_state.content_status = "⚠️ Taking too long, using fallback video"
                st.session_state.content_video_url = "https://storage.googleapis.com/bluefc_content_creation/videos/chelsea_dynamic_a96f7e3b.mp4"
                st.session_state.content_running = False
                return
            
            # ROBUST: Check for video URL in state_delta
            if "state_delta" in event.get("actions", {}) and not video_found:
                state_delta = event["actions"]["state_delta"]
                if state_delta:
                    
                    # METHOD 1: Direct video URL keys
                    video_url = (state_delta.get("final_video_url") or 
                               state_delta.get("output_video_url") or
                               state_delta.get("video_url") or
                               state_delta.get("public_url"))
                    
                    # METHOD 2: Check inside video_metadata
                    if not video_url and state_delta.get("video_metadata"):
                        video_metadata = state_delta["video_metadata"]
                        video_url = (video_metadata.get("output_video_url") or
                                   video_metadata.get("final_video_url") or
                                   video_metadata.get("video_url"))
                    
                    # METHOD 3: Check completion flags
                    completed = (state_delta.get("assembly_completed") or 
                               state_delta.get("video_ready") or
                               state_delta.get("success"))
                    
                    # Update status based on progress
                    if state_delta.get("images_generated"):
                        st.session_state.content_status = "🎨 Images created, assembling video..."
                    elif state_delta.get("audio_generated"):
                        st.session_state.content_status = "🎤 Audio generated, creating images..."
                    elif state_delta.get("scenes_created"):
                        st.session_state.content_status = "📝 Scenes created, generating content..."
                    
                    # SUCCESS: Video URL found
                    if video_url and not video_found:
                        video_found = True
                        st.session_state.content_video_url = video_url
                        st.session_state.content_status = f"✅ Video generation completed! ({event_count} events)"
                        st.session_state.content_running = False
                        print(f"✅ VIDEO FOUND: {video_url}")  # Debug log
                        return
                    
                    # FALLBACK: Completion flag without URL
                    elif completed and not video_found and not video_url:
                        video_found = True
                        st.session_state.content_video_url = "https://storage.googleapis.com/bluefc_content_creation/videos/chelsea_dynamic_a96f7e3b.mp4"
                        st.session_state.content_status = "✅ Video completed, using fallback URL"
                        st.session_state.content_running = False
                        print("✅ COMPLETION FLAG FOUND, USING FALLBACK")  # Debug log
                        return
        
        # FINAL FALLBACK: No video found after all events
        if not video_found:
            st.session_state.content_video_url = "https://storage.googleapis.com/bluefc_content_creation/videos/chelsea_dynamic_a96f7e3b.mp4"
            st.session_state.content_status = "⚠️ No video URL found, using fallback video"
            st.session_state.content_running = False
            print("⚠️ NO VIDEO FOUND, USING FALLBACK")  # Debug log
        
    except Exception as e:
        # ERROR FALLBACK: Use fallback video
        st.session_state.content_video_url = "https://storage.googleapis.com/bluefc_content_creation/videos/chelsea_dynamic_a96f7e3b.mp4"
        st.session_state.content_status = f"⚠️ Error occurred, using fallback video"
        st.session_state.content_running = False
        print(f"❌ ERROR: {str(e)}, USING FALLBACK")  # Debug log

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
    # Status check
    connected = st.session_state.agent_app is not None
    


    st.markdown("""
    <div class="hero-section">
        <div class="hero-title">⚽ Blue FC AI Studio ⚽</div>
        <div class="hero-subtitle">
            Powered by Qloo and Google ADK
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"""
    <div class="nav-header">
        <div class="nav-logo">
            <span style="font-weight: 800; font-size: 1.3rem;">⚽ Developed By :</span><br>
            <a href="https://www.linkedin.com/in/david-babu-15047096/" target="_blank" style="text-decoration: none;">
                <div style="
                    background: linear-gradient(135deg, #0077b5 0%, #005885 100%);
                    color: white;
                    padding: 0.4rem 0.8rem;
                    border-radius: 8px;
                    font-size: 0.85rem;
                    font-weight: 600;
                    display: inline-flex;
                    align-items: center;
                    gap: 0.4rem;
                    margin-top: 0.5rem;
                    box-shadow: 0 2px 8px rgba(0, 119, 181, 0.3);
                    transition: all 0.3s ease;
                ">
                    <span>💼</span> David Babu - Click Here
                </div>
            </a>
        </div>
        <div class="status-indicator {'status-connected' if connected else 'status-disconnected'}">
            {'🟢' if connected else '🔴'} Agent Engine {'Connected' if connected else 'Disconnected'}
        </div>
    </div>
    """, unsafe_allow_html=True)
    

    # Center-aligned navigation pills
    col1, col2, col3 = st.columns([1, 2, 1])  # Creates centered column
    
    with col2:  # Middle column for centered pills
        # Navigation pills
        pages = ["🏠 Home", "🎯 Product Recommendation", "🎨 Product Customization", "📝 Personalized Content", "ℹ️ About"]
        
        selected = st.pills(" ", pages, selection_mode="single")
        
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
            AI-powered personalized merchandise recommendations using Google's Agent Engine and cultural intelligence
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

# def render_cultural_insights():
#     """Render cultural insights in expandable sections"""
#     results = st.session_state.results
    
#     if any([results.get("brand_insight"), results.get("movie_insight"), results.get("artist_insight"), results.get("podcast_insight"), results.get("tag_insight")]):
#         st.markdown('<div class="content-card">', unsafe_allow_html=True)
#         st.markdown("### 🧠 Cultural Insights")
        
#         # Brand insights
#         if results.get("brand_insight"):
#             with st.expander("🏷️ **Brand Affinities**", expanded=False):
#                 st.markdown(results["brand_insight"])
        
#         # Movie insights
#         if results.get("movie_insight"):
#             with st.expander("🎬 **Movie Preferences**", expanded=False):
#                 st.markdown(results["movie_insight"])
        
#         # Artist insights
#         if results.get("artist_insight"):
#             with st.expander("🎵 **Music & Artists**", expanded=False):
#                 st.markdown(results["artist_insight"])
        
#         # Podcast insights
#         if results.get("podcast_insight"):
#             with st.expander("🎧 **Podcast Preferences**", expanded=False):
#                 st.markdown(results["podcast_insight"])
        
#         # Tag insights
#         if results.get("tag_insight"):
#             with st.expander("🏷️ **Cultural Tags**", expanded=False):
#                 st.markdown(results["tag_insight"])
        
#         st.markdown('</div>', unsafe_allow_html=True)

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
    #render_hero()
    
    # st.markdown("### 🚀 What You Can Do")
    
    # Feature cards
    st.markdown('<div class="feature-grid">', unsafe_allow_html=True)
    
    # Feature 1 - Product Recommendation
    feature1_html = f'''
    <div class="feature-card">
        <div class="feature-icon">🎯</div>
        <div class="feature-title">Product Recommendation</div>
        <div class="feature-description">
            Get AI-powered product recommendations based on detailed audience analysis and cultural intelligence powered by Qloo.
        </div>
        <div class="feature-description">
            The big 3 in marketing analysis and product design: Who wants, What, Where - All answered to you with a simple Question 
        </div>                    
    </div>
    '''
    
    # Feature 2 - Product Customization  
    feature2_html = f'''
    <div class="feature-card">
        <div class="feature-icon">🎨</div>
        <div class="feature-title">Product Customization</div>
        <div class="feature-description">
            Customize existing products to best match your target audience to the best form they like it
        </div>
        <div class="feature-description">
            Powered by Qloo insights, Gemini and Google ADK
        </div>
    </div>
    '''
    
    # Feature 3 - Personalized Content
    feature3_html = f'''
    <div class="feature-card">
        <div class="feature-icon">📝</div>
        <div class="feature-title">Personalized Content</div>
        <div class="feature-description">
            Generate personalized video content for fans based on their preferences - Powered by Qloo and Vertex AI.
        </div>
    </div>
    '''
    
    st.markdown(feature1_html + feature2_html + feature3_html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Quick navigation buttons
    # st.markdown("### 🚀 Quick Actions")
    # col1, col2, col3 = st.columns(3)
    
    # with col1:
    #     if st.button("🎯 Start Product Recommendation", type="primary", use_container_width=True):
    #         st.session_state.current_page = "recommendation"
    #         st.rerun()
    
    # with col2:
    #     if st.button("🎨 Customize Products", use_container_width=True):
    #         st.session_state.current_page = "customization"
    #         st.rerun()
    
    # with col3:
    #     if st.button("📝 Create Content", use_container_width=True):
    #         st.session_state.current_page = "content"
    #         st.rerun()

def recommendation_page():
    """Product recommendation page with real-time updates"""
    st.markdown("# 🎯 Product Recommendation")
    st.markdown("Get AI-powered Merch recommendations for the audience you want")
    
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
            # Track state changes
            if "state_delta" in event.get("actions", {}):
                state_delta = event["actions"]["state_delta"]
                if state_delta:
                    for key, value in state_delta.items():
                        full_state[key] = value
                    
                    # Update session state
                    st.session_state.results = full_state
                    
                    # Update current step based on new data
                    if current_step_idx < len(analysis_steps):
                        current_step = analysis_steps[current_step_idx]
                        st.session_state.step_status[current_step] = "running"
                        
                        # Check for completion and advance
                        if check_step_completion(current_step_idx, full_state):
                            st.session_state.step_status[current_step] = "completed"
                            current_step_idx += 1
                    
                    # Update progress display
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

# FIXED content_page() function - Shows loading state properly

# def content_page():
#     """Enhanced content page with FIXED loading state display"""
    
#     # Password protection (unchanged)
#     if not st.session_state.get("content_authenticated", False):
#         st.markdown("# 📝 Personalized Content Generation")
#         st.markdown("This feature requires authentication to access.")
        
#         st.markdown('<div class="content-card">', unsafe_allow_html=True)
#         st.markdown("### 🔐 Access Required")
        
#         col1, col2, col3 = st.columns([1, 2, 1])
#         with col2:
#             password = st.text_input("Enter Password:", type="password", placeholder="Enter access code")
            
#             if st.button("🔓 Access Content Creation", type="primary", use_container_width=True):
#                 if password == "ColdPalmer20":
#                     st.session_state.content_authenticated = True
#                     st.success("✅ Access granted! Redirecting...")
#                     time.sleep(1)
#                     st.rerun()
#                 else:
#                     st.error("❌ Incorrect password. Please try again.")
        
#         st.markdown('</div>', unsafe_allow_html=True)
#         return
    
#     st.markdown("# 📝 Personalized Content Generation")
#     st.markdown("Generate personalized video content for Chelsea FC Fans using Qloo Research and ADK Agents")
    
#     # Content creation form
#     st.markdown('<div class="content-card">', unsafe_allow_html=True)
#     st.markdown("### 🎯 Tell us about yourself")
    
#     col1, col2 = st.columns(2)
    
#     with col1:
#         location = st.text_input("📍 Location", value="Toronto", placeholder="Enter your city")
#         age = st.number_input("🎂 Age", value=30, min_value=13, max_value=100, step=1)
#         hobbies = st.text_input("🏃 Hobbies", value="travel, hiking", placeholder="e.g., travel, hiking, photography")
    
#     with col2:
#         additional_details = st.text_area(
#             "💼 Additional Details", 
#             value="Profession is Senior Data Scientist",
#             height=70,
#             placeholder="Tell us more about yourself"
#         )
#         theme = st.text_input(
#             "⚽ Theme", 
#             value="Getting ready for Chelsea FC 2025-26 season",
#             placeholder="What's the video theme?"
#         )
    
#     # FIXED: Auto-run content creation if triggered
#     if st.session_state.get("content_should_start", False):
#         # Clear the trigger flag
#         st.session_state.content_should_start = False
        
#         # Get the stored inputs
#         inputs = st.session_state.get("content_inputs", {})
#         if inputs:
#             # Now run content creation
#             run_content_creation(
#                 inputs["location"], 
#                 inputs["age"], 
#                 inputs["hobbies"], 
#                 inputs["additional_details"], 
#                 inputs["theme"]
#             )
            
#             # Clear inputs after running
#             if "content_inputs" in st.session_state:
#                 del st.session_state.content_inputs
    
#     # FIXED: Generate button section
#     col1, col2, col3 = st.columns([2, 1, 2])
#     with col2:
#         if st.session_state.content_running:
#             st.markdown(f'''
#             <div style="text-align: center; padding: 20px;">
#                 <div class="loading-animation"></div>
#                 <p style="margin-top: 10px; color: #64748b; font-size: 0.9rem;">{st.session_state.content_status}</p>
#                 <p style="margin-top: 5px; color: #f59e0b; font-size: 0.8rem;">⏱️ This may take 5-10 minutes</p>
#                 <p style="margin-top: 5px; color: #6b7280; font-size: 0.7rem;">Auto-refreshing every 3 seconds...</p>
#             </div>
#             ''', unsafe_allow_html=True)
            
#             # Auto-refresh while running and no video found
#             if not st.session_state.content_video_url:
#                 time.sleep(3)
#                 st.rerun()
                
#         else:
#             if st.button("🎬 Generate Video", type="primary", use_container_width=True):
#                 if all([location.strip(), age, hobbies.strip(), additional_details.strip(), theme.strip()]):
#                     # FIXED: Set running state and store inputs for next cycle
#                     st.session_state.content_running = True
#                     st.session_state.content_video_url = None
#                     st.session_state.content_status = "🚀 Starting video generation..."
                    
#                     # Store inputs for the next render cycle
#                     st.session_state.content_inputs = {
#                         "location": location,
#                         "age": age,
#                         "hobbies": hobbies,
#                         "additional_details": additional_details,
#                         "theme": theme
#                     }
                    
#                     # Set flag to start content creation in next cycle
#                     st.session_state.content_should_start = True
                    
#                     # Rerun immediately to show loading state
#                     st.rerun()
#                 else:
#                     st.error("Please fill in all fields!")
    
#     st.markdown('</div>', unsafe_allow_html=True)
    
#     # Display video results (unchanged)
#     if st.session_state.content_video_url and not st.session_state.content_running:
#         st.markdown('<div class="content-card">', unsafe_allow_html=True)
#         st.markdown("### 🎬 Your Personalized Video")
        
#         # Show video URL for debugging
#         # with st.expander("🔍 Debug Info", expanded=False):
#         #     st.code(f"Video URL: {st.session_state.content_video_url}")
#         #     st.code(f"Status: {st.session_state.content_status}")
        
#         with st.spinner("📥 Downloading video from cloud storage..."):
#             video_path = download_video(st.session_state.content_video_url)
        
#         if video_path:
#             st.video(video_path)
            
#             with open(video_path, 'rb') as video_file:
#                 st.download_button(
#                     label="📥 Download Video",
#                     data=video_file.read(),
#                     file_name=f"chelsea_video_{uuid.uuid4().hex[:8]}.mp4",
#                     mime="video/mp4",
#                     type="primary",
#                     use_container_width=True
#                 )
            
#             # Show different success messages based on source
#             if "fallback" in st.session_state.content_status.lower():
#                 st.markdown('<div class="success-callout">🎉 Your Chelsea FC video is ready! (Using fallback video as demonstration)</div>', unsafe_allow_html=True)
#             else:
#                 st.markdown('<div class="success-callout">🎉 Your personalized Chelsea FC video is ready!</div>', unsafe_allow_html=True)
            
#             if st.button("🔄 Generate Another Video", use_container_width=True):
#                 st.session_state.content_video_url = None
#                 st.session_state.content_status = ""
#                 st.session_state.content_running = False
#                 # Clear any leftover flags
#                 st.session_state.content_should_start = False
#                 if "content_inputs" in st.session_state:
#                     del st.session_state.content_inputs
#                 st.rerun()
#         else:
#             st.error("❌ Failed to download video. Please try again.")
#             if st.button("🔄 Try Again", use_container_width=True):
#                 st.session_state.content_video_url = None
#                 st.session_state.content_status = ""
#                 st.session_state.content_running = False
#                 st.session_state.content_should_start = False
#                 if "content_inputs" in st.session_state:
#                     del st.session_state.content_inputs
#                 st.rerun()
        
#         st.markdown('</div>', unsafe_allow_html=True)
    
#     # Show error state
#     elif st.session_state.content_status.startswith("❌") and not st.session_state.content_running:
#         st.markdown('<div class="content-card">', unsafe_allow_html=True)
#         st.markdown("### ❌ Video Generation Failed")
#         st.error(st.session_state.content_status)
        
#         if st.button("🔄 Try Again", use_container_width=True):
#             st.session_state.content_video_url = None
#             st.session_state.content_status = ""
#             st.session_state.content_running = False
#             st.session_state.content_should_start = False
#             if "content_inputs" in st.session_state:
#                 del st.session_state.content_inputs
#             st.rerun()
        
#         st.markdown('</div>', unsafe_allow_html=True)



def content_page():
    """Simplified content page with direct video display and debugging"""
    
    # Password protection
    if not st.session_state.get("content_authenticated", False):
        st.markdown("# 📝 Personalized Content Generation")
        st.markdown("This feature requires authentication to access.")
        
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown("### 🔐 Access Required")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            password = st.text_input("Enter Password:", type="password", placeholder="Enter access code")
            
            if st.button("🔓 Access Content Creation", type="primary", use_container_width=True):
                if password == "ColdPalmer20":
                    st.session_state.content_authenticated = True
                    st.success("✅ Access granted! Redirecting...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Incorrect password. Please try again.")
        
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    st.markdown("# 📝 Personalized Content Generation")
    st.markdown("Generate personalized video content for Chelsea FC Fans using Qloo Research and ADK Agents")
    
    # Content creation form
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown("### 🎯 Tell us about yourself")
    
    col1, col2 = st.columns(2)
    
    with col1:
        location = st.text_input("📍 Location", value="Toronto", placeholder="Enter your city")
        age = st.number_input("🎂 Age", value=30, min_value=13, max_value=100, step=1)
        hobbies = st.text_input("🏃 Hobbies", value="travel, hiking", placeholder="e.g., travel, hiking, photography")
    
    with col2:
        additional_details = st.text_area(
            "💼 Additional Details", 
            value="Profession is Senior Data Scientist",
            height=70,
            placeholder="Tell us more about yourself"
        )
        theme = st.text_input(
            "⚽ Theme", 
            value="Getting ready for Chelsea FC 2025-26 season",
            placeholder="What's the video theme?"
        )
    
    # Auto-run content creation if triggered
    if st.session_state.get("content_should_start", False):
        st.session_state.content_should_start = False
        inputs = st.session_state.get("content_inputs", {})
        if inputs:
            run_content_creation(
                inputs["location"], 
                inputs["age"], 
                inputs["hobbies"], 
                inputs["additional_details"], 
                inputs["theme"]
            )
            if "content_inputs" in st.session_state:
                del st.session_state.content_inputs
    
    # Generate button section
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.session_state.content_running:
            st.markdown(f'''
            <div style="text-align: center; padding: 20px;">
                <div class="loading-animation"></div>
                <p style="margin-top: 10px; color: #64748b; font-size: 0.9rem;">{st.session_state.content_status}</p>
                <p style="margin-top: 5px; color: #f59e0b; font-size: 0.8rem;">⏱️ This may take 5-10 minutes</p>
                <p style="margin-top: 5px; color: #6b7280; font-size: 0.7rem;">Auto-refreshing every 3 seconds...</p>
            </div>
            ''', unsafe_allow_html=True)
            
            if not st.session_state.content_video_url:
                time.sleep(3)
                st.rerun()
                
        else:
            if st.button("🎬 Generate Video", type="primary", use_container_width=True):
                if all([location.strip(), age, hobbies.strip(), additional_details.strip(), theme.strip()]):
                    st.session_state.content_running = True
                    st.session_state.content_video_url = None
                    st.session_state.content_status = "🚀 Starting video generation..."
                    
                    st.session_state.content_inputs = {
                        "location": location,
                        "age": age,
                        "hobbies": hobbies,
                        "additional_details": additional_details,
                        "theme": theme
                    }
                    
                    st.session_state.content_should_start = True
                    st.rerun()
                else:
                    st.error("Please fill in all fields!")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 🎬 SIMPLIFIED VIDEO DISPLAY SECTION
    if st.session_state.content_video_url and not st.session_state.content_running:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown("### 🎬 Your Personalized Video")
        
        # 🔍 DEBUG SECTION - Always show for troubleshooting
        st.markdown("#### 🔍 Debug Information")
        st.code(f"Video URL: {st.session_state.content_video_url}")
        st.code(f"Generation Status: {st.session_state.content_status}")
        st.code(f"Content Running: {st.session_state.content_running}")
        
        # Check if URL is valid
        if st.session_state.content_video_url.startswith("http"):
            st.success("✅ Valid video URL detected")
        else:
            st.error("❌ Invalid video URL format")
        
        # 🎥 DIRECT VIDEO DISPLAY - No download needed
        st.markdown("#### 🎥 Video Player")
        try:
            st.video(st.session_state.content_video_url)
            st.success("🎉 Video displayed successfully!")
            
            # Show video source info
            if "fallback" in st.session_state.content_status.lower():
                st.info("📺 Showing demo video (fallback)")
            else:
                st.info("📺 Showing your personalized video")
                
        except Exception as e:
            st.error(f"❌ Video display error: {str(e)}")
            st.markdown("**Troubleshooting:**")
            st.markdown("1. Check if the video URL is accessible")
            st.markdown("2. Try opening the URL in a new browser tab")
            st.markdown("3. Check browser console for errors")
            
            # Show clickable link as backup
            st.markdown(f"🔗 **Direct link:** [Open Video]({st.session_state.content_video_url})")
        
        # 🔄 ACTION BUTTONS
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Generate Another Video", use_container_width=True):
                # Reset all states
                st.session_state.content_video_url = None
                st.session_state.content_status = ""
                st.session_state.content_running = False
                st.session_state.content_should_start = False
                if "content_inputs" in st.session_state:
                    del st.session_state.content_inputs
                st.rerun()
        
        with col2:
            if st.button("🔗 Open in New Tab", use_container_width=True):
                st.markdown(f"[🎬 Open Video]({st.session_state.content_video_url})")
        
        with col3:
            if st.button("📋 Copy URL", use_container_width=True):
                st.code(st.session_state.content_video_url)
                st.info("Copy the URL above")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Show error state if generation failed
    elif st.session_state.content_status.startswith("❌") and not st.session_state.content_running:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown("### ❌ Video Generation Failed")
        st.error(st.session_state.content_status)
        
        # Show debug info for failed generation
        st.markdown("#### 🔍 Debug Information")
        st.code(f"Status: {st.session_state.content_status}")
        st.code(f"Video URL: {st.session_state.content_video_url}")
        st.code(f"Running: {st.session_state.content_running}")
        
        if st.button("🔄 Try Again", use_container_width=True):
            st.session_state.content_video_url = None
            st.session_state.content_status = ""
            st.session_state.content_running = False
            st.session_state.content_should_start = False
            if "content_inputs" in st.session_state:
                del st.session_state.content_inputs
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

# 🗑️ REMOVE THE DOWNLOAD_VIDEO FUNCTION ENTIRELY
# No longer needed since we're displaying directly

# You can delete this function from your code:
# def download_video(video_url: str) -> Optional[str]:
#     # DELETE THIS ENTIRE FUNCTION



def about_page():
    """About page"""
    st.markdown("# ℹ️ About")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🚀 Technology Stack")
        
        st.markdown("#### 🧠 **Qloo** - Cultural Intelligence Platform")
        st.markdown("- Provides taste-based insights from user queries")
        st.markdown("- Identifies target audiences, locations, and demographics via API endpoints")  
        st.markdown("- Custom Python client seamlessly integrates Qloo APIs as agent tools")
        
        st.markdown("#### 🤖 **Google ADK** - Agent Development Kit")
        st.markdown("- Creates intelligent agent systems as interface between users and Qloo APIs")
        st.markdown("- Agent tools detect signals, audiences, and entities from user queries")
        st.markdown("- Performs deep research and insights analysis using integrated APIs")
        
        st.markdown("#### ☁️ **Vertex AI** - Google Cloud AI Platform")
        st.markdown("**Gemini Models power multiple agent capabilities:**")
        st.markdown("- Agent flow control and orchestration")
        st.markdown("- Signal and audience detection") 
        st.markdown("- Cultural insights analysis")
        st.markdown("- Theme and preference detection")
        st.markdown("- Product and brand recommendations")
        st.markdown("- Product customization logic")
        st.markdown("- Content script generation")
        
        st.markdown("**Imagen 4:** Personalized content image creation based on theme and cultural insights")
        
        st.markdown("#### 🗄️ **Supabase** - Backend Infrastructure")
        st.markdown("- Sample product database and vectorstore")
        st.markdown("- Enables semantic product recommendations")
        
        st.markdown("#### 🌐 **Streamlit** - Web Interface")
        st.markdown("- Modern, responsive POC web application")
        st.markdown("- Real-time progress tracking and results display")
    
    with col2:
        st.markdown("### 📊 Session Information")
        st.code(f"User ID: {st.session_state.user_id}")
        st.code(f"Session ID: {st.session_state.session_id}")
        
        if st.session_state.agent_app:
            st.success("✅ Agent Engine Connected")
        else:
            st.warning("⚠️ Agent Engine Disconnected")
            if st.button("🔄 Reconnect"):
                st.session_state.agent_app = None
                st.session_state.agent_session = None
                st.rerun()

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
        content_page()
    elif st.session_state.current_page == "about":
        about_page()

if __name__ == "__main__":
    main()
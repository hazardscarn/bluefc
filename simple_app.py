# enhanced_chelsea_app.py - Fixed Chelsea FC Merchandise Agent with Async Video Generation + Comprehensive Logging
import streamlit as st
import time
import uuid
import json
import requests
import tempfile
import os
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta
from app_components import render_cultural_insights,style_component

# Agent Engine imports
try:
    from vertexai import agent_engines
    AGENT_ENGINE_AVAILABLE = True
except ImportError:
    AGENT_ENGINE_AVAILABLE = False

# ============================================================================
# ENHANCED LOGGING CONFIGURATION
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)
logger.info("🚀 Starting Blue FC AI Studio application")

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

logger.info(f"📋 Configuration loaded - Project: {PROJECT_ID}, Location: {LOCATION}")
logger.info(f"🤖 Main Agent Resource: {RESOURCE_ID}")
logger.info(f"🎬 Content Agent Resource: {CONTENT_RESOURCE_ID}")

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Blue FC",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)
logger.info("📱 Streamlit page configuration set")

# ============================================================================
# MODERN STYLING (Same as before)
# ============================================================================
st.markdown(style_component(), unsafe_allow_html=True)
logger.debug("🎨 Style components loaded")

# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

def initialize_session_state():
    """Initialize all session state variables with comprehensive logging"""
    logger.info("🔧 Starting session state initialization")
    
    # Basic session info
    if "current_page" not in st.session_state:
        st.session_state.current_page = "home"
        logger.info("📄 Set default page to 'home'")
    
    if "user_id" not in st.session_state:
        st.session_state.user_id = f"user_{uuid.uuid4().hex[:8]}"
        logger.info(f"👤 Generated new user ID: {st.session_state.user_id}")
    
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"session_{uuid.uuid4().hex[:8]}"
        logger.info(f"🔐 Generated new session ID: {st.session_state.session_id}")
    
    # Analysis state
    if "agent_running" not in st.session_state:
        st.session_state.agent_running = False
        logger.debug("🎯 Initialized agent_running = False")
    
    if "analysis_started" not in st.session_state:
        st.session_state.analysis_started = False
        logger.debug("📊 Initialized analysis_started = False")
    
    if "results" not in st.session_state:
        st.session_state.results = {}
        logger.debug("📈 Initialized empty results dict")
    
    if "step_status" not in st.session_state:
        st.session_state.step_status = {}
        logger.debug("👣 Initialized empty step_status dict")
    
    if "query_to_run" not in st.session_state:
        st.session_state.query_to_run = None
        logger.debug("❓ Initialized query_to_run = None")
    
    if "analysis_events" not in st.session_state:
        st.session_state.analysis_events = []
        logger.debug("📋 Initialized empty analysis_events list")
    
    if "current_step" not in st.session_state:
        st.session_state.current_step = 0
        logger.debug("🚶 Initialized current_step = 0")
    
    # Customization state
    if "customization_running" not in st.session_state:
        st.session_state.customization_running = False
        logger.debug("🎨 Initialized customization_running = False")
    
    if "customization_results" not in st.session_state:
        st.session_state.customization_results = {}
        logger.debug("🖼️ Initialized empty customization_results dict")
    
    if "customization_status" not in st.session_state:
        st.session_state.customization_status = ""
        logger.debug("📱 Initialized empty customization_status")
    
    # Agent Engine connections
    if "agent_app" not in st.session_state:
        st.session_state.agent_app = None
        logger.debug("🤖 Initialized agent_app = None")
    
    if "agent_session" not in st.session_state:
        st.session_state.agent_session = None
        logger.debug("🔗 Initialized agent_session = None")
    
    # Content creation state - LEGACY (keeping for compatibility)
    if "content_agent_app" not in st.session_state:
        st.session_state.content_agent_app = None
        logger.debug("🎬 Initialized content_agent_app = None")
    
    if "content_agent_session" not in st.session_state:
        st.session_state.content_agent_session = None
        logger.debug("🎥 Initialized content_agent_session = None")
    
    # NEW: Async video job management
    if "video_jobs" not in st.session_state:
        st.session_state.video_jobs = {}
        logger.info("📹 Initialized empty video_jobs dict for async processing")
    
    logger.info("✅ Session state initialization completed successfully")

# ============================================================================
# AGENT ENGINE MANAGER
# ============================================================================

def connect_to_agent_engine():
    """Connect to the deployed Agent Engine with detailed logging"""
    logger.info("🔌 Attempting to connect to main Agent Engine")
    
    if not AGENT_ENGINE_AVAILABLE:
        error_msg = "❌ Vertex AI not available. Please install: pip install google-cloud-aiplatform[adk,agent_engines]"
        logger.error(error_msg)
        st.error(error_msg)
        return False
    
    try:
        # Check if agent app needs initialization
        if st.session_state.agent_app is None:
            logger.info(f"🔗 Creating agent connection to: {RESOURCE_NAME}")
            st.session_state.agent_app = agent_engines.get(RESOURCE_NAME)
            logger.info("✅ Agent app created successfully")
        else:
            logger.debug("♻️ Using existing agent app connection")
        
        # Check if session needs initialization
        if st.session_state.agent_session is None:
            logger.info(f"🆕 Creating new agent session for user: {st.session_state.user_id}")
            session = st.session_state.agent_app.create_session(user_id=st.session_state.user_id)
            st.session_state.agent_session = session
            logger.info(f"✅ Agent session created: {session.get('id', 'unknown')}")
        else:
            logger.debug(f"♻️ Using existing agent session: {st.session_state.agent_session.get('id', 'unknown')}")
        
        logger.info("🟢 Agent Engine connection established successfully")
        return True
        
    except Exception as e:
        error_msg = f"Failed to connect to Agent Engine: {e}"
        logger.error(f"❌ {error_msg}", exc_info=True)
        st.error(error_msg)
        return False

def connect_to_content_agent():
    """Connect to the content creation Agent Engine with detailed logging"""
    logger.info("🔌 Attempting to connect to Content Agent Engine")
    
    if not AGENT_ENGINE_AVAILABLE:
        error_msg = "❌ Vertex AI not available. Please install: pip install google-cloud-aiplatform[adk,agent_engines]"
        logger.error(error_msg)
        st.error(error_msg)
        return False
    
    try:
        # Check if content agent app needs initialization
        if st.session_state.content_agent_app is None:
            logger.info(f"🔗 Creating content agent connection to: {CONTENT_RESOURCE_NAME}")
            st.session_state.content_agent_app = agent_engines.get(CONTENT_RESOURCE_NAME)
            logger.info("✅ Content agent app created successfully")
        else:
            logger.debug("♻️ Using existing content agent app connection")
        
        # Check if content session needs initialization
        if st.session_state.content_agent_session is None:
            logger.info(f"🆕 Creating new content agent session for user: {st.session_state.user_id}")
            session = st.session_state.content_agent_app.create_session(user_id=st.session_state.user_id)
            st.session_state.content_agent_session = session
            logger.info(f"✅ Content agent session created: {session.get('id', 'unknown')}")
        else:
            logger.debug(f"♻️ Using existing content agent session: {st.session_state.content_agent_session.get('id', 'unknown')}")
        
        logger.info("🟢 Content Agent Engine connection established successfully")
        return True
        
    except Exception as e:
        error_msg = f"Failed to connect to Content Agent: {e}"
        logger.error(f"❌ {error_msg}", exc_info=True)
        st.error(error_msg)
        return False

# ============================================================================
# NEW: ASYNC VIDEO GENERATION FUNCTIONS
# ============================================================================

def start_video_generation_async(location: str, age: int, hobbies: str, additional_details: str, theme: str):
    """Start video generation in background and return job info with detailed logging"""
    logger.info("🚀 Starting async video generation process")
    logger.info(f"📋 Input params - Location: {location}, Age: {age}, Hobbies: {hobbies}")
    logger.debug(f"📝 Additional details: {additional_details}")
    logger.debug(f"🎯 Theme: {theme}")
    
    if not connect_to_content_agent():
        logger.error("❌ Failed to connect to content agent, aborting video generation")
        return None
    
    # Create unique job ID
    job_id = f"video_job_{uuid.uuid4().hex[:8]}"
    logger.info(f"🆔 Generated job ID: {job_id}")
    
    # Store job info in session state
    job_data = {
        "status": "starting",
        "start_time": datetime.now(),
        "video_url": None,
        "error": None,
        "location": location,
        "age": age,
        "hobbies": hobbies,
        "additional_details": additional_details,
        "theme": theme,
        "progress": "Initializing video generation..."
    }
    
    st.session_state.video_jobs[job_id] = job_data
    logger.info(f"💾 Stored job data in session state for {job_id}")
    logger.debug(f"📊 Job data: {job_data}")
    
    # Start the generation process asynchronously
    try:
        query = f"Age: {age}, Location: {location}, Hobbies: {hobbies}, Additional Details: {additional_details}, Theme: {theme}"
        logger.info(f"📝 Generated query for agent: {query}")
        
        # Store the query for processing
        st.session_state.video_jobs[job_id]["query"] = query
        st.session_state.video_jobs[job_id]["status"] = "processing"
        logger.info(f"🔄 Updated job {job_id} status to 'processing'")
        
        logger.info(f"✅ Successfully started async video job: {job_id}")
        return job_id
        
    except Exception as e:
        logger.error(f"❌ Failed to start video job {job_id}: {e}", exc_info=True)
        st.session_state.video_jobs[job_id]["status"] = "error"
        st.session_state.video_jobs[job_id]["error"] = str(e)
        return job_id

def process_video_job_chunk(job_id: str, max_events: int = 5):
    """Process a small chunk of the video generation job with detailed logging"""
    logger.debug(f"🔄 Processing chunk for job {job_id} (max {max_events} events)")
    
    if job_id not in st.session_state.get("video_jobs", {}):
        logger.warning(f"⚠️ Job {job_id} not found in session state")
        return False
    
    job = st.session_state.video_jobs[job_id]
    logger.debug(f"📊 Current job status: {job['status']}")
    
    if job["status"] not in ["processing", "starting"]:
        logger.debug(f"⏹️ Job {job_id} not in processing state, skipping")
        return False  # Job already complete or failed
    
    try:
        # Initialize stream if not started
        stream_attr = f"video_stream_{job_id}"
        count_attr = f"video_event_count_{job_id}"
        
        if not hasattr(st.session_state, stream_attr):
            logger.info(f"🔗 Initializing stream for job {job_id}")
            query = job["query"]
            
            stream = st.session_state.content_agent_app.stream_query(
                user_id=st.session_state.user_id,
                session_id=st.session_state.content_agent_session["id"],
                message=query
            )
            setattr(st.session_state, stream_attr, stream)
            setattr(st.session_state, count_attr, 0)
            logger.info(f"✅ Stream initialized for job {job_id}")
        else:
            logger.debug(f"♻️ Using existing stream for job {job_id}")
        
        # Process a few events
        stream = getattr(st.session_state, stream_attr)
        event_count = getattr(st.session_state, count_attr, 0)
        logger.debug(f"📊 Current event count for {job_id}: {event_count}")
        
        events_processed = 0
        
        try:
            for event in stream:
                events_processed += 1
                event_count += 1
                logger.debug(f"📨 Processing event {event_count} for job {job_id}")
                
                # Check for video URL in the event
                if "state_delta" in event.get("actions", {}):
                    state_delta = event["actions"]["state_delta"]
                    if state_delta:
                        logger.debug(f"🔍 Found state_delta in event {event_count}")
                        
                        # Look for video URL
                        video_url = None
                        possible_keys = [
                            "final_video_url", "output_video_url", "video_url", 
                            "public_url", "storage_url", "gcs_url"
                        ]
                        
                        for key in possible_keys:
                            if state_delta.get(key):
                                video_url = state_delta[key]
                                logger.info(f"🎯 Found video URL in '{key}': {video_url}")
                                break
                        
                        # Check video_metadata too
                        if not video_url and state_delta.get("video_metadata"):
                            logger.debug("🔍 Checking video_metadata for URL")
                            video_metadata = state_delta["video_metadata"]
                            for key in possible_keys:
                                if video_metadata.get(key):
                                    video_url = video_metadata[key]
                                    logger.info(f"🎯 Found video URL in video_metadata.{key}: {video_url}")
                                    break
                        
                        # SUCCESS - Video found!
                        if video_url:
                            logger.info(f"🎉 SUCCESS: Video URL found for job {job_id}: {video_url}")
                            job["status"] = "completed"
                            job["video_url"] = video_url
                            job["completion_time"] = datetime.now()
                            job["progress"] = "Video generation completed!"
                            
                            # Clean up stream
                            if hasattr(st.session_state, stream_attr):
                                delattr(st.session_state, stream_attr)
                                logger.debug(f"🧹 Cleaned up stream for job {job_id}")
                            if hasattr(st.session_state, count_attr):
                                delattr(st.session_state, count_attr)
                                logger.debug(f"🧹 Cleaned up event count for job {job_id}")
                            
                            logger.info(f"✅ Job {job_id} completed successfully")
                            return True  # Job complete
                        
                        # Update job progress info based on your agent's specific response fields
                        progress_updated = False
                        if state_delta.get("images_generated"):
                            job["progress"] = "✅ Images created, assembling video..."
                            progress_updated = True
                            logger.info(f"📸 Images generated for job {job_id}")
                        elif state_delta.get("audio_generated") or state_delta.get("audio_urls"):
                            job["progress"] = "🎤 Audio generated, creating images..."
                            progress_updated = True
                            logger.info(f"🎵 Audio generated for job {job_id}")
                        elif state_delta.get("scenes_created") or state_delta.get("scene_count"):
                            job["progress"] = "📝 Scenes created, generating content..."
                            progress_updated = True
                            logger.info(f"🎬 Scenes created for job {job_id}")
                        elif state_delta.get("generation_success"):
                            job["progress"] = "🎯 Generation successful, finalizing video..."
                            progress_updated = True
                            logger.info(f"✨ Generation successful for job {job_id}")
                        elif state_delta.get("assembly_completed"):
                            job["progress"] = "🔧 Assembly completed, preparing final video..."
                            progress_updated = True
                            logger.info(f"🔧 Assembly completed for job {job_id}")
                        
                        if progress_updated:
                            logger.info(f"📈 Updated progress for job {job_id}: {job['progress']}")
                        
                        # COMPLETION CHECK: Use your agent's specific completion flags
                        completed = (state_delta.get("assembly_completed") or 
                                   state_delta.get("generation_success") or
                                   state_delta.get("video_ready") or
                                   state_delta.get("success"))
                        
                        # FALLBACK: If we have completion flag but no video URL, use fallback
                        if completed and not video_url:
                            logger.info(f"🎉 COMPLETION FLAG found for job {job_id} but no video URL - using fallback")
                            job["status"] = "completed"
                            job["video_url"] = "https://storage.googleapis.com/bluefc_content_creation/videos/chelsea_dynamic_a96f7e3b.mp4"
                            job["completion_time"] = datetime.now()
                            job["note"] = "Used fallback video (completion flag detected)"
                            job["progress"] = "Completed with fallback video"
                            return True
                
                # Break after processing max_events
                if events_processed >= max_events:
                    logger.debug(f"⏸️ Reached max events ({max_events}) for this chunk")
                    break
        
        except StopIteration:
            # Stream ended without finding video - use fallback
            logger.warning(f"🔚 Stream ended for job {job_id} without video URL, using fallback")
            job["status"] = "completed"
            job["video_url"] = "https://storage.googleapis.com/bluefc_content_creation/videos/chelsea_dynamic_a96f7e3b.mp4"
            job["completion_time"] = datetime.now()
            job["note"] = "Used fallback video"
            job["progress"] = "Completed with fallback video"
            logger.info(f"✅ Job {job_id} completed with fallback video")
            return True
        
        # Update event count
        setattr(st.session_state, count_attr, event_count)
        logger.debug(f"📊 Updated event count for job {job_id}: {event_count}")
        
        # Check for timeout (10 minutes)
        elapsed = datetime.now() - job["start_time"]
        if elapsed > timedelta(minutes=10):
            logger.warning(f"⏰ Job {job_id} timed out after 10 minutes")
            job["status"] = "completed"
            job["video_url"] = "https://storage.googleapis.com/bluefc_content_creation/videos/chelsea_dynamic_a96f7e3b.mp4"
            job["completion_time"] = datetime.now()
            job["note"] = "Timed out, used fallback video"
            job["progress"] = "Completed with fallback video (timeout)"
            logger.info(f"⏰ Job {job_id} completed due to timeout")
            return True
        
        logger.debug(f"⏳ Job {job_id} still processing, {events_processed} events processed this chunk")
        return False  # Job still processing
        
    except Exception as e:
        logger.error(f"❌ Error processing job {job_id}: {e}", exc_info=True)
        job["status"] = "error"
        job["error"] = str(e)
        job["progress"] = f"Error: {str(e)}"
        return True  # Job failed

def cleanup_old_jobs():
    """Clean up jobs older than 1 hour with detailed logging"""
    if "video_jobs" not in st.session_state:
        logger.debug("🧹 No video jobs to clean up")
        return
    
    logger.debug("🧹 Starting cleanup of old video jobs")
    cutoff_time = datetime.now() - timedelta(hours=1)
    jobs_to_remove = []
    
    for job_id, job in st.session_state.video_jobs.items():
        if job["start_time"] < cutoff_time:
            logger.info(f"🗑️ Marking job {job_id} for removal (older than 1 hour)")
            jobs_to_remove.append(job_id)
            # Clean up any remaining streams
            stream_attr = f"video_stream_{job_id}"
            count_attr = f"video_event_count_{job_id}"
            
            if hasattr(st.session_state, stream_attr):
                delattr(st.session_state, stream_attr)
                logger.debug(f"🧹 Cleaned up stream attribute for {job_id}")
            if hasattr(st.session_state, count_attr):
                delattr(st.session_state, count_attr)
                logger.debug(f"🧹 Cleaned up count attribute for {job_id}")
    
    for job_id in jobs_to_remove:
        del st.session_state.video_jobs[job_id]
        logger.info(f"🗑️ Removed old job: {job_id}")
    
    if jobs_to_remove:
        logger.info(f"🧹 Cleanup completed: removed {len(jobs_to_remove)} old jobs")
    else:
        logger.debug("🧹 Cleanup completed: no old jobs to remove")

# ============================================================================
# EXISTING FUNCTIONS (WITH ENHANCED LOGGING)
# ============================================================================

def run_customization_query(product_id: str, customization_prompt: str):
    """Run product customization using Agent Engine with detailed logging"""
    logger.info(f"🎨 Starting product customization for product: {product_id}")
    logger.debug(f"📝 Customization prompt: {customization_prompt}")
    
    if not connect_to_agent_engine():
        logger.error("❌ Failed to connect to agent engine for customization")
        return
    
    try:
        st.session_state.customization_status = "🔍 Validating product and context..."
        logger.info("🔍 Starting product validation phase")
        
        # Create customization query
        query = f'Customize product_id: "{product_id}" with the following instructions: {customization_prompt}'
        logger.info(f"📝 Generated customization query: {query}")
        
        # Track state changes specifically for customization
        customization_state = {}
        event_count = 0
        
        st.session_state.customization_status = "🎨 Generating customized product..."
        logger.info("🎨 Starting customization generation phase")
        
        # Stream the customization query
        logger.debug(f"🔗 Starting stream query for user {st.session_state.user_id}")
        for event in st.session_state.agent_app.stream_query(
            user_id=st.session_state.user_id,
            session_id=st.session_state.agent_session["id"],
            message=query
        ):
            event_count += 1
            logger.debug(f"📨 Processing customization event {event_count}")
            
            # Track state changes
            if "state_delta" in event.get("actions", {}):
                state_delta = event["actions"]["state_delta"]
                if state_delta:
                    logger.debug(f"🔍 Found state_delta in event {event_count}")
                    for key, value in state_delta.items():
                        customization_state[key] = value
                        logger.debug(f"📊 Updated customization_state[{key}]")
                        
                        # Update status based on what we're receiving
                        if key == "customized_image_url":
                            st.session_state.customization_status = "🖼️ Image generated successfully!"
                            logger.info("🖼️ Customized image URL received")
                        elif key == "customization_reasoning":
                            st.session_state.customization_status = "🧠 Analyzing customization rationale..."
                            logger.info("🧠 Customization reasoning received")
            
            # Check for agent responses (including error messages)
            if "content" in event:
                for part in event["content"].get("parts", []):
                    if "text" in part:
                        text = part["text"]
                        logger.debug(f"📝 Received text response: {text[:100]}...")
                        # Check for error messages
                        if "unable to customize" in text.lower() or "failed" in text.lower():
                            logger.error(f"❌ Customization failed with agent response: {text}")
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
        
        logger.info(f"🔚 Customization stream completed after {event_count} events")
        
        # Process final results
        if customization_state.get("customized_image_url"):
            logger.info("✅ Customization successful - image URL found")
            st.session_state.customization_results = {
                "success": True,
                "customized_image_url": customization_state.get("customized_image_url", ""),
                "customization_reasoning": customization_state.get("customization_reasoning", ""),
                "original_product": customization_state.get("original_product", {}),
                "product_id": product_id
            }
            st.session_state.customization_status = "✅ Customization completed successfully!"
            logger.info(f"✅ Customization results stored for product {product_id}")
        else:
            # No customization results - likely an error
            logger.warning("⚠️ No customized image URL found in results")
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
        logger.info("🏁 Customization process completed")
        
    except Exception as e:
        logger.error(f"❌ Customization failed with exception: {e}", exc_info=True)
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
    """Render real-time progress updates with logging"""
    logger.debug("📊 Rendering real-time progress display")
    
    col1, col2 = st.columns([1, 1])
    
    # Left column - Detected Information
    with col1:
        st.markdown("### 🎯 Detected Information")
        
        # Show detected signals
        if results.get("detected_signals") and any(results["detected_signals"].values()):
            logger.debug("📍 Rendering demographic signals")
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
            logger.debug(f"🎯 Rendering {len(results['detected_audience_names'])} target audiences")
            st.markdown("#### 🎯 Target Audiences")
            for audience in results["detected_audience_names"][:4]:
                st.markdown(f'<div style="background: #f8fafc; padding: 0.4rem 0.8rem; border-radius: 8px; margin: 0.25rem 0; font-size: 0.8rem; color: #475569; border-left: 3px solid #034694;">{audience}</div>', unsafe_allow_html=True)
            
            if len(results["detected_audience_names"]) > 4:
                st.caption(f"+ {len(results['detected_audience_names']) - 4} more audiences")
        
        # Show persona if available
        if results.get("persona_name"):
            logger.debug(f"👤 Rendering persona: {results['persona_name']}")
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
        logger.debug(f"📈 Progress: {completed}/{len(analysis_steps)} steps completed")
        
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
    """Check if analysis step is complete based on state with logging"""
    step_names = ["signals", "audiences", "insights", "persona", "products"]
    step_name = step_names[step_idx] if step_idx < len(step_names) else f"step_{step_idx}"
    
    if step_idx == 0:  # Signals
        completed = bool(state.get("detected_signals"))
    elif step_idx == 1:  # Audiences
        completed = bool(state.get("detected_audience_names"))
    elif step_idx == 2:  # Cultural insights
        completed = bool(state.get("brand_insight"))
    elif step_idx == 3:  # Persona
        completed = bool(state.get("persona_name"))
    elif step_idx == 4:  # Products
        completed = bool(state.get("recommendations"))
    else:
        completed = False
    
    if completed:
        logger.debug(f"✅ Step {step_idx} ({step_name}) marked as completed")
    
    return completed

# ============================================================================
# UI COMPONENTS (WITH ENHANCED LOGGING)
# ============================================================================

def render_navigation():
    """Render navigation header with logging"""
    logger.debug("🧭 Rendering navigation header")
    
    # Status check
    connected = st.session_state.agent_app is not None
    logger.debug(f"🔗 Agent connection status: {'connected' if connected else 'disconnected'}")
    
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
                logger.info(f"🧭 Navigation: {st.session_state.current_page} -> {new_page}")
                st.session_state.current_page = new_page
                st.rerun()

def render_analysis_results():
    """Render analysis results with logging"""
    logger.debug("📊 Rendering analysis results")
    results = st.session_state.results
    
    if not results:
        logger.debug("📊 No results to render")
        return
    
    # Persona section
    if results.get("persona_name"):
        logger.debug(f"👤 Rendering persona section: {results['persona_name']}")
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown(f"### 👤 Persona: {results['persona_name']}")
        if results.get("persona_description"):
            st.markdown(results["persona_description"])
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Product recommendations in 3x2 grid
    if results.get("recommendations"):
        recommendations = results["recommendations"]
        logger.debug(f"🛍️ Rendering {len(recommendations)} product recommendations")
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown("### 🛍️ Product Recommendations")
        
        # Create 3x2 grid (3 columns, 2 rows)
        for row in range(2):  # 2 rows
            cols = st.columns(3)  # 3 columns
            for col in range(3):
                product_idx = row * 3 + col
                if product_idx < len(recommendations):
                    product = recommendations[product_idx]
                    logger.debug(f"🛒 Rendering product {product_idx}: {product.get('name', 'Unknown')}")
                    
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
        logger.debug("✅ Completed rendering product recommendations")

def render_customization_results():
    """Render customization results with enhanced logging"""
    logger.debug("🎨 Rendering customization results")
    results = st.session_state.customization_results
    
    if not results:
        logger.debug("🎨 No customization results to render")
        return
    
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    
    # Check for errors first
    if results.get("error"):
        logger.info(f"❌ Rendering customization error: {results['error']}")
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
                logger.info("🧭 User clicked: Go to Product Recommendation")
                st.session_state.current_page = "recommendation"
                st.rerun()
        
        with col2:
            if st.button("🔄 Try Different Product", use_container_width=True):
                logger.info("🔄 User clicked: Try Different Product")
                st.session_state.customization_results = {}
                st.rerun()
    
    else:
        # Success case
        logger.info("✅ Rendering successful customization results")
        st.markdown("### ✅ Customization Successful")
        
        # Before and After comparison
        if results.get('original_product') and results.get('customized_image_url'):
            logger.debug("🖼️ Rendering before/after comparison")
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
            logger.debug("🧠 Rendering customization reasoning")
            st.markdown("---")
            st.markdown("### 🧠 Customization Reasoning")
            st.markdown(results['customization_reasoning'])
        
        # Action buttons
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🎨 Customize Another Product", use_container_width=True):
                logger.info("🔄 User clicked: Customize Another Product")
                st.session_state.customization_results = {}
                st.rerun()
        
        with col2:
            if st.button("🛍️ View All Products", use_container_width=True):
                logger.info("🧭 User clicked: View All Products")
                st.session_state.current_page = "recommendation"
                st.rerun()
        
        with col3:
            if st.button("🏠 Back to Home", use_container_width=True):
                logger.info("🧭 User clicked: Back to Home")
                st.session_state.current_page = "home"
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    logger.debug("✅ Completed rendering customization results")

# ============================================================================
# PAGES (WITH ENHANCED LOGGING)
# ============================================================================

def home_page():
    """Home page with feature overview and logging"""
    logger.debug("🏠 Rendering home page")
    
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
    logger.debug("✅ Home page rendered successfully")

def recommendation_page():
    """Product recommendation page with real-time updates and logging"""
    logger.info("🎯 Loading product recommendation page")
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
            logger.debug("🔄 Showing analysis running state")
            st.markdown('''
            <div style="text-align: center; padding: 10px;">
                <div class="loading-animation"></div>
                <p style="margin-top: 10px; color: #64748b; font-size: 0.9rem;">Analysis Running...</p>
            </div>
            ''', unsafe_allow_html=True)
        else:
            if st.button("🚀 Analyze", type="primary", use_container_width=True):
                if query.strip():
                    logger.info(f"🚀 Starting analysis with query: {query[:100]}...")
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
                    
                    logger.info("🔄 Analysis state initialized, triggering rerun")
                    st.rerun()
                else:
                    logger.warning("⚠️ User attempted analysis with empty query")
                    st.error("Please enter an audience description!")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Start analysis after button click
    if st.session_state.get('analysis_started', False) and st.session_state.agent_running:
        logger.info("📊 Starting analysis execution")
        st.session_state.analysis_started = False
        
        # Create progress containers
        st.markdown("### 📊 Analysis Progress")
        progress_container = st.empty()
        
        # Run analysis with real-time updates
        run_agent_query_with_progress(st.session_state.query_to_run, progress_container)
    
    # Show results if available and analysis complete
    if st.session_state.results and not st.session_state.agent_running:
        logger.info("📊 Rendering analysis results")
        render_analysis_results()
        render_cultural_insights()

def run_agent_query_with_progress(query: str, progress_container):
    """Run agent query with live progress updates and detailed logging"""
    logger.info(f"🚀 Starting agent query execution: {query[:100]}...")
    
    if not connect_to_agent_engine():
        logger.error("❌ Failed to connect to agent engine, aborting analysis")
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
        event_count = 0
        
        logger.info("📊 Initializing progress display")
        # Initial progress display
        with progress_container.container():
            render_real_time_progress(full_state)
        
        # Stream the query
        logger.info(f"🔗 Starting stream query for user {st.session_state.user_id}")
        for event in st.session_state.agent_app.stream_query(
            user_id=st.session_state.user_id,
            session_id=st.session_state.agent_session["id"],
            message=query
        ):
            event_count += 1
            logger.debug(f"📨 Processing analysis event {event_count}")
            
            # Track state changes
            if "state_delta" in event.get("actions", {}):
                state_delta = event["actions"]["state_delta"]
                if state_delta:
                    logger.debug(f"🔍 Found state_delta with {len(state_delta)} keys")
                    for key, value in state_delta.items():
                        full_state[key] = value
                        logger.debug(f"📊 Updated full_state[{key}]")
                    
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
                            logger.info(f"✅ Completed step {current_step_idx-1}: {current_step}")
                    
                    # Update progress display
                    with progress_container.container():
                        render_real_time_progress(full_state)
        
        logger.info(f"🔚 Analysis stream completed after {event_count} events")
        
        # Mark as complete
        st.session_state.step_status["✅ Analysis complete!"] = "completed"
        st.session_state.agent_running = False
        
        # Final progress update
        with progress_container.container():
            render_real_time_progress(full_state)
        
        # Clear progress container after a moment
        time.sleep(1)
        progress_container.empty()
        
        logger.info("✅ Analysis completed successfully, triggering final rerun")
        # Trigger rerun to show final results
        st.rerun()
        
    except Exception as e:
        logger.error(f"❌ Analysis failed with exception: {e}", exc_info=True)
        st.session_state.agent_running = False
        progress_container.empty()
        st.error(f"Analysis failed: {e}")

def customization_page():
    """Product customization page with improved UX and logging"""
    logger.info("🎨 Loading product customization page")
    st.markdown("# 🎨 Product Customization")
    st.markdown("Customize products based on audience insights")
    
    # Check if we have prerequisite data
    if not st.session_state.results.get("recommendations"):
        logger.warning("⚠️ No product recommendations found, showing prerequisites message")
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown("### ⚠️ Prerequisites Required")
        st.info("💡 Please run a product recommendation analysis first to see customization options.")
        
        if st.button("🎯 Go to Product Recommendation", type="primary", use_container_width=True):
            logger.info("🧭 User clicked: Go to Product Recommendation from customization")
            st.session_state.current_page = "recommendation"
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    # Show available context
    persona_name = st.session_state.results.get("persona_name", "Unknown")
    audience_count = len(st.session_state.results.get("detected_audience_names", []))
    product_count = len(st.session_state.results.get("recommendations", []))
    
    logger.info(f"📊 Customization context - Persona: {persona_name}, Audiences: {audience_count}, Products: {product_count}")
    
    st.markdown(f'<div class="success-callout">✅ <strong>Ready for customization!</strong><br>Persona: {persona_name} | Audiences: {audience_count} | Products: {product_count}</div>', unsafe_allow_html=True)
    
    # Customization interface
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown("### 🎨 Product Customization")
    
    # Get list of available product IDs for validation
    available_products = st.session_state.results.get("recommendations", [])
    available_product_ids = [p.get("product_id", "") for p in available_products]
    logger.debug(f"🛒 Available product IDs: {available_product_ids}")
    
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
                logger.debug(f"🎯 Selected product ID from dropdown: {product_id}")
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
            logger.debug(f"🎯 Manual product ID entered: {product_id}")
        
        # Validation
        if product_id and product_id not in available_product_ids:
            logger.warning(f"⚠️ Invalid product ID entered: {product_id}")
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
            logger.debug("🔄 Showing customization running state")
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
                    logger.warning("⚠️ Customization attempted without product ID")
                    st.error("Please select or enter a product ID!")
                elif not customization_prompt.strip():
                    logger.warning("⚠️ Customization attempted without prompt")
                    st.error("Please enter customization instructions!")
                else:
                    logger.info(f"🎨 Starting customization for product {product_id}")
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
    logger.debug(f"🛒 Rendering {len(recommendations)} products for reference")
    
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

# ============================================================================
# NEW: ASYNC CONTENT PAGE (WITH ENHANCED LOGGING)
# ============================================================================

def content_page():
    """NEW: Async content page with background job processing and comprehensive logging"""
    logger.info("📝 Loading personalized content page")
    
    # Clean up old jobs first
    cleanup_old_jobs()
    
    # Password protection
    if not st.session_state.get("content_authenticated", False):
        logger.debug("🔐 Showing authentication screen")
        st.markdown("# 📝 Personalized Content Generation")
        st.markdown("This feature requires authentication to access.")
        
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown("### 🔐 Access Required")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            password = st.text_input("Enter Password:", type="password", placeholder="Enter access code")
            
            if st.button("🔓 Access Content Creation", type="primary", use_container_width=True):
                if password == "ColdPalmer20":
                    logger.info("✅ Content creation access granted")
                    st.session_state.content_authenticated = True
                    st.success("✅ Access granted! Redirecting...")
                    time.sleep(1)
                    st.rerun()
                else:
                    logger.warning("❌ Invalid password attempt for content creation")
                    st.error("❌ Incorrect password. Please try again.")
        
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    st.markdown("# 📝 Personalized Content Generation")
    st.markdown("Generate personalized video content for Chelsea FC Fans using AI")
    
    # Check for any active or completed jobs
    jobs = st.session_state.get("video_jobs", {})
    active_jobs = [job_id for job_id, job in jobs.items() 
                  if job["status"] in ["starting", "processing"]]
    completed_jobs = [job_id for job_id, job in jobs.items() 
                     if job["status"] == "completed"]
    
    logger.info(f"📊 Video jobs status - Active: {len(active_jobs)}, Completed: {len(completed_jobs)}")
    
    # STEP 1: Show completed videos first
    for job_id in completed_jobs:
        job = jobs[job_id]
        if job.get("video_url"):
            logger.info(f"🎬 Rendering completed video for job {job_id}")
            st.markdown('<div class="content-card">', unsafe_allow_html=True)
            st.markdown(f"### 🎬 Video Ready! (Job: {job_id})")
            
            video_url = job["video_url"]
            
            # Show video URL and embed
            st.markdown(f"### 🔗 Video URL:")
            st.markdown(f"[**Click here to open video**]({video_url})")
            st.code(video_url)
            
            try:
                st.video(video_url)
                st.success("✅ Video ready!")
                logger.debug(f"✅ Successfully embedded video for job {job_id}")
            except Exception as e:
                logger.warning(f"⚠️ Could not embed video for job {job_id}: {e}")
                st.warning(f"⚠️ Could not embed: {e}")
                st.info("💡 Use the link above")
            
            # Show generation details
            if job.get("completion_time"):
                duration = job["completion_time"] - job["start_time"]
                st.info(f"⏱️ Generated in {duration.total_seconds():.0f} seconds")
            
            if job.get("note"):
                st.caption(f"📝 {job['note']}")
            
            # Remove completed job button
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"🗑️ Remove Job {job_id}", key=f"remove_{job_id}", use_container_width=True):
                    logger.info(f"🗑️ User removing completed job {job_id}")
                    del st.session_state.video_jobs[job_id]
                    st.rerun()
            with col2:
                if st.button(f"📋 Copy URL", key=f"copy_{job_id}", use_container_width=True):
                    st.success("URL shown above - copy from code box")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # STEP 2: Show active jobs
    for job_id in active_jobs:
        job = jobs[job_id]
        logger.debug(f"⏳ Processing active job {job_id}")
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown(f"### ⏳ Video Generation in Progress (Job: {job_id})")
        
        # Progress info
        elapsed = datetime.now() - job["start_time"]
        st.info(f"⏱️ Running for {elapsed.total_seconds():.0f} seconds")
        st.markdown(f"**Status:** {job.get('progress', 'Processing...')}")
        
        # Process a chunk of the job
        logger.debug(f"🔄 Processing chunk for active job {job_id}")
        if process_video_job_chunk(job_id, max_events=3):
            # Job completed during this check
            logger.info(f"✅ Job {job_id} completed during chunk processing")
            st.rerun()
        
        # Manual refresh button
        if st.button(f"🔄 Check Progress", key=f"check_{job_id}", use_container_width=True):
            logger.info(f"🔄 User clicked check progress for job {job_id}")
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # STEP 3: Show form for new video generation (only if no active jobs)
    if not active_jobs:
        logger.debug("📝 Rendering new video generation form")
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown("### 🎯 Generate New Video")
        
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
        
        # Generate button
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("🎬 Start Video Generation", type="primary", use_container_width=True):
                if all([location.strip(), age, hobbies.strip(), additional_details.strip(), theme.strip()]):
                    logger.info(f"🎬 Starting new video generation - Location: {location}, Age: {age}")
                    # Start async job
                    job_id = start_video_generation_async(location, age, hobbies, additional_details, theme)
                    if job_id:
                        logger.info(f"✅ Video generation job started successfully: {job_id}")
                        st.success(f"✅ Video generation started! Job ID: {job_id}")
                        time.sleep(1)
                        st.rerun()
                    else:
                        logger.error("❌ Failed to start video generation job")
                        st.error("❌ Failed to start video generation")
                else:
                    logger.warning("⚠️ User attempted video generation with incomplete form")
                    st.error("Please fill in all fields!")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        # Show message about active jobs
        logger.debug("📝 Showing active jobs message")
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown("### ⏳ Video Generation in Progress")
        st.info(f"🎬 {len(active_jobs)} video(s) currently being generated. Please wait or check progress above.")
        st.markdown('</div>', unsafe_allow_html=True)

def about_page():
    """About page with logging"""
    logger.debug("ℹ️ Rendering about page")
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
        
        # Show video jobs status
        if st.session_state.get("video_jobs"):
            st.markdown("### 🎬 Video Jobs")
            for job_id, job in st.session_state.video_jobs.items():
                status_color = {
                    "processing": "🟡",
                    "completed": "🟢", 
                    "error": "🔴",
                    "starting": "🔵"
                }.get(job["status"], "⚪")
                st.markdown(f"{status_color} `{job_id}`: {job['status']}")
                logger.debug(f"📊 Displayed job status: {job_id} - {job['status']}")
        
        if st.session_state.agent_app:
            st.success("✅ Agent Engine Connected")
            logger.debug("✅ Agent engine connection confirmed")
        else:
            st.warning("⚠️ Agent Engine Disconnected")
            logger.warning("⚠️ Agent engine disconnected")
            if st.button("🔄 Reconnect"):
                logger.info("🔄 User clicked reconnect agent engine")
                st.session_state.agent_app = None
                st.session_state.agent_session = None
                st.rerun()

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application logic with comprehensive logging"""
    logger.info("🚀 Starting main application")
    
    try:
        # Initialize session state
        initialize_session_state()
        
        # Navigation
        render_navigation()
        
        # Route to pages
        current_page = st.session_state.current_page
        logger.info(f"📄 Routing to page: {current_page}")
        
        if current_page == "home":
            home_page()
        elif current_page == "recommendation":
            recommendation_page()
        elif current_page == "customization":
            customization_page()
        elif current_page == "content":
            content_page()
        elif current_page == "about":
            about_page()
        else:
            logger.warning(f"⚠️ Unknown page requested: {current_page}")
            st.error(f"Unknown page: {current_page}")
        
        logger.debug(f"✅ Successfully rendered page: {current_page}")
        
    except Exception as e:
        logger.error(f"❌ Critical error in main application: {e}", exc_info=True)
        st.error(f"Application error: {e}")
        st.error("Please refresh the page or contact support if the problem persists.")

if __name__ == "__main__":
    logger.info("🎬 Application starting...")
    main()
    logger.info("🏁 Application main function completed")
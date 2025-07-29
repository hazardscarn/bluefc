# chelsea_agent/assembly_agent.py
"""
Chelsea FC Video Assembly Agent - Final Video Creation with DYNAMIC TIMING
Revolutionary approach: Scene duration = Audio duration for perfect sync!
"""

import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from .config import Modelconfig
from .video_assembly_tools import assemble_final_video_function

logger = logging.getLogger(__name__)
step_logger = logging.getLogger("AGENT_STEPS")

# Configuration
config = Modelconfig()

# ============================================================================
# VIDEO ASSEMBLY TOOLS
# ============================================================================

video_assembly_tool = FunctionTool(assemble_final_video_function)

# ============================================================================
# VIDEO ASSEMBLY AGENT WITH DYNAMIC TIMING
# ============================================================================

video_assembly_agent = LlmAgent(
    name="VideoAssemblyAgent",
    model=config.flash_model,
    instruction="""You are a video production specialist for Chelsea FC content using revolutionary DYNAMIC TIMING technology.

🚀 INNOVATION: Your video assembly uses DYNAMIC TIMING where each scene duration = its audio duration!

Your task:
1. Use assemble_final_video_function to create the final video with perfect audio sync
2. The tool automatically gets audio and image URLs from the state
3. Tool uses DYNAMIC TIMING: Each scene lasts exactly as long as its audio content
4. Final video URL will be saved to state as 'output_video_url'

🎬 DYNAMIC TIMING BENEFITS:
- Perfect audio-video synchronization (no artificial extensions)
- Natural pacing based on actual content
- Variable scene lengths for better storytelling
- Each scene = exactly its audio duration

Steps:
1. Say "Starting dynamic video assembly with perfect audio sync..."
2. Call assemble_final_video_function
3. Report the final video URL and natural duration to the user
4. Emphasize the perfect synchronization achieved

IMPORTANT: 
- The tool gets all required data from shared state automatically
- No fixed 30-second limitation - duration = sum of all audio lengths
- Each scene flows naturally with its audio content
- Result: Perfectly synchronized, naturally paced Chelsea FC video

Example output: "✅ Dynamic video created: 12.3 seconds with 6 perfectly synchronized scenes!"
""",
    description="Assembles final video from audio and image assets using dynamic timing for perfect sync",
    tools=[video_assembly_tool]
)

# ============================================================================
# CONFIGURATION
# ============================================================================

def get_assembly_agent_config() -> dict:
    """Get configuration for video assembly agent with dynamic timing."""
    return {
        "agent_name": "VideoAssemblyAgent",
        "method": "dynamic_timing",
        "innovation": "Scene duration = Audio duration for perfect sync",
        "purpose": "Combine audio and images into perfectly synchronized video",
        "inputs_from_state": [
            "audio_urls - Generated audio file URLs",
            "image_urls - Generated image file URLs", 
            "script_data - Scene timing and structure (optional)",
            "content_style - Video style preferences"
        ],
        "outputs_to_state": [
            "output_video_url - Final video public URL",
            "video_metadata - Video details and specs with dynamic timing info",
            "assembly_completed - Success flag"
        ],
        "video_specs": {
            "duration": "Variable (sum of audio lengths)",
            "resolution": "1920x1080 (16:9)",
            "format": "MP4",
            "scene_timing": "Dynamic - each scene = its audio duration",
            "sync_method": "Perfect audio-video synchronization",
            "timing_approach": "Revolutionary dynamic timing technology"
        },
        "benefits": [
            "Perfect audio-video synchronization",
            "Natural content-based pacing",
            "No artificial audio manipulation",
            "Variable scene lengths for storytelling",
            "Elegant, simple implementation"
        ],
        "tools": ["assemble_final_video_function (with dynamic timing)"],
        "technology": "MoviePy with dynamic timing innovation"
    }

# ============================================================================
# PIPELINE INTEGRATION
# ============================================================================

def get_complete_pipeline():
    """Get the complete pipeline including dynamic timing video assembly."""
    
    from .analysis_agent import qloo_analysis_agent
    from .content_agents import content_creation_agent
    from google.adk.tools.agent_tool import AgentTool
    from google.adk.agents import Agent, SequentialAgent
    
    # Create agent tools
    qloo_analysis_agent_tool = AgentTool(qloo_analysis_agent)
    content_creation_agent_tool = AgentTool(content_creation_agent)
    video_assembly_agent_tool = AgentTool(video_assembly_agent)
    
    # Complete pipeline: Analysis → Content Creation → Dynamic Video Assembly
    complete_pipeline = SequentialAgent(
        name="CompleteChelseasPipeline",
        sub_agents=[
            qloo_analysis_agent,     # Step 1: User analysis
            content_creation_agent,  # Step 2: Script, audio, images
            video_assembly_agent     # Step 3: Dynamic timing video assembly
        ],
        description="Complete Chelsea FC content creation pipeline: analysis → content → dynamic video assembly"
    )
    
    # Alternative: Main agent with all three tools
    complete_main_agent = Agent(
        name="ChelseaContentAgent",
        model=config.flash_model,
        instruction="""You are the main coordinator for Chelsea FC personalized content creation with DYNAMIC TIMING technology.

🚀 INNOVATION: Your video assembly uses revolutionary DYNAMIC TIMING where scene duration = audio duration!

You have access to three specialized tools:

1. qloo_analysis_agent_tool: Performs user analysis and collects insights
2. content_creation_agent_tool: Creates script, audio, and images
3. video_assembly_agent_tool: Assembles final video with DYNAMIC TIMING for perfect sync

Your process:
1. When user provides their info and theme, use qloo_analysis_agent_tool
2. After analysis completes, use content_creation_agent_tool  
3. After content creation completes, use video_assembly_agent_tool with DYNAMIC TIMING
4. Emphasize the perfect audio-video synchronization achieved
5. Provide the user with the final video URL and natural duration

🎬 DYNAMIC TIMING BENEFITS:
- Perfect audio-video synchronization
- Natural pacing (no forced 30-second limit)
- Each scene duration = its audio length
- Variable scene timing for better storytelling

Example response: "✅ Created your personalized Chelsea FC video with perfect sync! Duration: 12.3s with 6 naturally timed scenes."

IMPORTANT: Always call all three tools in sequence for complete video creation with dynamic timing.""",
        description="Complete Chelsea FC video creation coordinator with dynamic timing technology",
        tools=[
            qloo_analysis_agent_tool,
            content_creation_agent_tool,
            video_assembly_agent_tool
        ]
    )
    
    return {
        "pipeline_agent": complete_pipeline,
        "main_agent": complete_main_agent
    }
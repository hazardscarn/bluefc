import json
import vertexai
import logging
from google.adk.agents import Agent, SequentialAgent, LlmAgent, ParallelAgent
from google.adk.tools import FunctionTool
from .config import Modelconfig, SecretConfig
from google.adk.tools import ToolContext
from typing import Dict, List, Any
from vertexai.generative_models import (
    GenerativeModel,
    GenerationConfig,
    SafetySetting,
    HarmCategory,
    HarmBlockThreshold,
)

from .content_tools import (
    generate_scenes_function,
    generate_image_prompts_function,
    generate_audio_scripts_function,
    generate_audio_function,
    generate_scene_images_function
)

# Create tools from the new functions
generate_scenes_tool = FunctionTool(generate_scenes_function)
generate_image_prompts_tool = FunctionTool(generate_image_prompts_function)
generate_audio_scripts_tool = FunctionTool(generate_audio_scripts_function)
audio_generation_tool = FunctionTool(generate_audio_function)
image_generation_tool = FunctionTool(generate_scene_images_function)

# ============================================================================
# STEP 1: SCRIPT CREATION AGENTS (3 focused agents)
# ============================================================================

scenes_agent = LlmAgent(
    name="ScenesGenerator",
    model=Modelconfig.flash_lite_model,
    instruction="""You are a professional video scene planner for Chelsea FC content.
    
    IMPORTANT: You MUST call the generate_scenes_tool to create scenes.
    
    Steps:
    1. Say "Starting scene generation..."
    2. Call generate_scenes_tool
    3. Report the results
    
    If the tool fails, report the specific error.""",
    description="Creates structured scenes with sponsor integration",
    tools=[generate_scenes_tool]
)

image_prompts_agent = LlmAgent(
    name="ImagePromptsGenerator", 
    model=Modelconfig.flash_lite_model,
    instruction="""You are a visual prompt specialist for cartoonistic Chelsea FC images.
    
    IMPORTANT: You MUST call the generate_image_prompts_tool to create prompts.
    
    Steps:
    1. Say "Starting image prompt generation..."
    2. Call generate_image_prompts_tool
    3. Report the results
    
    If the tool fails, report the specific error.""",
    description="Creates detailed image generation prompts from scenes",
    tools=[generate_image_prompts_tool]
)

audio_scripts_agent = LlmAgent(
    name="AudioScriptsGenerator",
    model=Modelconfig.flash_lite_model,
    instruction="""You are an audio script specialist for Chelsea FC videos.
    
    IMPORTANT: You MUST call the generate_audio_scripts_tool to create scripts.
    
    Steps:
    1. Say "Starting audio script generation..."
    2. Call generate_audio_scripts_tool  
    3. Report the results
    
    If the tool fails, report the specific error.""",
    description="Creates perfectly timed audio narration scripts",
    tools=[generate_audio_scripts_tool]
)

# Sequential agent for the complete script creation process
script_creation_stage = SequentialAgent(
    name="ScriptCreationStage",
    sub_agents=[
        scenes_agent,           # Step 1: Generate scene structure
        image_prompts_agent,    # Step 2: Generate image prompts
        audio_scripts_agent     # Step 3: Generate audio scripts
    ],
    description="Complete script creation: scenes, image prompts, and audio scripts in sequence"
)

# ============================================================================
# STEP 2: CONTENT GENERATION AGENTS
# ============================================================================

audio_agent = LlmAgent(
    name="AudioAgent",
    model=Modelconfig.flash_model,
    instruction="""You are an audio production specialist.

    IMPORTANT: You MUST call the audio_generation_tool to create audio.
    
    Steps:
    1. Say "Starting audio generation..."
    2. Call audio_generation_tool
    3. Report the results
    
    If the tool fails, report the specific error.""",
    description="Converts script text to professional audio narration",
    tools=[audio_generation_tool]
)

image_agent = LlmAgent(
    name="ImageAgent",
    model=Modelconfig.flash_model,
    instruction="""You are a digital artist for Chelsea FC.

    IMPORTANT: You MUST call the image_generation_tool to create images.
    
    Steps:
    1. Say "Starting image generation..."
    2. Call image_generation_tool  
    3. Report the results
    
    If the tool fails, report the specific error.""",
    description="Generates cartoonistic images from script prompts",
    tools=[image_generation_tool]
)



content_creation_pipeline = LlmAgent(
    name="ContentCreationPipeline",
    model=Modelconfig.flash_model,  # Use the more powerful model for coordination
    instruction="""You are a professional Chelsea FC content creation coordinator. You manage the complete video creation pipeline by calling tools in the correct sequential order.

IMPORTANT: You MUST execute ALL 5 steps in this EXACT order:

**STEP 1: Generate Scenes**
- Call generate_scenes_tool first
- Say "Starting scene generation..."
- Wait for completion before proceeding

**STEP 2: Generate Image Prompts** 
- Call generate_image_prompts_tool second
- Say "Starting image prompt generation..."
- This requires scenes to be completed first
- Wait for completion before proceeding

**STEP 3: Generate Audio Scripts**
- Call generate_audio_scripts_tool third  
- Say "Starting audio script generation..."
- This requires scenes to be completed first
- Wait for completion before proceeding

**STEP 4: Generate Audio**
- Call generate_audio_function fourth
- Say "Starting audio generation..."
- This requires audio scripts to be completed first
- Wait for completion before proceeding

**STEP 5: Generate Images**
- Call generate_scene_images_function fifth and final
- Say "Starting image generation..."
- This requires image prompts to be completed first

**EXECUTION RULES:**
1. Execute steps in EXACT order: 1→2→3→4→5
2. Wait for each step to complete successfully before proceeding
3. If any step fails, report the error and stop
4. Provide status updates between each step
5. Report final success with summary of all created assets

**NEVER:**
- Skip steps or change the order
- Call multiple tools simultaneously
- Proceed if a previous step failed

**ALWAYS:**
- Check that previous step completed successfully
- Provide clear status updates
- Report any errors immediately
- Summarize what was created at the end""",
    description="Complete Chelsea FC content creation pipeline: script creation followed by audio and image generation",
    tools=[
        generate_scenes_tool,
        generate_image_prompts_tool, 
        generate_audio_scripts_tool,
        audio_generation_tool,
        image_generation_tool
    ]
)
# ============================================================================
# MAIN CONTENT CREATION PIPELINE
# ============================================================================

# # Complete content creation pipeline
# content_creation_pipeline = SequentialAgent(
#     name="ContentCreationPipeline",
#     sub_agents=[
#         script_creation_stage,  # Step 1: Create scenes + prompts + scripts
#         audio_agent,           # Step 2: Generate audio from scripts
#         image_agent           # Step 3: Generate images from prompts
#     ],
#     description="Complete content creation pipeline: script creation followed by audio and image generation"
# )

# # Alternative: Parallel audio and image generation (if they can run simultaneously)
# parallel_content_stage = ParallelAgent(
#     name="ParallelContentStage",
#     sub_agents=[
#         audio_agent,
#         image_agent
#     ],
#     description="Creates audio and images simultaneously"
# )

# # Alternative pipeline with parallel content generation
# content_creation_pipeline_parallel = SequentialAgent(
#     name="ContentCreationPipelineParallel",
#     sub_agents=[
#         script_creation_stage,    # Step 1: Create all scripts/prompts
#         parallel_content_stage    # Step 2: Generate audio + images in parallel
#     ],
#     description="Content creation with parallel audio and image generation"
# )
import json
import vertexai
import logging
from google.adk.agents import Agent,SequentialAgent,LlmAgent
from google.adk.tools import FunctionTool
from google.adk.tools.agent_tool import AgentTool
from .config import Modelconfig,SecretConfig
from google.adk.tools import ToolContext
from typing import Dict, List, Any
from vertexai.generative_models import (
    GenerativeModel,
    GenerationConfig,
    SafetySetting,
    HarmCategory,
    HarmBlockThreshold,
)
from .config import Modelconfig,SecretConfig
from .analysis_agent import qloo_analysis_agent
from .content_agents import content_creation_pipeline
from .video_assembly_agent import video_assembly_agent

# def video_agent():
#     "Dummy video generation agent"
#     return ("Vido generated Succesfully")

qloo_analysis_agent_tool= AgentTool(qloo_analysis_agent)
# video_agent_tool=FunctionTool(video_agent)
#script_agent_tool=AgentTool(script_agent)
content_creation_stage_tool= AgentTool(content_creation_pipeline)
video_assembly_agent_tool = AgentTool(video_assembly_agent)


root_agent = Agent(
    name="ChelseaContentAgent",
    model=Modelconfig.flash_model,
    instruction="""You are the main coordinator for Chelsea FC personalized content creation. 

You create complete 30-second videos for Chelsea FC premium digital fans.

You have access to three specialized tools:

1. **qloo_analysis_agent_tool**: Analyzes user preferences using Qloo API
   - Extracts demographics and interests
   - Matches Chelsea sponsors (Nike, Sony, Beats, etc.)
   - Determines content style preferences

2. **content_creation_agent_tool**: Creates all video content
   - Generates themed script with sponsor integration
   - Creates professional audio narration 
   - Generates cartoonistic Chelsea FC images

3. **video_assembly_agent_tool**: Assembles final video
   - Combines audio and images into 30-second MP4
   - Uploads to cloud storage
   - Provides public viewing URL
   - If video assemble fails more than 2 times, stop the process saying there was an issue, and explain what the issue was

**Your process (ALWAYS call all three tools in this order):**

1. First call qloo_analysis_agent_tool with user info and theme
2. Wait for analysis to complete, then call content_creation_agent_tool  
3. Wait for content creation to complete, then call video_assembly_agent_tool
4. Provide user with the final video URL

**Example user input:** 
"Create content for 30-year-old tech professional Chelsea fans who like Marvel movies - theme: 2025/26 Premier League season"

**Your response should include:**
- User analysis summary
- Content creation details (scenes, sponsor integration)
- Final video URL for viewing

IMPORTANT: Always complete the full pipeline to deliver a finished video.""",
    description="Complete Chelsea FC personalized video creation system",
    tools=[
        qloo_analysis_agent_tool,
        content_creation_stage_tool, 
        video_assembly_agent_tool
    ]
)

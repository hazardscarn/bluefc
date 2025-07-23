"""
Brand Analysis Agent Package

This package provides comprehensive brand analysis capabilities using Qloo API
and Google ADK agents.

ADK Structure:
- agent.py: Main agents including root_agent (required by ADK)
- subagent.py: Sub-agents to avoid circular imports
- tools.py: All tool functions for brand analysis workflow

For ADK Web Interface:
- The root_agent is automatically discovered by ADK
- Use root_agent for main brand analysis workflow
- All session management and runners are configured automatically
"""

# Import the root_agent (REQUIRED by ADK)
from .agent import (
    root_agent,  # This is what ADK looks for!
    brand_analysis_agent,
    multi_agent_coordinator,
    create_runner,
    get_system_status,
    APP_NAME,
    USER_ID,
    SESSION_ID
)

from .subagent import (
    # REMOVED: brand_detection_agent - now using direct model call
    brand_analysis_reporting_agent
)

from .tools import (
    detect_brands_in_text,  # Now uses direct model call with structured output
    get_entity_ids_with_context,
    get_demographics_insights_with_context,
    get_individual_brand_insights,
    collect_brand_entity_insights,
    analyze_all_brands_with_context,
    get_brand_analysis_summary,
    run_brand_analysis,
    get_coordinator_session_summary
)

__version__ = "1.0.0"
__author__ = "Brand Analysis Team"
__description__ = "Comprehensive brand analysis system using Qloo API and Google ADK"

# CRITICAL: root_agent must be exposed at package level for ADK discovery
__all__ = [
    # ADK REQUIRED
    "root_agent",  # This is what ADK looks for!
    
    # Main Agents
    "brand_analysis_agent",
    "multi_agent_coordinator",
    
    # Sub-agents
    # REMOVED: "brand_detection_agent",
    "brand_analysis_reporting_agent",
    
    # Tools
    "detect_brands_in_text",
    "get_entity_ids_with_context", 
    "get_demographics_insights_with_context",
    "get_individual_brand_insights",
    "collect_brand_entity_insights",
    "analyze_all_brands_with_context",
    "get_brand_analysis_summary",
    "run_brand_analysis",
    "get_coordinator_session_summary",
    
    # Configuration
    "create_runner",
    "get_system_status",
    "APP_NAME",
    "USER_ID", 
    "SESSION_ID"
]

# Print confirmation that root_agent is available
print(f"✅ [PACKAGE] brandagent package loaded - root_agent available: {root_agent.name}")
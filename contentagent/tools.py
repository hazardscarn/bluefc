# tools/chelsea_analysis_tools.py
"""
Chelsea FC Analysis Tools - Brand Matching and Style Analysis
These tools work with the existing Qloo insights to provide Chelsea-specific analysis
"""

import logging
import json
from typing import Dict, Any
from google.adk.tools import ToolContext
from vertexai.generative_models import GenerativeModel, GenerationConfig, HarmCategory, HarmBlockThreshold
from .config import Modelconfig

step_logger = logging.getLogger("AGENT_STEPS")
config = Modelconfig()

def match_sponsor_brand_function(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Match user brand preferences to the best Chelsea sponsor brand.
    
    Uses brand insights from Qloo to determine which Chelsea sponsor
    would resonate most with the user's brand affinities.
    
    Args:
        tool_context: ADK tool context containing brand insights in state
        
    Returns:
        Dict containing sponsor match results
    """
    step_logger.info("STEP 4: 🏟️ Matching Chelsea sponsors to user preferences...")
    
    # Get brand insights from state (set by get_insights_function)
    brand_insight = tool_context.state.get('brand_insight', '')
    detected_signals = tool_context.state.get('detected_signals', {})
    theme_detected = tool_context.state.get('theme_detected', {})
    # theme_value = theme_detected.get('theme', {}).get(0, "Chelsea FC CWC 2025 victory")
    theme_value = theme_detected.get('theme', ["Chelsea FC CWC 2025 victory"])[0]
    
    
    if not brand_insight:
        step_logger.error("   ❌ No brand insights found")
        return {"error": "No brand insights found. Run insights collection first."}
    
    step_logger.info(f"   📊 Analyzing {len(brand_insight)} chars of brand data")
    
    try:
        # Chelsea sponsors configuration
        chelsea_sponsors_config = get_chelsea_sponsors_config()
        
        # Use AI to analyze brand preferences and match to sponsors
        model = GenerativeModel(
            config.flash_model,
            generation_config=GenerationConfig(
                temperature=0.2,
                max_output_tokens=8000,  # Reduced from 6000 to prevent MAX_TOKENS error
                response_mime_type="application/json"
            ),
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        prompt = f"""Analyze user brand preferences and match to the best Chelsea FC sponsor.

USER BRAND INSIGHTS FROM QLOO:
{brand_insight}

USER DEMOGRAPHICS:
{json.dumps(detected_signals, indent=2)}

CHELSEA SPONSORS TO MATCH AGAINST:
{json.dumps(chelsea_sponsors_config, indent=2)}

TASK: Determine which sponsor would resonate most with this user based on their brand preferences.

Return concise JSON object (not array):
{{
    "selected_sponsor": "sponsor_name",
    "confidence_score": 0.85,
    "match_reasoning": "Brief reason why this sponsor matches",
    "integration_strategy": "How to integrate sponsor into the themed: {theme_value}video subtly in one scene",
}}

Keep responses brief to stay within token limits."""
        
        response = model.generate_content(prompt)
        
        # Robust JSON parsing to handle both objects and arrays
        try:
            sponsor_analysis = json.loads(response.text.strip())
            
            # Fix: Handle if AI returns a list instead of dict
            if isinstance(sponsor_analysis, list):
                if len(sponsor_analysis) > 0 and isinstance(sponsor_analysis[0], dict):
                    sponsor_analysis = sponsor_analysis[0]  # Take first item
                else:
                    # Fallback if list is empty or invalid
                    sponsor_analysis = {"selected_sponsor": "Nike", "confidence_score": 0.7}
            
            # Ensure it's a dictionary
            if not isinstance(sponsor_analysis, dict):
                sponsor_analysis = {"selected_sponsor": "Nike", "confidence_score": 0.7}
                
        except json.JSONDecodeError:
            # If JSON parsing fails, use default
            sponsor_analysis = {"selected_sponsor": "Nike", "confidence_score": 0.7, 
                              "match_reasoning": "Default fallback selection", 
                              "integration_strategy": "Standard brand integration"}
        
        selected_sponsor = sponsor_analysis.get('selected_sponsor', 'Nike')
        confidence = sponsor_analysis.get('confidence_score', 0.7)
        
        # Prepare comprehensive sponsor match data for state
        sponsor_match_data = {
            "selected_sponsor": selected_sponsor,
            "confidence_score": confidence,
            "match_reasoning": sponsor_analysis.get('match_reasoning', ''),
            "integration_strategy": sponsor_analysis.get('integration_strategy', ''),
            "sponsor_category": chelsea_sponsors_config.get(selected_sponsor, {}).get('category', ''),
        }
        
        logging.info(f"🎯 Saving Brand Sponsor to Context")
        # Save to tool context state
        tool_context.state['sponsor_match'] = sponsor_match_data
        
        step_logger.info(f"   ✅ Matched sponsor: {selected_sponsor} (confidence: {confidence:.0%})")
        step_logger.info(f"   🎯 Strategy: {sponsor_analysis.get('integration_strategy', '')[:50]}...")
        
        return {
            "success": True,
            "selected_sponsor": selected_sponsor,
            "confidence": confidence,
            "integration_strategy": sponsor_analysis.get('integration_strategy', ''),
            "message": f"Matched {selected_sponsor} with {confidence:.0%} confidence"
        }
        
    except Exception as e:
        step_logger.error(f"   ❌ Brand matching failed: {str(e)}")
        return {"error": f"Brand matching failed: {str(e)}"}

def analyze_content_style_function(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Analyze user's content style preferences from their movie and TV show preferences.
    
    Uses movie and TV insights from Qloo to determine what style of content
    the user prefers for video creation.
    
    Args:
        tool_context: ADK tool context containing entertainment insights
        
    Returns:
        Dict containing content style analysis results
    """
    step_logger.info("STEP 5: 🎬 Analyzing user content style preferences...")
    
    # Get entertainment insights from state (set by get_insights_function)
    movie_insight = tool_context.state.get('movie_insight', '')
    # Add other insights that might indicate content style
    artist_insight = tool_context.state.get('artist_insight', '')
    #tag_insight = tool_context.state.get('tag_insight', '')
    
    if not movie_insight and not artist_insight:
        step_logger.error("   ❌ No entertainment insights found")
        return {"error": "No entertainment insights found. Run insights collection first."}
    
    step_logger.info(f"   📊 Analyzing content from {len(movie_insight)} chars movie data")
    
    try:
        model = GenerativeModel(
            config.flash_model,
            generation_config=GenerationConfig(
                temperature=0.3,
                max_output_tokens=10000,
                response_mime_type="application/json"
            ),
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        prompt = f"""Analyze user's entertainment preferences to determine their ideal content style for Chelsea FC video creation.

MOVIE/TV INSIGHTS FROM QLOO:
{movie_insight}

MUSIC/ARTIST INSIGHTS:
{artist_insight}

TASK: Determine what style of video content this user would prefer based on their entertainment tastes.

Analyze:
1. Visual style preferences (cinematic, documentary, animated, action-packed, etc.)
2. Tone preferences (serious, playful, dramatic, upbeat, inspirational)
3. Pacing preferences (fast-paced, slow-burn, dynamic, rhythmic)
4. Narrative style (storytelling, highlights, emotional, technical)
5. Production style (high-budget feel, authentic, polished, raw)

Return JSON:
{{
    "visual_style": "primary visual style preference",
    "tone": "preferred tone for content",
    "pacing": "preferred pacing style", 
    "narrative_approach": "how to tell the story",
    "production_style": "production quality preference",
    "key_elements": ["element1", "element2", "element3"],
    "avoid_elements": ["avoid1", "avoid2"],
    "music_style": "preferred music/audio style",
    "emotional_drivers": ["emotion1", "emotion2"],
    "style_confidence": 0.85,
    "style_summary": "2-3 sentence summary of their content preferences"
}}"""
        
        response = model.generate_content(prompt)
        style_analysis = json.loads(response.text.strip())
        
        # Prepare comprehensive content style data for state
        content_style_data = {
            "visual_style": style_analysis.get('visual_style', 'cinematic'),
            "tone": style_analysis.get('tone', 'upbeat'),
            "pacing": style_analysis.get('pacing', 'dynamic'),
            "narrative_approach": style_analysis.get('narrative_approach', 'storytelling'),
            "production_style": style_analysis.get('production_style', 'polished'),
            "key_elements": style_analysis.get('key_elements', []),
            "avoid_elements": style_analysis.get('avoid_elements', []),
            "music_style": style_analysis.get('music_style', 'energetic'),
            "emotional_drivers": style_analysis.get('emotional_drivers', []),
            "content_themes": style_analysis.get('content_themes', []),
            "style_confidence": style_analysis.get('style_confidence', 0.8),
            "style_summary": style_analysis.get('style_summary', ''),
            "analysis_source": "movie_tv_music_preferences"
        }
        
        # Save to tool context state
        tool_context.state['content_style'] = content_style_data
        # tool_context.state['video_tone'] = style_analysis.get('tone', 'upbeat')
        # tool_context.state['video_pacing'] = style_analysis.get('pacing', 'dynamic')
        # tool_context.state['visual_style'] = style_analysis.get('visual_style', 'cinematic')
        
        step_logger.info(f"   ✅ Style: {style_analysis.get('visual_style')} + {style_analysis.get('tone')}")
        step_logger.info(f"   🎵 Music: {style_analysis.get('music_style')}")
        step_logger.info(f"   📈 Confidence: {style_analysis.get('style_confidence', 0.8):.0%}")
        
        return {
            "success": True,
            "visual_style": style_analysis.get('visual_style'),
            "tone": style_analysis.get('tone'),
            "pacing": style_analysis.get('pacing'),
            "confidence": style_analysis.get('style_confidence', 0.8),
            "style_summary": style_analysis.get('style_summary', ''),
            "message": f"Content style analyzed: {style_analysis.get('visual_style')} with {style_analysis.get('tone')} tone"
        }
        
    except Exception as e:
        step_logger.error(f"   ❌ Style analysis failed: {str(e)}")
        return {"error": f"Style analysis failed: {str(e)}"}

# ============================================================================
# CONFIGURATION DATA
# ============================================================================

def get_chelsea_sponsors_config():
    """Get complete Chelsea sponsors configuration."""
    return {
        "BingX": {"category": "Crypto", "integration": "digital_innovation"},
        "Cadbury": {"category": "Food", "integration": "sweet_victory"},
        "EA Sports": {"category": "Gaming", "integration": "fifa_esports"},
        "Fanatics": {"category": "Merchandise", "integration": "fan_gear"},
        "Linglong Tires": {"category": "Automotive", "integration": "performance_drive"},
        "Predator Energy": {"category": "Energy", "integration": "energy_boost"},
        "Beats by Dre": {"category": "Audio", "integration": "music_culture"},
        "Sony": {"category": "Technology", "integration": "entertainment_tech"},
        "Oman Air": {"category": "Travel", "integration": "global_journey"},
        "Hilton": {"category": "Hospitality", "integration": "luxury_hospitality"},
        "MSC Cruises": {"category": "Travel", "integration": "cruise_celebration"},
        "Singha Beer": {"category": "Beverages", "integration": "celebration_drinks"},
        "Coca-Cola": {"category": "Beverages", "integration": "happiness_sharing"},
    }
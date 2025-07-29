# tools/chelsea_content_tools.py
"""
Chelsea FC Content Creation Tools - Script, Audio, and Image Generation
These tools handle the actual content creation process
"""

import logging
import json
import uuid
import os
import tempfile
from typing import Dict, Any, List
from google.adk.tools import ToolContext
from vertexai.generative_models import GenerativeModel, GenerationConfig, HarmCategory, HarmBlockThreshold
from vertexai.preview.vision_models import ImageGenerationModel
import vertexai
from google.cloud import texttospeech
from .config import Modelconfig, SecretConfig,Settings
from .utils import storage_manager
import requests

step_logger = logging.getLogger("AGENT_STEPS")
config = Modelconfig()

# Initialize Vertex AI
vertexai.init(project=SecretConfig.get_google_cloud_project(), location=SecretConfig.get_google_cloud_location())



def generate_scenes_function(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Generate 5-6 scenes for a 30-second Chelsea FC video.
    Focused solely on scene structure, descriptions, and sponsor integration.
    
    Args:
        tool_context: ADK tool context containing analysis results
        
    Returns:
        Dict containing scene generation results
    """
    step_logger.info("STEP 7a: 🎬 Generating Chelsea FC scenes...")
    
    # Get required data from state
    content_style = tool_context.state.get('content_style', {})
    sponsor_match = tool_context.state.get('sponsor_match', {})
    theme_detected = tool_context.state.get('theme_detected', {})
    theme_value = theme_detected.get('theme', ["Chelsea FC CWC 2025 victory"])[0]
    
    if not content_style or not sponsor_match:
        step_logger.error("   ❌ Missing content style or sponsor match")
        return {"error": "Missing required analysis data. Run analysis first."}
    
    try:
        model = GenerativeModel(
            config.flash_model,
            generation_config=GenerationConfig(
                temperature=0.7,
                max_output_tokens=8000,
                response_mime_type="application/json"
            )
        )
        
        prompt = f"""Create a 30-second Chelsea FC video scene structure on the theme: {theme_value}

You need to understand the theme in detail.
    - If the theme was an event that happened, you need to learn and understand the event and create the scenes from that knowledge
        eg: Chelsea 2025 CWC win : You need to think about the Chelsea's journey in CWC and make the story and scenes around that
    - If the theme is an even to happen or start, you need to think about tthat in detail and create the story and scenes around that
        eg: Chelsea 2025/26 season : Think about what Chelsea will do in the next season, where they are now and what fans expects from the next season to build the story
    - The scenes/story built have to be around the theme
    - The scenes created should have a continuity flow and should be telling a story


USER PREFERENCES:
- Visual Style: {content_style.get('visual_style', 'cinematic')}
- Tone: {content_style.get('tone', 'celebratory')}
- Pacing: {content_style.get('pacing', 'dynamic')}

You need to subtly integrate this sponsor into atleast ONE of the scenes:
    Sponsor: {sponsor_match.get('selected_sponsor', 'Nike')}
    Integration Strategy but not limited to: {sponsor_match.get('integration_strategy', '')}
    Sector of sponsors business: {sponsor_match.get('sponsor_category', '')}


REQUIREMENTS:
- Create exactly 5-6 scenes
- Each scene 5-6 seconds long
- Total duration: 30 seconds
- Integrate sponsor subtly in atleast ONE scene
- Make it exciting for premium digital fans

FOR EACH SCENE PROVIDE:
- Scene number
- Duration (5-6 seconds)
- Scene description (what happens visually)
- Key elements (characters, actions, settings)
- Indicate which scene has brand integration

Return JSON:
{{
    "title": "Scene title",
    "total_duration": 30,
    "sponsor_integrated": "{sponsor_match.get('selected_sponsor', 'Nike')}",
    "scenes": [
        {{
            "scene_number": 1,
            "duration": 5,
            "scene_description": "Detailed description of what happens in this scene",
            "key_elements": ["element1", "element2", "element3"],
            "setting": "Where this scene takes place",
            "characters": ["character names if any"],
            "action": "Main action happening",
            "brand_integration": false
        }}
    ]
}}"""

        response = model.generate_content(prompt)
        scenes_data = json.loads(response.text.strip())
        
        # Save to state
        tool_context.state['scenes_data'] = scenes_data
        tool_context.state['scenes_created'] = True
        
        step_logger.info(f"   ✅ Generated {len(scenes_data.get('scenes', []))} scenes")
        
        return {
            "success": True,
            "scenes_created": True,
            "scene_count": len(scenes_data.get('scenes', [])),
            "title": scenes_data.get('title', ''),
            "sponsor_integrated": scenes_data.get('sponsor_integrated', ''),
            "message": f"Scenes generated successfully"
        }
        
    except Exception as e:
        step_logger.error(f"   ❌ Scene generation failed: {str(e)}")
        return {"error": f"Scene generation failed: {str(e)}"}


def generate_image_prompts_function(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Generate detailed image prompts from the created scenes.
    Focused solely on creating cartoonistic image generation prompts.
    
    Args:
        tool_context: ADK tool context containing scenes data
        
    Returns:
        Dict containing image prompt generation results
    """
    step_logger.info("STEP 7b: 🎨 Generating image prompts from scenes...")
    
    # Get scenes data from state
    scenes_data = tool_context.state.get('scenes_data', {})
    content_style = tool_context.state.get('content_style', {})
    
    if not scenes_data or not scenes_data.get('scenes'):
        step_logger.error("   ❌ No scenes data found")
        return {"error": "No scenes found. Generate scenes first."}
    
    try:
        model = GenerativeModel(
            config.flash_model,
            generation_config=GenerationConfig(
                temperature=0.8,
                max_output_tokens=25000,
                response_mime_type="application/json"
            )
        )
        
        # Create detailed player descriptions for reference
        player_descriptions = """
    ### **1. COLE PALMER (#10)"**
    PHYSICAL CHARACTERISTICS:
    Estimated Height: Average to slightly short for a professional athlete, with a notably slender build.
    Body Build: Lean and athletic. He has a wiry frame without significant muscle bulk, typical of a agile midfielder.
    Skin Tone: Fair and pale, with neutral to cool undertones.
    Age Appearance: Young adult, appearing to be in his late teens or early twenties.
    FACIAL FEATURES:
    Face Shape: A long and somewhat angular oval shape.
    Eyes: Light-colored (likely light brown or hazel), almond-shaped, and set with a focused, serious expression. They are a prominent feature in his face.
    Nose: Straight bridge with a defined, but not overly large, tip.
    Mouth/Lips: Thin lips, particularly the upper lip. His default expression is neutral, almost a slight pout.
    Jawline: Defined and angular, but not overly wide.
    Facial Hair: A sparse and light brown goatee and soul patch, with some light stubble on his chin and upper lip.
    HAIR DESCRIPTION:
    Color: Light brown or dark ash-blond.
    Style: A modern, short haircut, faded or clipped close on the sides and left slightly longer and textured on top.
    Texture: Appears fine and straight.

    ---

    ### **2. MARC CUCURELLA (#3)**
    PHYSICAL CHARACTERISTICS:
    Estimated Height: Average for a footballer, with a compact and low center of gravity.
    Body Build: Lean and athletic. He possesses a wiry strength, with defined but not bulky muscles, particularly noticeable in the arms and shoulders.
    Skin Tone: A warm, light olive or sun-kissed tan complexion, typical of a Mediterranean heritage.
    Age Appearance: Young, appearing to be in his early-to-mid 20s.
    FACIAL FEATURES:
    Face Shape: Primarily oval, but with an angular structure underneath.
    Eyes: Dark brown, almond-shaped, and expressive. They are framed by thick, dark, and well-defined eyebrows that are a prominent feature. His gaze is direct and calm.
    Nose: Prominent and straight-bridged with a distinct profile, slightly pointed at the tip. It's a key feature for a caricature.
    Mouth/Lips: Average in size with a neutral, closed-mouth expression. The lips are framed by his beard.
    Jawline: Defined and angular, though partially obscured by his beard.
    Facial Hair: A full but neatly maintained beard and mustache. The color is a consistent dark brown, matching his hair.
    HAIR DESCRIPTION:
    Color: Dark chocolate brown, appearing almost black in shadowed areas.
    Style: A long, voluminous, and wild mane of tight curls that extends to shoulder length. It frames his face and has a life of its own.
    Texture: Appears very thick, dense, and coarse, with tightly coiled curls.
    Distinctive Features: The hair is by far his most defining characteristic. For cartooning, it could be exaggerated as a large, bouncy "cloud" or "halo" of curls that moves dynamically with the character. It creates a unique and instantly recognizable silhouette.

    ---
    ### **3. REECE JAMES (#24) - "The Captain"**
    PHYSICAL CHARACTERISTICS:

    Estimated Height: Average; his powerful build makes him appear very solid and grounded.
    Body Build: Very athletic and powerful; a compact, muscular build with broad shoulders
    Skin Tone: Light brown with warm, golden undertones.
    Age Appearance: Young; appears to be in his early to mid-20s.
    FACIAL FEATURES:

    Face Shape: A soft square or rounded square shape; broad across the cheekbones.
    Eyes: Dark brown, almond-shaped. They have a calm, focused, and slightly gentle expression.
    Nose: Prominent and broad, particularly at the bridge and nostrils, with a rounded tip. This is a key defining feature.
    Mouth/Lips: Full and well-defined. The expression is neutral and composed, with the lips closed.
    Jawline: Strong and wide, but more rounded than sharply angular. Its shape is defined by his facial hair.
    Facial Hair: A neatly trimmed full beard that is dense and well-maintained. It covers his jawline, chin, and connects to a mustache.
    HAIR DESCRIPTION:

    Color: Dark brown to black.
    Style: A short, modern style; it appears to be faded or closely cropped on the sides, with more length and volume on top.
    Texture: Thick and textured, with tight, coarse curls or coils on top.
    Distinctive Features: The contrast between the tightly cropped sides and the textured, curly top is a key feature, along with his well-defined hairline.

    ---


 

    ### **8. ENZO FERNÁNDEZ (#8) - "The Argentine Bulldog"**
    Estimated Height: Average; he has a typical footballer's stature, not remarkably tall or short.
    Body Build: Athletic and lean. He has a well-defined but not overly bulky muscular frame, with broad shoulders and strong arms visible beneath the jersey.
    Skin Tone: A light, warm complexion with subtle olive undertones, appearing slightly tanned.
    Age Appearance: Young, appearing to be in his early 20s.
    FACIAL FEATURES:

    Face Shape: A soft square or round-oval. He has full cheeks combined with a structured chin, giving him a youthful yet defined look.
    Eyes: Deep-set, almond-shaped, and dark brown in color. They carry a serious, focused, and intense expression.
    Nose: Straight and well-proportioned to his face; it is not a dominant feature.
    Mouth/Lips: Full lips, with the bottom lip being noticeably fuller than the top. His expression is neutral to slightly pensive.
    Jawline: Moderately strong and defined, providing a solid base to his otherwise softer facial features.
    Facial Hair: Clean-shaven.
    HAIR DESCRIPTION:

    Color: Dark brown, with some lighter brown or dark blonde highlights concentrated in the fringe.
    Style: A modern, textured crop or bowl cut. The defining feature is a thick, heavy fringe that is cut bluntly and falls straight across his forehead.
    Texture: Appears thick and dense with a slight natural wave, giving it volume and a piecey look.
    Distinctive Features: The combination of his heavy fringe, intense eyes, and highly visible tattoos creates a very distinct and modern look. The neck tattoos are particularly prominent: a swallow, the year "2001," and a flower are key identifiers. His arms feature full tattoo sleeves, which should be included as a major design element.

        """
        
        scenes_json = json.dumps(scenes_data.get('scenes', []), indent=2)
        
        prompt = f"""Create detailed cartoonistic image generation prompts for each scene.

SCENES TO CONVERT:
{scenes_json}

PLAYER REFERENCE (use only if players appear in scenes):
{player_descriptions}

REQUIREMENTS FOR EACH IMAGE PROMPT:
- Cartoonistic/comic book style
- Still image (single shot, not multiple shots)
- Extremely detailed descriptions of every element
- Include character appearances if players are featured
- 16:9 aspect ratio suitable for video
- Vibrant Chelsea blue and white colors
- {content_style.get('visual_style', 'cinematic')} composition
- High quality, professional illustration style

FOR EACH SCENES:
- The description for image of each scene have to be as detailed as possible to every point including every character
- Image generation prompt have to be a still image prompt of a single shot. You can't have image prompt for multiple shots 
- Focus on visual elements, colors, composition
- Include lighting and mood descriptions
- Specify cartoonistic style clearly
- Make sure to add that the images have to cartoonistic/comic style
- If characters are in the scene, make detailed instruction on each characters apperance as realistic as it is in cartoonistic style
- Use player description provided only in the scene and use this details to create detailed prompt of the corresponding player
- If players are used in scene , all players are in blue jersey, except for GK in black jersey

Return JSON:
{{
    "image_prompts": [
        {{
            "scene_number": 1,
            "prompt": "Extremely detailed cartoonistic image prompt for Vertex AI Imagen..."
        }}
    ]
}}"""

        response = model.generate_content(prompt)
        prompts_data = json.loads(response.text.strip())
        
        # Save to state
        tool_context.state['image_prompts_data'] = prompts_data
        tool_context.state['image_prompts'] = [p['prompt'] for p in prompts_data.get('image_prompts', [])]
        tool_context.state['image_prompts_created'] = True
        
        step_logger.info(f"   ✅ Generated {len(prompts_data.get('image_prompts', []))} image prompts")
        
        return {
            "success": True,
            "image_prompts_created": True,
            "prompt_count": len(prompts_data.get('image_prompts', [])),
            "message": f"Image prompts generated successfully"
        }
        
    except Exception as e:
        step_logger.error(f"   ❌ Image prompt generation failed: {str(e)}")
        return {"error": f"Image prompt generation failed: {str(e)}"}


def generate_audio_scripts_function(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Generate audio narration scripts from the created scenes.
    Focused solely on creating perfect audio content for each scene.
    
    Args:
        tool_context: ADK tool context containing scenes data
        
    Returns:
        Dict containing audio script generation results
    """
    step_logger.info("STEP 7c: 🎤 Generating audio scripts from scenes...")
    
    # Get scenes data from state
    scenes_data = tool_context.state.get('scenes_data', {})
    content_style = tool_context.state.get('content_style', {})
    
    if not scenes_data or not scenes_data.get('scenes'):
        step_logger.error("   ❌ No scenes data found")
        return {"error": "No scenes found. Generate scenes first."}
    
    try:
        model = GenerativeModel(
            config.flash_model,
            generation_config=GenerationConfig(
                temperature=0.7,
                max_output_tokens=6000,
                response_mime_type="application/json"
            )
        )
        
        scenes_json = json.dumps(scenes_data.get('scenes', []), indent=2)
        
        prompt = f"""Create perfect audio narration scripts for each scene.

SCENES TO NARRATE:
{scenes_json}

AUDIO REQUIREMENTS:
- Each script should be atleast 5-8 seconds of spoken content
- Perfect word count for timing (roughly 15-20 words per scene)
- Exciting and energetic tone matching {content_style.get('tone', 'celebratory')}
- Professional sports commentary style
- Build excitement and engagement
- Flow smoothly from scene to scene
- It is very important that you add silence, sxcitement etc. in the script with ....., !, and other ways you can express in words
- The audio script is passed to a TTS converter. So the tone and energy you set should work well for a TTS tool

WORD COUNT GUIDE:
- 5 seconds = 12-15 words
- 6 seconds = 15-17 words  
- 7 seconds = 17-20 words

FOR EACH SCENE CREATE:
- Concise, punchy narration text
- Perfectly timed for the scene duration
- Exciting sports commentary style
- Natural pronunciation and flow

Return JSON:
{{
    "audio_scripts": [
        {{
            "scene_number": 1,
            "duration": 5,
            "script": "Brief exciting narration text here",
            "word_count": 12
        }}
    ]
}}"""

        response = model.generate_content(prompt)
        audio_data = json.loads(response.text.strip())
        
        # Save to state
        tool_context.state['audio_scripts_data'] = audio_data
        tool_context.state['audio_scripts'] = [s['script'] for s in audio_data.get('audio_scripts', [])]
        tool_context.state['audio_scripts_created'] = True
        
        step_logger.info(f"   ✅ Generated {len(audio_data.get('audio_scripts', []))} audio scripts")
        
        return {
            "success": True,
            "audio_scripts_created": True,
            "script_count": len(audio_data.get('audio_scripts', [])),
            "total_estimated_duration": sum(s.get('duration', 5) for s in audio_data.get('audio_scripts', [])),
            "message": f"Audio scripts generated successfully"
        }
        
    except Exception as e:
        step_logger.error(f"   ❌ Audio script generation failed: {str(e)}")
        return {"error": f"Audio script generation failed: {str(e)}"}


def generate_audio_function(tool_context: ToolContext) -> Dict[str, Any]:
    """Generate audio narration from script using Google Text-to-Speech."""
    step_logger.info("🎤 AUDIO AGENT CALLED - Starting audio generation...")
    
    try:
        from google.cloud import texttospeech
        step_logger.info("✅ Google TTS imported successfully")
    except ImportError as e:
        step_logger.error(f"❌ Google TTS import failed: {e}")
        return {
            "error": "Google Cloud TTS not available. Run: pip install google-cloud-texttospeech",
            "success": False
        }
    
    # Get script data from state
    audio_scripts = tool_context.state.get('audio_scripts', [])
    script_data = tool_context.state.get('script_data', {})
    
    step_logger.info(f"📝 Found {len(audio_scripts)} audio scripts to process")
    step_logger.info(f"📊 Script data keys: {list(script_data.keys())}")
    
    if not audio_scripts:
        step_logger.error("❌ No audio scripts found in state")
        return {
            "error": "No audio scripts found. Generate script first.",
            "available_keys": list(tool_context.state.keys()),
            "success": False
        }
    
    try:
        # Initialize Google TTS client
        tts_client = texttospeech.TextToSpeechClient()
        
        # UPDATED: Your preferred UK voices first, then fallbacks
        voice_options = [
            # YOUR PREFERRED VOICES (Chirp3-HD UK male voices)
            'en-GB-Chirp3-HD-Algenib',    # Your #1 choice
            'en-GB-Chirp3-HD-Enceladus',  # Your #2 choice  
            'en-GB-Chirp3-HD-Puck',       # Your #3 choice
            
            # Additional excellent UK Chirp3-HD male voices
            'en-GB-Chirp3-HD-Fenrir',     # Dynamic, powerful
            'en-GB-Chirp3-HD-Orus',       # Strong, commanding
            'en-GB-Chirp3-HD-Charon',     # Dramatic
            'en-GB-Chirp3-HD-Schedar',    # Authoritative
            
            # Fallback to older UK voices
            'en-GB-Studio-C',             # Try Studio C (often more dramatic)
            'en-GB-Studio-B',             # Fallback to Studio B
            'en-GB-Neural2-D',            # Neural2 fallback
            'en-GB-Neural2-B',            # Another Neural2 option
            'en-GB-Standard-D',           # Standard fallback
            
            # Last resort: US voices
            'en-US-Studio-O',             # Deep US voice
            'en-US-Chirp3-HD-Orus'        # US Chirp3 fallback
        ]
        
        voice_used = None
        voice = None
        
        step_logger.info("🎯 Trying your preferred UK voices...")
        
        # Try each voice option until one works
        for i, voice_name in enumerate(voice_options, 1):
            try:
                # Determine language code based on voice name
                language_code = "en-GB" if voice_name.startswith('en-GB') else "en-US"
                
                voice = texttospeech.VoiceSelectionParams(
                    language_code=language_code,
                    name=voice_name
                )
                
                # Test the voice with a short synthesis to make sure it works
                test_input = texttospeech.SynthesisInput(text="Test")
                test_audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3
                )
                
                # Try to synthesize - this will fail if voice doesn't exist
                test_response = tts_client.synthesize_speech(
                    input=test_input,
                    voice=voice,
                    audio_config=test_audio_config
                )
                
                # If we get here, the voice works!
                voice_used = voice_name
                is_uk = language_code == "en-GB"
                is_preferred = i <= 3  # Your top 3 choices
                is_chirp3 = 'Chirp3-HD' in voice_name
                
                # Log which voice we're using with preference indication
                preference_note = ""
                if voice_name == 'en-GB-Chirp3-HD-Algenib':
                    preference_note = " (🥇 YOUR #1 CHOICE!)"
                elif voice_name == 'en-GB-Chirp3-HD-Enceladus':
                    preference_note = " (🥈 YOUR #2 CHOICE!)"
                elif voice_name == 'en-GB-Chirp3-HD-Puck':
                    preference_note = " (🥉 YOUR #3 CHOICE!)"
                elif is_preferred:
                    preference_note = " (⭐ PREFERRED)"
                elif is_chirp3:
                    preference_note = " (🚀 CHIRP3-HD)"
                elif is_uk:
                    preference_note = " (🇬🇧 UK)"
                else:
                    preference_note = " (🇺🇸 US FALLBACK)"
                
                step_logger.info(f"✅ Using voice: {voice_name}{preference_note}")
                break
                
            except Exception as e:
                step_logger.warning(f"Voice #{i} {voice_name} not available: {e}")
                continue
        
        if not voice_used:
            step_logger.error("❌ No voices available")
            return {"error": "No UK or US voices available"}

        # OPTIMIZED: Audio configuration based on voice type
        if 'Chirp3-HD' in voice_used:
            # Chirp3-HD voices need less pitch adjustment
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=0.95,      # Slightly slower for dramatic effect
                #pitch=-0.5,             # Chirp3-HD needs less adjustment
                volume_gain_db=1.5,     # Boost for presence
                sample_rate_hertz=24000  # High quality
            )
            step_logger.info("   🚀 Using Chirp3-HD optimized settings")
        else:
            # Neural2/Studio/Standard voices need more pitch adjustment
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=0.95,     # Slightly slower for dramatic effect
                pitch=-1.0,            # Lower pitch for authority
                volume_gain_db=1.5,    # Boost for presence
                sample_rate_hertz=24000  # High quality
            )
            step_logger.info("   ⚙️ Using Neural2/Studio optimized settings")

        generated_audio_data = []
        audio_urls = []
        
        # Generate audio for each scene
        for i, script_text in enumerate(audio_scripts, 1):
            if not script_text.strip():
                continue
                
            # Generate audio
            synthesis_input = texttospeech.SynthesisInput(text=script_text)
            
            response = tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # Save audio to GCS
            audio_filename = f"scene_{i}_audio_{uuid.uuid4().hex[:8]}.mp3"
            
            if storage_manager:
                upload_result = storage_manager.upload_binary(
                    content=response.audio_content,
                    folder="audio",
                    filename=audio_filename,
                    content_type="audio/mpeg"
                )
                
                if upload_result["status"] == "success":
                    audio_url = upload_result["public_url"]
                    audio_urls.append(audio_url)
                    
                    generated_audio_data.append({
                        "scene_number": i,
                        "script_text": script_text,
                        "audio_url": audio_url,
                        "gcs_url": upload_result["gcs_url"],
                        "filename": audio_filename,
                        "voice_used": voice_used,
                        "voice_type": "Chirp3-HD" if 'Chirp3-HD' in voice_used else "Neural2/Studio/Standard",
                        "duration_estimate": len(script_text.split()) * 0.5  # Rough estimate
                    })
                    
                    step_logger.info(f"   ✅ Scene {i} audio generated")
                else:
                    step_logger.error(f"   ❌ Failed to upload scene {i} audio")
            else:
                step_logger.error("   ❌ Storage manager not available")
        
        # Save comprehensive audio data to state
        voice_quality = "Premium Chirp3-HD" if 'Chirp3-HD' in voice_used else "Premium Neural2/Studio"
        user_preference_met = voice_used in ['en-GB-Chirp3-HD-Algenib', 'en-GB-Chirp3-HD-Enceladus', 'en-GB-Chirp3-HD-Puck']
        
        audio_data = {
            "audio_generated": True,
            "scene_count": len(generated_audio_data),
            "audio_files": generated_audio_data,
            "audio_urls": audio_urls,
            "voice_used": voice_used,
            "voice_quality": voice_quality,
            "user_preference_met": user_preference_met,
            "accent": "UK English" if 'en-GB' in voice_used else "US English",
            "total_estimated_duration": sum(item["duration_estimate"] for item in generated_audio_data),
            "generation_timestamp": str(uuid.uuid4())[:8]
        }
        
        tool_context.state['audio_data'] = audio_data
        tool_context.state['audio_urls'] = audio_urls
        tool_context.state['audio_generated'] = True
        
        step_logger.info(f"   🏆 Generated audio for {len(generated_audio_data)} scenes")
        step_logger.info(f"   🎭 Voice: {voice_used} ({voice_quality})")
        step_logger.info(f"   ⏱️ Duration: ~{audio_data['total_estimated_duration']:.1f}s")
        step_logger.info(f"   {'🎯 USER PREFERENCE MET!' if user_preference_met else '📋 Using fallback voice'}")
        
        return {
            "success": True,
            "audio_generated": True,
            "scene_count": len(generated_audio_data),
            "total_duration": audio_data['total_estimated_duration'],
            "voice_used": voice_used,
            "voice_quality": voice_quality,
            "user_preference_met": user_preference_met,
            "message": f"Audio generated for {len(generated_audio_data)} scenes with {voice_used}"
        }
        
    except Exception as e:
        step_logger.error(f"   ❌ Audio generation failed: {str(e)}")
        return {"error": f"Audio generation failed: {str(e)}"}





def generate_scene_images_function(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Generate cartoonistic images for each scene using Vertex AI Imagen with retry logic.
    
    Args:
        tool_context: ADK tool context containing image prompts
        
    Returns:
        Dict containing image generation results
    """
    step_logger.info("STEP 8b: 🎨 Generating cartoonistic scene images...")
    
    # Get image prompts from state
    image_prompts = tool_context.state.get('image_prompts', [])
    content_style = tool_context.state.get('content_style', {})
    
    if not image_prompts:
        step_logger.error("   ❌ No image prompts found")
        return {"error": "No image prompts found. Generate script first."}
    
    step_logger.info(f"   🎨 Generating images for {len(image_prompts)} scenes")
    
    try:
        # Initialize Imagen model
        image_model = ImageGenerationModel.from_pretrained(config.imagen4_ultra)
        
        # Base style for all images
        base_style = f"""
        cartoonistic style, vibrant colors, Chelsea FC theme, 
        blue and white colors, football/soccer atmosphere,
        {content_style.get('visual_style', 'cinematic')} composition,
        high quality, detailed, professional illustration
        """
        
        generated_images_data = []
        image_urls = []
        
        # Generate image for each scene
        for i, prompt in enumerate(image_prompts, 1):
            if not prompt.strip():
                continue
            
            # Enhance prompt with Chelsea FC style
            enhanced_prompt = f"{prompt}, {base_style}"
            
            # Retry logic for image generation
            max_retries = 2
            success = False
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    step_logger.info(f"   🎯 Scene {i} - Attempt {attempt + 1}/{max_retries}")
                    
                    # Generate image using Imagen with optimized parameters
                    response = image_model.generate_images(
                        prompt=enhanced_prompt,
                        number_of_images=1,
                        aspect_ratio="16:9",  # Video aspect ratio
                        safety_filter_level="allow_most",
                        person_generation="allow_adult",
                        # Additional parameters for better quality
                        add_watermark=False,  # Clean images
                        guidance_scale=10,    # Good balance of prompt adherence
                        seed=None            # Random seed for variety
                    )

                    step_logger.info(f"   📝 Scene {i} Prompt: {enhanced_prompt}")
                    
                    if response and response.images and len(response.images) > 0:
                        image = response.images[0]
                        
                        # Validate image before processing
                        if not validate_imagen_response(image):
                            raise ValueError(f"Invalid image response for scene {i}")
                        
                        # Convert PIL image to bytes with proper format handling
                        img_bytes = convert_pil_to_bytes(image._pil_image)
                        
                        if not img_bytes:
                            raise ValueError(f"Failed to convert image to bytes for scene {i}")
                        
                        # Save image to GCS
                        image_filename = f"scene_{i}_image_{uuid.uuid4().hex[:8]}.png"
                        
                        if storage_manager:
                            upload_result = storage_manager.upload_binary(
                                content=img_bytes,
                                folder="images",
                                filename=image_filename,
                                content_type="image/png"
                            )
                            
                            if upload_result["status"] == "success":
                                image_url = upload_result["public_url"]
                                image_urls.append(image_url)
                                
                                generated_images_data.append({
                                    "scene_number": i,
                                    "prompt": prompt,
                                    "enhanced_prompt": enhanced_prompt,
                                    "image_url": image_url,
                                    "gcs_url": upload_result["gcs_url"],
                                    "filename": image_filename,
                                    "aspect_ratio": "16:9",
                                    "attempts_used": attempt + 1,
                                    "generation_success": True
                                })
                                
                                step_logger.info(f"   ✅ Scene {i} image generated successfully on attempt {attempt + 1}")
                                success = True
                                break
                            else:
                                raise ValueError(f"Failed to upload: {upload_result.get('error', 'Unknown upload error')}")
                        else:
                            raise ValueError("Storage manager not available")
                    else:
                        raise ValueError(f"No image generated in response for scene {i}")
                        
                except Exception as e:
                    last_error = str(e)
                    step_logger.warning(f"   ⚠️ Scene {i} attempt {attempt + 1} failed: {last_error}")
                    
                    # If this isn't the last attempt, wait a bit before retrying
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(2)  # Wait 2 seconds before retry
                        step_logger.info(f"   🔄 Retrying scene {i} in 2 seconds...")
            
            # If all attempts failed, log and continue with next scene
            if not success:
                step_logger.error(f"   ❌ Scene {i} failed after {max_retries} attempts. Last error: {last_error}")
                
                # Add failed scene info for tracking
                generated_images_data.append({
                    "scene_number": i,
                    "prompt": prompt,
                    "enhanced_prompt": enhanced_prompt,
                    "image_url": None,
                    "gcs_url": None,
                    "filename": None,
                    "aspect_ratio": "16:9",
                    "attempts_used": max_retries,
                    "generation_success": False,
                    "error": last_error
                })
        
        # Count successful generations
        successful_scenes = [item for item in generated_images_data if item.get("generation_success", False)]
        failed_scenes = [item for item in generated_images_data if not item.get("generation_success", False)]
        
        # Save comprehensive images data to state
        images_data = {
            "images_generated": len(successful_scenes) > 0,
            "total_scenes": len(image_prompts),
            "successful_scenes": len(successful_scenes),
            "failed_scenes": len(failed_scenes),
            "scene_count": len(successful_scenes),
            "image_files": generated_images_data,
            "image_urls": image_urls,
            "style_applied": base_style,
            "model_used": config.imagen4_ultra,
            "generation_timestamp": str(uuid.uuid4())[:8],
            "retry_logic_used": True
        }
        
        tool_context.state['images_data'] = images_data
        tool_context.state['image_urls'] = image_urls
        tool_context.state['images_generated'] = len(successful_scenes) > 0
        
        step_logger.info(f"   🏆 Generated images for {len(successful_scenes)}/{len(image_prompts)} scenes")
        if failed_scenes:
            step_logger.warning(f"   ⚠️ {len(failed_scenes)} scenes failed after retries")
        step_logger.info(f"   🎨 Style: Cartoonistic Chelsea FC theme")
        
        return {
            "success": len(successful_scenes) > 0,
            "images_generated": len(successful_scenes) > 0,
            "total_scenes": len(image_prompts),
            "successful_scenes": len(successful_scenes),
            "failed_scenes": len(failed_scenes),
            "scene_count": len(successful_scenes),
            "style": "cartoonistic_chelsea_fc",
            "model_used": config.imagen4_ultra,
            "message": f"Images generated for {len(successful_scenes)}/{len(image_prompts)} scenes with retry logic"
        }
        
    except Exception as e:
        step_logger.error(f"   ❌ Image generation system failed: {str(e)}")
        return {"error": f"Image generation system failed: {str(e)}"}


def validate_imagen_response(image) -> bool:
    """
    Validate that the Imagen response contains a valid image.
    
    Args:
        image: Imagen response image object
        
    Returns:
        bool: True if image is valid
    """
    try:
        if not hasattr(image, '_pil_image'):
            return False
        
        pil_image = image._pil_image
        
        # Check if image has valid dimensions
        if not pil_image.size or pil_image.size[0] <= 0 or pil_image.size[1] <= 0:
            return False
        
        # Check if image is not corrupted
        try:
            pil_image.load()  # This will raise an exception if image is corrupted
        except Exception:
            return False
        
        return True
        
    except Exception as e:
        step_logger.warning(f"Image validation failed: {e}")
        return False


def convert_pil_to_bytes(pil_image) -> bytes:
    """
    Convert PIL image to bytes with proper format handling.
    
    Args:
        pil_image: PIL Image object
        
    Returns:
        bytes: Image as PNG bytes or None if conversion fails
    """
    try:
        import io
        
        # Convert to RGB if necessary (handles any color mode issues)
        if pil_image.mode not in ['RGB', 'RGBA']:
            if pil_image.mode == 'P':
                # Handle palette mode
                pil_image = pil_image.convert('RGBA')
            else:
                pil_image = pil_image.convert('RGB')
        
        # Create byte buffer
        img_byte_arr = io.BytesIO()
        
        # Save as PNG with optimization
        pil_image.save(
            img_byte_arr, 
            format='PNG', 
            optimize=True,
            compress_level=6  # Good compression without too much processing time
        )
        
        # Get bytes
        img_bytes = img_byte_arr.getvalue()
        
        # Validate that we have actual image data
        if len(img_bytes) < 1000:  # PNG header + some data should be at least 1KB
            step_logger.warning(f"Generated image seems too small: {len(img_bytes)} bytes")
            return None
        
        step_logger.info(f"   📦 Image converted to {len(img_bytes):,} bytes")
        return img_bytes
        
    except Exception as e:
        step_logger.error(f"   ❌ Failed to convert PIL image to bytes: {e}")
        return None









# def generate_scene_images_function(tool_context: ToolContext) -> Dict[str, Any]:
#     """
#     Generate cartoonistic images for each scene using Vertex AI Imagen.
    
#     Args:
#         tool_context: ADK tool context containing image prompts
        
#     Returns:
#         Dict containing image generation results
#     """
#     step_logger.info("STEP 8b: 🎨 Generating cartoonistic scene images...")
    
#     # Get image prompts from state
#     image_prompts = tool_context.state.get('image_prompts', [])
#     content_style = tool_context.state.get('content_style', {})
    
#     if not image_prompts:
#         step_logger.error("   ❌ No image prompts found")
#         return {"error": "No image prompts found. Generate script first."}
    
#     step_logger.info(f"   🎨 Generating images for {len(image_prompts)} scenes")
    
#     try:
#         # Initialize Imagen model
#         image_model = ImageGenerationModel.from_pretrained(config.imagen4_ultra)
        
#         # Base style for all images
#         base_style = f"""
#         cartoonistic style, vibrant colors, Chelsea FC theme, 
#         blue and white colors, football/soccer atmosphere,
#         {content_style.get('visual_style', 'cinematic')} composition,
#         high quality, detailed, professional illustration
#         """
        
#         generated_images_data = []
#         image_urls = []
        
#         # Generate image for each scene
#         for i, prompt in enumerate(image_prompts, 1):
#             if not prompt.strip():
#                 continue
            
#             # Enhance prompt with Chelsea FC style
#             enhanced_prompt = f"{prompt}, {base_style}"
            
#             try:
#                 # Generate image using Imagen
#                 response = image_model.generate_images(
#                     prompt=enhanced_prompt,
#                     number_of_images=1,
#                     aspect_ratio="16:9",  # Video aspect ratio
#                     safety_filter_level="allow_most",
#                     person_generation="allow_adult"
#                 )

#                 logging.info(f"Scene {i} Prompt: {enhanced_prompt}")
                
#                 if response.images:
#                     image = response.images[0]
                    
#                     # Convert to bytes for storage
#                     image_bytes = image._pil_image.tobytes()
                    
#                     # Save image to GCS
#                     image_filename = f"scene_{i}_image_{uuid.uuid4().hex[:8]}.png"
                    
#                     if storage_manager:
#                         # Convert PIL image to bytes properly
#                         import io
#                         img_byte_arr = io.BytesIO()
#                         image._pil_image.save(img_byte_arr, format='PNG')
#                         img_byte_arr = img_byte_arr.getvalue()
                        
#                         upload_result = storage_manager.upload_binary(
#                             content=img_byte_arr,
#                             folder="images",
#                             filename=image_filename,
#                             content_type="image/png"
#                         )
                        
#                         if upload_result["status"] == "success":
#                             image_url = upload_result["public_url"]
#                             image_urls.append(image_url)
                            
#                             generated_images_data.append({
#                                 "scene_number": i,
#                                 "prompt": prompt,
#                                 "enhanced_prompt": enhanced_prompt,
#                                 "image_url": image_url,
#                                 "gcs_url": upload_result["gcs_url"],
#                                 "filename": image_filename,
#                                 "aspect_ratio": "16:9"
#                             })
                            
#                             step_logger.info(f"   ✅ Scene {i} image generated")
#                         else:
#                             step_logger.error(f"   ❌ Failed to upload scene {i} image")
#                     else:
#                         step_logger.error("   ❌ Storage manager not available")
#                 else:
#                     step_logger.error(f"   ❌ No image generated for scene {i}")
                    
#             except Exception as e:
#                 step_logger.error(f"   ❌ Failed to generate image for scene {i}: {str(e)}")
#                 continue
        
#         # Save comprehensive images data to state
#         images_data = {
#             "images_generated": True,
#             "scene_count": len(generated_images_data),
#             "image_files": generated_images_data,
#             "image_urls": image_urls,
#             "style_applied": base_style,
#             "model_used": config.imagen4_fast,
#             "generation_timestamp": str(uuid.uuid4())[:8]
#         }
        
#         tool_context.state['images_data'] = images_data
#         tool_context.state['image_urls'] = image_urls
#         tool_context.state['images_generated'] = True
        
#         step_logger.info(f"   ✅ Generated images for {len(generated_images_data)} scenes")
#         step_logger.info(f"   🎨 Style: Cartoonistic Chelsea FC theme")
        
#         return {
#             "success": True,
#             "images_generated": True,
#             "scene_count": len(generated_images_data),
#             "style": "cartoonistic_chelsea_fc",
#             "model_used": config.imagen4_fast,
#             "message": f"Images generated for {len(generated_images_data)} scenes"
#         }
        
#     except Exception as e:
#         step_logger.error(f"   ❌ Image generation failed: {str(e)}")
#         return {"error": f"Image generation failed: {str(e)}"}

# # ============================================================================
# CONFIGURATION FUNCTIONS
# ============================================================================

def get_content_tools_config() -> dict:
    """Get configuration for content creation tools."""
    return {
        "tools": {
            "theme_search": "Research video themes and context",
            "script_generation": "Create 30-second scripts with sponsor integration",
            "audio_generation": "Convert scripts to professional narration",
            "image_generation": "Create cartoonistic scenes with Vertex AI Imagen"
        },
        "models_used": {
            "script": config.flash_model,
            "theme_research": config.flash_model,
            "audio": "Google TTS",
            "images": config.imagen4_fast
        },
        "storage": {
            "audio_format": "MP3",
            "image_format": "PNG", 
            "aspect_ratio": "16:9",
            "storage_service": "Google Cloud Storage"
        },
        "content_specs": {
            "video_duration": "30 seconds",
            "scene_count": "5-6 scenes",
            "scene_duration": "5-6 seconds each",
            "style": "cartoonistic_chelsea_fc",
            "sponsor_integration": "subtle_single_scene"
        }
    }
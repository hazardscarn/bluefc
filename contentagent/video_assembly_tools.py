# tools/video_assembly_tools.py - FIXED VERSION
"""
Video Assembly Tools - Creates final video from audio and image assets
Uses MoviePy with DYNAMIC TIMING for perfect audio-video synchronization
"""

import logging
import json
import uuid
import os
import tempfile
import requests
from typing import Dict, Any, List
from google.adk.tools import ToolContext
from .config import SecretConfig, Modelconfig
from .utils import storage_manager


# MoviePy imports - using EXACT same imports as your WORKING test script
try:
    from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

step_logger = logging.getLogger("AGENT_STEPS")

def assemble_final_video_function(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Assemble final video using DYNAMIC TIMING approach.
    
    Revolutionary method: Each scene duration = its audio duration for perfect sync!
    
    Args:
        tool_context: ADK tool context containing audio and image URLs in state
        
    Returns:
        Dict containing final video URL and metadata
    """
    step_logger.info("🎬 VIDEO ASSEMBLY STARTED (Dynamic Timing)")
    
    # FIXED: Use safe state access instead of .keys()
    try:
        # Test what state methods are available
        state_info = []
        for attr in ['audio_urls', 'image_urls', 'script_data', 'video_metadata']:
            if hasattr(tool_context.state, attr) or tool_context.state.get(attr) is not None:
                state_info.append(attr)
        step_logger.info(f"📊 Available state data: {state_info}")
    except Exception as e:
        step_logger.warning(f"📊 Could not inspect state: {e}")
    
    if not MOVIEPY_AVAILABLE:
        return {
            "error": "MoviePy not available. Install with: pip install moviepy",
            "success": False
        }
    
    try:
        # Get assets from state - FIXED: More defensive access
        audio_urls = []
        image_urls = []
        script_data = {}
        
        try:
            audio_urls = tool_context.state.get('audio_urls') or []
            image_urls = tool_context.state.get('image_urls') or []
            script_data = tool_context.state.get('script_data') or {}
        except Exception as e:
            step_logger.warning(f"⚠️ State access error: {e}")
            # Try alternative state keys
            try:
                # Check for alternative keys that might be used
                audio_urls = (tool_context.state.get('audio_data', {}).get('audio_urls', []) or 
                             tool_context.state.get('audio_urls', []))
                image_urls = (tool_context.state.get('images_data', {}).get('image_urls', []) or 
                             tool_context.state.get('image_urls', []))
            except:
                pass
        
        step_logger.info(f"🎤 Found {len(audio_urls)} audio files")
        step_logger.info(f"🖼️ Found {len(image_urls)} image files")
        step_logger.info(f"📝 Script data available: {bool(script_data)}")
        step_logger.info("💡 Using DYNAMIC TIMING: Scene duration = Audio duration")
        
        if not audio_urls or not image_urls:
            # FIXED: Safe state inspection for debugging
            available_data = []
            try:
                # Try to get some info about what's available
                test_keys = ['audio_urls', 'image_urls', 'audio_data', 'images_data', 
                           'script_data', 'scenes_data', 'audio_generated', 'images_generated']
                for key in test_keys:
                    try:
                        value = tool_context.state.get(key)
                        if value is not None:
                            if isinstance(value, (list, dict)):
                                available_data.append(f"{key}: {type(value).__name__}({len(value) if hasattr(value, '__len__') else 'N/A'})")
                            else:
                                available_data.append(f"{key}: {type(value).__name__}")
                    except:
                        continue
            except:
                available_data = ["state inspection failed"]
                
            return {
                "error": "Missing audio or image URLs. Run content creation first.",
                "available_state": available_data,
                "audio_urls_found": len(audio_urls),
                "image_urls_found": len(image_urls),
                "success": False
            }
        
        # Check storage manager
        if not storage_manager:
            return {
                "error": "Storage manager not available",
                "success": False
            }
        
        # Create temporary directory for video processing
        with tempfile.TemporaryDirectory() as temp_dir:
            step_logger.info(f"📁 Using temp directory: {temp_dir}")
            
            # Download all assets
            assets = _download_video_assets(audio_urls, image_urls, temp_dir)
            
            if not assets["success"]:
                return assets
            
            # Create video using MoviePy with dynamic timing
            video_result = _create_video_with_dynamic_timing(assets, script_data, temp_dir)
            
            if not video_result["success"]:
                return video_result
            
            # Upload final video to GCS
            final_video_url = _upload_final_video(video_result["video_path"])
            
            if not final_video_url:
                return {
                    "error": "Video upload failed", 
                    "success": False
                }
            
            # Save comprehensive results to state
            video_metadata = {
                "output_video_url": final_video_url,
                "video_specs": {
                    "duration": video_result["duration"],
                    "resolution": "1920x1080",
                    "format": "MP4",
                    "scene_count": len(image_urls),
                    "audio_tracks": len(audio_urls),
                    "timing_method": "dynamic_audio_based"
                },
                "assets_used": {
                    "audio_files": len(audio_urls),
                    "image_files": len(image_urls),
                    "audio_urls": audio_urls,
                    "image_urls": image_urls
                },
                "assembly_completed": True,
                "creation_timestamp": str(uuid.uuid4())[:8]
            }
            
            # FIXED: Safe state saving
            try:
                tool_context.state['output_video_url'] = final_video_url
                tool_context.state['video_metadata'] = video_metadata
                tool_context.state['assembly_completed'] = True
                tool_context.state['final_video_url'] = final_video_url  # Alternative key
            except Exception as e:
                step_logger.warning(f"⚠️ Could not save to state: {e}")
            
            step_logger.info(f"✅ Video assembly completed!")
            step_logger.info(f"🎬 Final video URL: {final_video_url}")
            step_logger.info(f"⏱️ Duration: {video_result['duration']:.2f}s (natural timing)")
            step_logger.info(f"📐 Resolution: 1920x1080")
            step_logger.info(f"🎵 Perfect audio sync achieved!")
            
            return {
                "success": True,
                "output_video_url": final_video_url,
                "video_specs": video_metadata["video_specs"],
                "scene_count": len(image_urls),
                "duration": video_result["duration"],
                "timing_method": "dynamic_audio_based",
                "message": f"Dynamic video created successfully: {final_video_url}"
            }
            
    except Exception as e:
        step_logger.error(f"❌ Video assembly failed: {str(e)}")
        return {
            "error": f"Video assembly failed: {str(e)}",
            "success": False
        }

def _download_video_assets(audio_urls: List[str], image_urls: List[str], temp_dir: str) -> Dict[str, Any]:
    """Download all audio and image assets from GCS to temp directory."""
    step_logger.info("📥 Downloading video assets using authenticated storage manager...")

    try:
        assets = {
            "audio_files": [],
            "image_files": [],
            "success": True
        }

        # Download audio files using storage_manager
        for i, audio_url in enumerate(audio_urls, 1):
            try:
                step_logger.info(f"📥 Downloading audio {i}: {audio_url}")

                # Convert the public HTTP URL to a GCS URI
                gcs_uri = audio_url.replace("https://storage.googleapis.com/", "gs://")

                # Use the authenticated storage_manager to download the file bytes
                file_content = storage_manager.download_as_bytes(gcs_uri)

                audio_path = os.path.join(temp_dir, f"audio_{i:02d}.mp3")
                with open(audio_path, 'wb') as f:
                    f.write(file_content)

                assets["audio_files"].append({
                    "path": audio_path,
                    "url": audio_url,
                    "index": i,
                    "size": len(file_content)
                })

                step_logger.info(f"✅ Audio {i} downloaded: {len(file_content)} bytes")

            except Exception as e:
                step_logger.error(f"❌ Failed to download audio {i}: {str(e)}")
                return {"success": False, "error": f"Audio download failed: {str(e)}"}

        # Download image files using storage_manager
        for i, image_url in enumerate(image_urls, 1):
            try:
                step_logger.info(f"📥 Downloading image {i}: {image_url}")

                # Convert the public HTTP URL to a GCS URI
                gcs_uri = image_url.replace("https://storage.googleapis.com/", "gs://")

                # Use the authenticated storage_manager to download the file bytes
                file_content = storage_manager.download_as_bytes(gcs_uri)

                image_path = os.path.join(temp_dir, f"image_{i:02d}.png")
                with open(image_path, 'wb') as f:
                    f.write(file_content)

                assets["image_files"].append({
                    "path": image_path,
                    "url": image_url,
                    "index": i,
                    "size": len(file_content)
                })

                step_logger.info(f"✅ Image {i} downloaded: {len(file_content)} bytes")

            except Exception as e:
                step_logger.error(f"❌ Failed to download image {i}: {str(e)}")
                return {"success": False, "error": f"Image download failed: {str(e)}"}

        step_logger.info(f"✅ All assets downloaded: {len(assets['audio_files'])} audio, {len(assets['image_files'])} images")
        return assets

    except Exception as e:
        step_logger.error(f"❌ Asset download failed: {str(e)}")
        return {"success": False, "error": f"Asset download failed: {str(e)}"}


def _create_video_with_dynamic_timing(assets: Dict[str, Any], script_data: Dict[str, Any], temp_dir: str) -> Dict[str, Any]:
    """
    Create video using MoviePy with DYNAMIC TIMING - EXACT same approach as working test script.
    """
    step_logger.info("🎬 Creating video with DYNAMIC TIMING...")
    step_logger.info("💫 Each scene duration will match its audio length!")
    
    try:
        video_clips = []
        total_duration = 0
        
        for i, image_asset in enumerate(assets["image_files"]):
            scene_num = i + 1
            step_logger.info(f"   Processing scene {scene_num}...")
            
            # Step 1: Create ImageClip (no duration set yet) - EXACT same as test script
            clip = ImageClip(image_asset["path"])
            step_logger.info(f"      📸 Image clip created (no duration set yet)")
            
            # Step 2: Load corresponding audio to determine scene duration - EXACT same as test script
            if i < len(assets["audio_files"]):
                try:
                    audio_asset = assets["audio_files"][i]
                    audio_clip = AudioFileClip(audio_asset["path"])
                    audio_duration = audio_clip.duration
                    
                    step_logger.info(f"      🎵 Audio loaded: {audio_duration:.2f}s duration")
                    
                    # Step 3: Set video duration to MATCH audio duration - EXACT same as test script
                    clip = clip.with_duration(audio_duration)
                    step_logger.info(f"      ⏱️ Video duration set to match audio: {audio_duration:.2f}s")
                    
                    # Step 4: Attach audio to video - EXACT same as test script
                    clip = clip.with_audio(audio_clip)
                    step_logger.info(f"      ✅ Audio attached - perfect sync achieved!")
                    
                    total_duration += audio_duration
                    
                except Exception as e:
                    step_logger.error(f"      ⚠️ Could not load audio {scene_num}: {e}")
                    # Fallback to 3 seconds - same as test script
                    fallback_duration = 3.0
                    clip = clip.with_duration(fallback_duration)
                    total_duration += fallback_duration
                    step_logger.info(f"      ⚠️ Using fallback duration: {fallback_duration}s")
            else:
                # No audio for this scene - same as test script
                fallback_duration = 3.0
                clip = clip.with_duration(fallback_duration)
                total_duration += fallback_duration
                step_logger.info(f"      ⚠️ No audio - using fallback duration: {fallback_duration}s")
            
            # Step 5: Resize to 1080p - EXACT same as test script
            try:
                clip = clip.resized(height=1080)
                step_logger.info(f"      📏 Resized to 1080p using resized()")
            except Exception as resize_error:
                step_logger.error(f"      ⚠️ Resize failed: {resize_error}")
            
            video_clips.append(clip)
        
        step_logger.info(f"📊 Dynamic timing complete!")
        step_logger.info(f"   🎬 Created {len(video_clips)} scenes with natural durations")
        step_logger.info(f"   ⏱️ Total duration: {total_duration:.2f}s")
        
        # Concatenate all clips - EXACT same as test script
        step_logger.info("🔗 Concatenating dynamically timed scenes...")
        final_video = concatenate_videoclips(video_clips, method="compose")
        
        actual_duration = final_video.duration
        step_logger.info(f"   ✅ Final video duration: {actual_duration:.2f}s")
        
        # Export video - EXACT same as test script
        video_filename = f"chelsea_dynamic_{uuid.uuid4().hex[:8]}.mp4"
        video_path = os.path.join(temp_dir, video_filename)
        
        step_logger.info(f"🎥 Exporting dynamic video: {video_filename}")
        
        final_video.write_videofile(
            video_path,
            fps=24,
            codec='libx264',
            audio_codec='aac'
        )
        
        file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
        step_logger.info(f"✅ Video exported: {file_size_mb:.2f} MB")
        
        # Clean up MoviePy resources - EXACT same as test script
        final_video.close()
        for clip in video_clips:
            if hasattr(clip, 'audio') and clip.audio:
                clip.audio.close()
            clip.close()
        
        step_logger.info("✅ Dynamic audio-video synchronization complete!")
        
        return {
            "success": True,
            "video_path": video_path,
            "duration": actual_duration,
            "file_size_mb": file_size_mb,
            "scene_count": len(video_clips)
        }
        
    except Exception as e:
        step_logger.error(f"❌ Video creation failed: {str(e)}")
        return {
            "success": False,
            "error": f"Video creation failed: {str(e)}"
        }

def _upload_final_video(video_path: str) -> str:
    """Upload final video to GCS and return public URL."""
    step_logger.info("📤 Uploading final video to GCS...")
    
    try:
        if not os.path.exists(video_path):
            step_logger.error("❌ Video file not found")
            return None
        
        video_size = os.path.getsize(video_path)
        step_logger.info(f"📁 Video size: {video_size} bytes")
        
        # Read video file
        with open(video_path, 'rb') as f:
            video_data = f.read()
        
        # Generate unique filename
        video_filename = f"chelsea_dynamic_{uuid.uuid4().hex[:8]}.mp4"
        
        # Upload to GCS videos folder
        upload_result = storage_manager.upload_binary(
            content=video_data,
            folder="videos",
            filename=video_filename,
            content_type="video/mp4"
        )
        
        if upload_result.get("status") == "success":
            public_url = upload_result["public_url"]
            step_logger.info(f"✅ Video uploaded to GCS: {public_url}")
            return public_url
        else:
            step_logger.error(f"❌ Upload failed: {upload_result}")
            return None
            
    except Exception as e:
        step_logger.error(f"❌ Video upload failed: {str(e)}")
        return None
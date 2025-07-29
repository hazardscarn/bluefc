# cultural_image_tool.py
import os
import json
import base64
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from google.adk.tools import ToolContext
from google.genai import types
from google import genai
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from vertexai.generative_models import HarmCategory, HarmBlockThreshold
import logging
from google.adk.tools import FunctionTool
from google.cloud import storage
import requests
from .config import Modelconfig, SecretConfig

# Initialize logging
step_logger = logging.getLogger("AGENT_STEPS")

# Initialize Vertex AI
# project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "energyagentai")
# location = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
# vertexai.init(project=project_id, location=location)

# Initialize Vertex AI with Secret Manager
project_id = SecretConfig.get_google_cloud_project()
location = SecretConfig.get_google_cloud_location()
vertexai.init(project=project_id, location=location)

# Initialize Gemini 2.0 Flash client for image generation
genai_client = genai.Client(
    vertexai=True,
    project=project_id,
    location=location
)

# Required GCS buckets (create these manually or via setup script)
ORIGINAL_IMAGES_BUCKET = f"{project_id}-bluefc-original-products"
CUSTOMIZED_IMAGES_BUCKET = f"{project_id}-bluefc-customized-product"

def customize_product_image_function(product_id: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Customize a product image based on cultural persona insights using Flash 2.0 image generation.
    
    This function takes a product ID, finds the corresponding product from recommendations,
    analyzes the cultural persona data, and generates a culturally-adapted version of the 
    product image using Gemini 2.0 Flash image generation model.
    
    Args:
        product_id (str): The product ID to customize
        tool_context (ToolContext): ADK tool context containing session state with:
            - 'recommendations': List of product recommendations
            - 'persona_name': Generated persona name  
            - 'persona_description': Persona description
            - 'cultural_values': Cultural preferences and values
            - 'audience_profile': Demographics and lifestyle info
    
    Returns:
        Dict[str, Any]: Result dictionary containing:
            - 'success' (bool): True if customization succeeded
            - 'customized_image_url' (str): URL of the generated image
            - 'original_image_url' (str): URL of the original product image
            - 'customization_reasoning' (str): Explanation of changes made
            - 'product_name' (str): Name of the customized product
            - 'error' (str): Error message if customization failed
    
    State Updates:
        Updates tool_context.state with:
        - 'customized_image_url': URL of the generated image
        - 'customization_reasoning': Detailed reasoning for the changes
        - 'original_product': Original product information
    """
    
    step_logger.info(f"STEP: 🎨 Customizing product image for ID: {product_id}")
    
    try:
        # Get recommendations from state
        recommendations = tool_context.state.get('recommendations', [])
        if not recommendations:
            return {"error": "No product recommendations found. Run product recommendations first."}
        
        # Find the specific product
        target_product = None
        for product in recommendations:
            if product.get('product_id') == product_id or product.get('id') == int(product_id.replace('prod_', '')):
                target_product = product
                break
        
        if not target_product:
            return {"error": f"Product with ID {product_id} not found in recommendations."}
        
        step_logger.info(f"   ✅ Found product: {target_product.get('name', 'Unknown')}")
        
        # Get persona data from state
        persona_data = {
            "persona_name": tool_context.state.get('persona_name', ''),
            "persona_description": tool_context.state.get('persona_description', ''),
            "cultural_values": tool_context.state.get('cultural_values', {}),
            "audience_profile": tool_context.state.get('audience_profile', {})
        }
        
        if not persona_data["persona_name"]:
            return {"error": "No persona data found. Create persona first."}
        
        step_logger.info(f"   📊 Using persona: {persona_data['persona_name']}")
        
        # Create cultural adaptation prompt
        customization_prompt = create_cultural_adaptation_prompt(target_product, persona_data)
        step_logger.info(f"   🎯 Generated customization prompt")
        
        # Get original product image
        original_image_url = target_product.get('image_url', '')
        if not original_image_url:
            return {"error": "No image URL found for this product."}
        
        # Generate customized image using Flash 2.0
        customized_image_url = generate_customized_image(original_image_url, customization_prompt)
        
        if not customized_image_url:
            return {"error": "Failed to generate customized image."}
        
        step_logger.info(f"   ✅ Generated customized image")
        
        # Generate reasoning for the customization
        reasoning = generate_customization_reasoning(target_product, persona_data, customization_prompt)
        
        # Update state with results
        tool_context.state['customized_image_url'] = customized_image_url
        tool_context.state['customization_reasoning'] = reasoning
        tool_context.state['original_product'] = target_product
        
        return {
            "success": True,
            "customized_image_url": customized_image_url,
            "original_image_url": original_image_url,
            "customization_reasoning": reasoning,
            "product_name": target_product.get('name', 'Unknown Product'),
            "message": f"Successfully customized {target_product.get('name')} for {persona_data['persona_name']}"
        }
        
    except Exception as e:
        step_logger.error(f"   ❌ Image customization failed: {str(e)}")
        return {"error": f"Image customization failed: {str(e)}"}


def create_cultural_adaptation_prompt(product: Dict[str, Any], persona: Dict[str, Any]) -> str:
    """Create a detailed prompt for cultural image adaptation."""
    
    # Extract key cultural elements
    cultural_values = persona.get('cultural_values', {})
    audience_profile = persona.get('audience_profile', {})
    
    entertainment_prefs = cultural_values.get('entertainment_preferences', '')
    brand_affinities = cultural_values.get('brand_affinities', '')
    demographics = audience_profile.get('demographics', '')
    lifestyle = audience_profile.get('lifestyle', '')
    values = audience_profile.get('values', '')
    
    prompt = f"""
    Modify this {product.get('type', 'product')} image to appeal to the target persona: {persona.get('persona_name', '')}.
    
    ORIGINAL PRODUCT: {product.get('name', '')}
    DESCRIPTION: {product.get('description', '')}
    
    TARGET AUDIENCE PROFILE:
    - Demographics: {demographics}
    - Lifestyle: {lifestyle}  
    - Core Values: {values}
    
    CULTURAL CUSTOMIZATION REQUIREMENTS:
    - Entertainment Preferences: {entertainment_prefs}
    - Brand Affinities: {brand_affinities}
    
    CUSTOMIZATION GOALS:
    1. Maintain the core Chelsea FC branding and product functionality
    2. Add cultural elements that resonate with this audience
    3. Modify colors, patterns, or text to match cultural preferences
    4. Include subtle design elements that reflect their lifestyle and values
    5. Ensure the design feels authentic and premium, not forced
    
    STYLE MODIFICATIONS:
    - Use colors and patterns that appeal to this demographic
    - Add cultural symbols or design elements that resonate
    - Modify typography if needed to match cultural preferences
    - Include lifestyle-relevant details (tech elements, artistic touches, etc.)
    - Maintain high-quality, premium appearance
    
    Make the customization thoughtful and authentic to both Chelsea FC heritage and the target culture.
    """
    
    return prompt.strip()


def download_and_upload_image(image_url: str) -> Optional[str]:
    """Download image from external URL and upload to Google Cloud Storage for Vertex AI access."""
    
    try:
        step_logger.info(f"   📥 Downloading image from: {image_url}")
        
        # Download the image
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(image_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        if not response.content:
            step_logger.error("   ❌ Empty image content")
            return None
        
        step_logger.info(f"   ✅ Downloaded {len(response.content)} bytes")
        
        # Initialize Cloud Storage client
        storage_client = storage.Client(project=project_id)
        
        # Create bucket name for original images
        bucket = storage_client.bucket(ORIGINAL_IMAGES_BUCKET)
        
        # Generate unique filename for the original image
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"original_product_{timestamp}_{unique_id}.jpg"
        
        # Upload to GCS
        blob = bucket.blob(filename)
        blob.upload_from_string(
            response.content, 
            content_type=response.headers.get('content-type', 'image/jpeg')
        )
        
        # Return GCS URI format that Vertex AI can access
        gcs_uri = f"gs://{ORIGINAL_IMAGES_BUCKET}/{filename}"
        step_logger.info(f"   ✅ Uploaded to GCS: {gcs_uri}")
        return gcs_uri
        
    except requests.exceptions.RequestException as e:
        step_logger.error(f"   ❌ Failed to download image: {str(e)}")
        return None
    except Exception as e:
        step_logger.error(f"   ❌ Failed to upload to GCS: {str(e)}")
        return None


def generate_customized_image(original_image_url: str, customization_prompt: str) -> Optional[str]:
    """Generate customized image using Gemini 2.0 Flash image generation."""
    
    try:
        step_logger.info(f"   🖼️ Starting Flash 2.0 image generation...")
        
        # First, download and upload the original image to a Vertex AI accessible location
        accessible_image_uri = download_and_upload_image(original_image_url)
        if not accessible_image_uri:
            step_logger.error("   ❌ Failed to make image accessible to Vertex AI")
            return None
        
        step_logger.info(f"   ✅ Image uploaded to accessible location: {accessible_image_uri}")
        
        # Create image part from accessible URI
        msg1_image1 = types.Part.from_uri(
            file_uri=accessible_image_uri,
            mime_type="image/jpeg"
        )
        
        # Set up the model
        model = "gemini-2.0-flash-preview-image-generation"
        
        # Create content with image and prompt
        contents = [
            types.Content(
                role="user",
                parts=[
                    msg1_image1,
                    types.Part.from_text(text=customization_prompt)
                ]
            )
        ]
        
        # Configure generation with valid safety settings only
        generate_content_config = types.GenerateContentConfig(
            temperature=0.8,
            top_p=0.95,
            max_output_tokens=8192,
            response_modalities=["TEXT", "IMAGE"],
            safety_settings=[
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF")
            ]
        )
        
        # Generate the image
        response = genai_client.models.generate_content(
            model=model,
            contents=contents,
            config=generate_content_config
        )
        
        # Extract image from response
        if response and hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        # Save image to cloud storage and return URL
                        image_url = save_image_to_cloud(part.inline_data.data, part.inline_data.mime_type)
                        return image_url
        
        step_logger.warning(f"   ⚠️ No image generated in response")
        return None
        
    except Exception as e:
        step_logger.error(f"   ❌ Flash 2.0 generation failed: {str(e)}")
        return None


def save_image_to_cloud(image_data: bytes, mime_type: str) -> str:
    """Save generated image to Google Cloud Storage and return public URL."""
    
    try:
        # Initialize Cloud Storage client
        storage_client = storage.Client(project=project_id)
        
        # Use the customized images bucket
        bucket = storage_client.bucket(CUSTOMIZED_IMAGES_BUCKET)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        file_extension = "jpg" if "jpeg" in mime_type else "png"
        filename = f"customized_product_{timestamp}_{unique_id}.{file_extension}"
        
        # Upload image
        blob = bucket.blob(filename)
        blob.upload_from_string(image_data, content_type=mime_type)
        
        # Make blob publicly accessible
        blob.make_public()
        
        # Return public URL
        public_url = blob.public_url
        step_logger.info(f"   ✅ Image saved to: {public_url}")
        return public_url
        
    except Exception as e:
        step_logger.error(f"   ❌ Failed to save image: {str(e)}")
        # Fallback: save locally and return a placeholder URL
        return save_image_locally(image_data, mime_type)


def save_image_locally(image_data: bytes, mime_type: str) -> str:
    """Fallback: Save image locally and return local path."""
    
    try:
        # Create local directory if it doesn't exist
        local_dir = "customized_images"
        os.makedirs(local_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        file_extension = "jpg" if "jpeg" in mime_type else "png"
        filename = f"customized_product_{timestamp}_{unique_id}.{file_extension}"
        filepath = os.path.join(local_dir, filename)
        
        # Save image
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        # Return local path (in production, you'd serve this through a web server)
        local_url = f"file://{os.path.abspath(filepath)}"
        step_logger.info(f"   💾 Image saved locally: {local_url}")
        return local_url
        
    except Exception as e:
        step_logger.error(f"   ❌ Failed to save image locally: {str(e)}")
        return "placeholder_image_url"


def generate_customization_reasoning(product: Dict[str, Any], persona: Dict[str, Any], prompt: str) -> str:
    """Generate detailed reasoning for why the customization appeals to the persona."""
    
    try:
        model = GenerativeModel(
            Modelconfig.flash_model,
            generation_config=GenerationConfig(
                temperature=0.3,
                max_output_tokens=2000
            ),
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        reasoning_prompt = f"""
        Explain why the customized version of this Chelsea FC product appeals to the target persona.
        
        PRODUCT: {product.get('name', '')}
        ORIGINAL: {product.get('description', '')}
        
        PERSONA: {persona.get('persona_name', '')}
        DESCRIPTION: {persona.get('persona_description', '')}
        
        CUSTOMIZATION APPLIED: {prompt}
        
        Provide a detailed but concise explanation covering:
        1. Cultural elements that resonate with this audience
        2. How the design modifications align with their values and lifestyle
        3. Why this customization would increase purchase appeal
        4. Connection between their entertainment/brand preferences and the design choices
        
        Keep it under 200 words and focus on the strategic marketing insights.
        """
        
        response = model.generate_content(reasoning_prompt)
        return response.text.strip() if response.text else "Customization designed to match cultural preferences."
        
    except Exception as e:
        step_logger.error(f"   ⚠️ Failed to generate reasoning: {str(e)}")
        return "Customization tailored to match the target audience's cultural preferences and lifestyle."



customize_product_image_tool = FunctionTool(customize_product_image_function)
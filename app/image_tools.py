"""Image generation tools for Culinary Companion agent."""

import base64
import io
import json
import re
import time
from google.cloud import storage
from google import genai
from google.genai import types
from google.adk.tools import ToolContext
from PIL import Image, ImageDraw, ImageFont

GCS_BUCKET_NAME = "culinary-companion-media-qwiklabs-gcp-03-f55cf09067a8"
GCP_PROJECT_ID = "qwiklabs-gcp-03-f55cf09067a8"
GCP_LOCATION = "us-east1"


def generate_culinary_item_image(
    item_description: str,
    tool_context: ToolContext,
) -> str:
    """Generate an image for a culinary item, dish, or ingredient in the agent's domain using gemini-3.1-flash-lite-image in the global region.

    Saves the generated image as an artifact using tool_context.save_artifact so it appears in Playground's Artifacts panel,
    uploads the image bytes directly to Cloud Storage, and returns its public https URL.

    Args:
        item_description: Detailed description of the food item, dish, or culinary creation to generate an image for.
        tool_context: ADK ToolContext injected automatically at runtime.

    Returns:
        The public Cloud Storage https URL of the generated image.
    """
    clean_desc = item_description.strip()
    slug = re.sub(r"[^\w\-_]", "_", clean_desc[:25].lower()).strip("_")
    filename = f"{slug}_{int(time.time())}.jpg"
    object_name = f"item_images/{filename}"

    client = genai.Client(vertexai=True, project=GCP_PROJECT_ID, location="global")
    prompt = f"Gourmet culinary food photography of {clean_desc}. Professional plating, 8k resolution, rustic restaurant lighting."

    resp = client.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"]
        ),
    )

    image_bytes = None
    mime_type = "image/jpeg"
    if resp.candidates and resp.candidates[0].content and resp.candidates[0].content.parts:
        for part in resp.candidates[0].content.parts:
            if part.inline_data:
                image_bytes = part.inline_data.data
                if part.inline_data.mime_type:
                    mime_type = part.inline_data.mime_type
                break

    if not image_bytes:
        raise RuntimeError("Failed to generate image bytes from gemini-3.1-flash-lite-image model.")

    # (1) Save artifact so it shows up in Playground's Artifacts panel
    artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    tool_context.save_artifact(filename=filename, artifact=artifact_part)

    # (2) Upload image bytes to public Cloud Storage bucket
    storage_client = storage.Client(project=GCP_PROJECT_ID)
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(object_name)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{object_name}"
    return public_url


def generate_culinary_item_video(
    item_description: str,
    tool_context: ToolContext,
) -> str:
    """Generate a short video for a culinary item, dish, or cooking process in the agent's domain using Google's Omni model (gemini-omni-flash-preview) in the global region.

    Saves the generated video as an artifact using tool_context.save_artifact so it appears in Playground's Artifacts panel,
    uploads the video bytes directly to Cloud Storage, and returns its public https URL.

    Args:
        item_description: Description of the food item, dish, or cooking process to generate a short video for.
        tool_context: ADK ToolContext injected automatically at runtime.

    Returns:
        The public Cloud Storage https URL of the generated video.
    """
    clean_desc = item_description.strip()
    slug = re.sub(r"[^\w\-_]", "_", clean_desc[:25].lower()).strip("_")
    filename = f"{slug}_{int(time.time())}.mp4"
    object_name = f"item_videos/{filename}"

    client = genai.Client(vertexai=True, project=GCP_PROJECT_ID, location="global")
    prompt = f"High quality gourmet culinary video of {clean_desc}. Smooth camera motion, rustic lighting."

    interaction = client.interactions.create(
        model="gemini-omni-flash-preview",
        input=prompt
    )

    video_bytes = None
    mime_type = "video/mp4"

    if hasattr(interaction, "output_video") and interaction.output_video:
        data = interaction.output_video.data
        if isinstance(data, str):
            video_bytes = base64.b64decode(data)
        elif isinstance(data, bytes):
            video_bytes = data
        if getattr(interaction.output_video, "mime_type", None):
            mime_type = interaction.output_video.mime_type

    if not video_bytes:
        raise RuntimeError("Failed to generate video bytes from gemini-omni-flash-preview model.")

    # (1) Save artifact so it shows up in Playground's Artifacts panel
    artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
    tool_context.save_artifact(filename=filename, artifact=artifact_part)

    # (2) Upload video bytes to public Cloud Storage bucket
    storage_client = storage.Client(project=GCP_PROJECT_ID)
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(object_name)
    blob.upload_from_string(video_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{object_name}"
    return public_url


def generate_recipe_photo(recipe_name: str, description: str = "") -> str:
    """Generate a high-quality photo for a recommended recipe or dish using gemini-3.1-flash-lite-image and upload it to Cloud Storage.
    
    Args:
        recipe_name: Name of the dish or recipe (e.g. 'Arrabiata Penne', 'Mushroom Risotto').
        description: Brief description or key visual details of the dish.
        
    Returns:
        JSON string containing the public image URL.
    """
    clean_name = recipe_name.strip()
    safe_filename = re.sub(r"[^\w\-_]", "_", clean_name.lower())
    object_name = f"recipe_photos/{safe_filename}_{int(time.time())}.jpg"
    
    image_bytes = None
    mime_type = "image/jpeg"
    
    # 1. Use gemini-3.1-flash-lite-image in global region for realistic food photography
    try:
        client = genai.Client(vertexai=True, project=GCP_PROJECT_ID, location="global")
        prompt = f"Gourmet food photo of {clean_name}. {description}. Plated elegantly on a rustic dinner table, professional food photography, 8k resolution."
        resp = client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"]
            ),
        )
        if resp.candidates and resp.candidates[0].content and resp.candidates[0].content.parts:
            for part in resp.candidates[0].content.parts:
                if part.inline_data:
                    image_bytes = part.inline_data.data
                    if part.inline_data.mime_type:
                        mime_type = part.inline_data.mime_type
                    break
    except Exception as e:
        print(f"Gemini image generation failed ({e}); trying Imagen fallback...")
    
    # 2. Fallback: Try Imagen 3
    if not image_bytes:
        try:
            client = genai.Client(vertexai=True, project=GCP_PROJECT_ID, location=GCP_LOCATION)
            prompt = f"Gourmet food photo of {clean_name}. {description}. Plated elegantly, professional food photography."
            result = client.models.generate_images(
                model="imagen-3.0-generate-002",
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    output_mime_type="image/jpeg",
                    aspect_ratio="1:1",
                ),
            )
            if result.generated_images:
                image_bytes = result.generated_images[0].image.image_bytes
        except Exception as err:
            print(f"Imagen fallback failed: {err}")
            
    if not image_bytes:
        return json.dumps({
            "status": "error",
            "message": f"Could not generate image for '{clean_name}'.",
        })
        
    # 3. Upload image bytes to Cloud Storage bucket
    try:
        storage_client = storage.Client(project=GCP_PROJECT_ID)
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(object_name)
        blob.upload_from_string(image_bytes, content_type=mime_type)
        
        public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{object_name}"
        return json.dumps({
            "status": "success",
            "recipe_name": clean_name,
            "public_url": public_url,
            "message": f"Successfully generated photo for '{clean_name}'.",
        }, indent=2)
    except Exception as err:
        return json.dumps({
            "status": "error",
            "message": f"Failed to upload image to GCS: {str(err)}",
        })

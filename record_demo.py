import os
import sys
import time
from playwright.sync_api import sync_playwright
from google.cloud import storage

GCS_BUCKET_NAME = "culinary-companion-media-qwiklabs-gcp-03-f55cf09067a8"
GCP_PROJECT_ID = "qwiklabs-gcp-03-f55cf09067a8"

def main():
    os.makedirs("demo_videos", exist_ok=True)
    
    with sync_playwright() as p:
        print("Launching Chromium browser for demo recording...")
        browser = p.chromium.launch(headless=True)
        
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            record_video_dir="demo_videos",
            record_video_size={"width": 1280, "height": 800}
        )
        
        page = context.new_page()
        print("Navigating to http://localhost:8080 ...")
        page.goto("http://localhost:8080", wait_until="networkidle")
        time.sleep(2)
        
        # --- Demo Step 1: Recipe Search & A2UI Card ---
        print("Executing Step 1: Recipe Search prompt...")
        prompt1 = "Search for an Arrabiata recipe"
        page.fill("#input", prompt1)
        time.sleep(1)
        page.click(".send-btn")
        
        print("Waiting for agent response to complete...")
        # Wait until the agent bubble is created AND no longer displaying "…" loading indicator
        page.wait_for_function(
            "document.querySelector('.msg-row.agent .bubble') && document.querySelector('.msg-row.agent .bubble').textContent !== '…'",
            timeout=45000
        )
        print("Response received for Step 1! Pausing to display recipe card...")
        time.sleep(8) # Let user clearly read the rendered card and recipe details
        
        # --- Demo Step 2: Image Generation Tool Call & GCS URL ---
        print("Executing Step 2: Image Generation prompt...")
        prompt2 = "Generate a photo of a freshly baked sourdough bread"
        page.fill("#input", prompt2)
        time.sleep(1)
        page.click(".send-btn")
        
        print("Waiting for second agent response to complete...")
        # Wait until the 2nd agent bubble is created AND no longer displaying "…"
        page.wait_for_function(
            "document.querySelectorAll('.msg-row.agent .bubble').length >= 2 && document.querySelectorAll('.msg-row.agent .bubble')[1].textContent !== '…'",
            timeout=45000
        )
        print("Response received for Step 2! Pausing to display generated image...")
        time.sleep(8) # Let user clearly see the generated photo card
        
        # Get recorded video path before closing
        video_path = page.video.path()
        context.close()
        browser.close()
        
        print("Recording finished. Local video path:", video_path)
        
        # Upload recorded video to Cloud Storage
        if os.path.exists(video_path):
            file_size = os.path.getsize(video_path)
            print(f"Video file size: {file_size} bytes")
            
            filename = f"culinary_companion_demo_{int(time.time())}.webm"
            object_name = f"demos/{filename}"
            
            storage_client = storage.Client(project=GCP_PROJECT_ID)
            bucket = storage_client.bucket(GCS_BUCKET_NAME)
            blob = bucket.blob(object_name)
            blob.upload_from_filename(video_path, content_type="video/webm")
            
            public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{object_name}"
            print("Successfully uploaded demo video to GCS!")
            print("Public Demo Video URL:", public_url)
            
            # Copy to artifact directory
            artifact_dir = "/config/.gemini/antigravity/brain/c34656c3-582d-4876-8b4e-dd2febcc7238"
            artifact_path = os.path.join(artifact_dir, "demo_video.webm")
            with open(video_path, "rb") as rf, open(artifact_path, "wb") as wf:
                wf.write(rf.read())
            print(f"Saved artifact copy to {artifact_path}")

if __name__ == "__main__":
    main()

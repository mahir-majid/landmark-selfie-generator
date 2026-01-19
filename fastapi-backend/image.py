#!/usr/bin/env python3
"""
FastAPI microservice for InfiniteYou RunPod API
Accepts face images and prompts from the selfie page
"""

import os
import time
import base64
import requests
import random
from dotenv import load_dotenv
from PIL import Image
import io
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import uvicorn
from typing import Optional

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="InfiniteYou RunPod API Service",
    description="FastAPI microservice for generating AI selfies using RunPod",
    version="1.0.0"
)

# Add CORS middleware to allow requests from the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def base64_to_image(base64_string, output_path):
    """Convert base64 string to image and save"""
    # Remove data URL prefix if present
    if base64_string.startswith('data:image'):
        base64_string = base64_string.split(',')[1]
    
    image_data = base64.b64decode(base64_string)
    image = Image.open(io.BytesIO(image_data))
    image.save(output_path)
    return output_path

def image_to_base64(image_data: bytes) -> str:
    """Convert image bytes to base64 string"""
    image_base64 = base64.b64encode(image_data).decode()
    return image_base64  # Return just the base64 string, not the data URL

async def call_runpod_api(id_image_base64: str, prompt: str, control_image_base64: Optional[str] = None):
    """
    Call RunPod InfiniteYou API
    
    Args:
        id_image_base64: Base64 encoded identity image
        prompt: Text prompt describing the desired image
        control_image_base64: Optional base64 encoded control image
    """
    
    # Get environment variables
    runpod_url = os.getenv('RUNPOD_INFU_URL')
    runpod_api_key = os.getenv('RUNPOD_API_KEY')
    
    if not runpod_url:
        raise HTTPException(status_code=500, detail="RUNPOD_INFU_URL environment variable not set")
    
    if not runpod_api_key:
        raise HTTPException(status_code=500, detail="RUNPOD_API_KEY environment variable not set")
    
    # Extract endpoint ID for status polling
    if runpod_url and '/v2/' in runpod_url:
        endpoint_id = runpod_url.split('/v2/')[1].split('/')[0]
        status_url = f"https://api.runpod.ai/v2/{endpoint_id}/status"
    else:
        status_url = runpod_url
    
    # Generate a random seed for reproducible but varied results
    random_seed = random.randint(1, 999999)
    
    # Prepare request payload in RunPod format
    payload = {
        "id": f"selfie-{int(time.time())}",
        "input": {
            "id_image": id_image_base64,
            "prompt": prompt,
            "infu_source_img_token": "person with a smile",
            "model_version": "aes_stage2",
            "enable_realism": True,
            "enable_anti_blur": True,
            "enable_face_realism": True,
            "enable_realism_one": False,
            "enable_realism_two": False,
            "realism_weight": 1.0,
            "anti_blur_weight": 1.0,
            "face_realism_weight": 1.0,
            "realism_one_weight": 1.0,
            "realism_two_weight": 1.0,
            "flux_model": "flux-schnell",
            "seed": random_seed,
            "guidance_scale": 5,
            "num_steps": 5,
            "width": 1024,
            "height": 1024,
        }
    }
    
    # Add control image to payload if provided
    if control_image_base64:
        payload["input"]["control_image"] = control_image_base64
    
    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {runpod_api_key}"
    }
    
    try:
        # Send request
        response = requests.post(
            runpod_url,
            json=payload,
            headers=headers,
            timeout=600  # 10 minutes timeout
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"RunPod API error: {response.text}")
        
        result = response.json()
        
        # Check if job is queued or processing
        if result.get("status") in ["IN_QUEUE", "IN_PROGRESS"]:
            job_id = result.get("id")
            
            # Poll for job completion
            max_polls = 1200  # 10 minutes with 0.5-second intervals
            poll_count = 0
            
            while poll_count < max_polls:
                time.sleep(0.5)  # Wait 0.5 seconds between polls
                poll_count += 1
                
                # Check job status
                status_response = requests.get(
                    f"{status_url}/{job_id}",
                    headers=headers,
                    timeout=30
                )
                
                if status_response.status_code == 200:
                    status_result = status_response.json()
                    current_status = status_result.get("status")
                    
                    if current_status == "COMPLETED":
                        # Get the output
                        if "output" in status_result:
                            output = status_result["output"]
                            
                            if output.get("success") and "image" in output:
                                print(f"🔍 Debug: RunPod job completed successfully")
                                print(f"🔍 Debug: Image data length: {len(output['image'])}")
                                return {
                                    "success": True,
                                    "image": output["image"],
                                    "metadata": output.get("metadata", {}),
                                    "job_id": job_id
                                }
                            else:
                                error_msg = output.get('error', 'Unknown error')
                                raise HTTPException(status_code=500, detail=f"RunPod generation failed: {error_msg}")
                        else:
                            raise HTTPException(status_code=500, detail="No output in completed job")
                            
                    elif current_status == "FAILED":
                        error_msg = status_result.get('error', 'Unknown error')
                        raise HTTPException(status_code=500, detail=f"Job failed: {error_msg}")
                        
                else:
                    raise HTTPException(status_code=status_response.status_code, detail="Failed to check job status")
            
            raise HTTPException(status_code=408, detail="Job timed out after 10 minutes")
            
        # Direct response (if job completed immediately)
        elif "output" in result:
            output = result["output"]
            
            if output.get("success") and "image" in output:
                return {
                    "success": True,
                    "image": output["image"],
                    "metadata": output.get("metadata", {}),
                    "job_id": result.get("id")
                }
            else:
                error_msg = output.get('error', 'Unknown error')
                raise HTTPException(status_code=500, detail=f"RunPod generation failed: {error_msg}")
        else:
            raise HTTPException(status_code=500, detail=f"Unexpected response format from RunPod")
            
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=408, detail="Request timed out")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.post("/generate-selfie")
async def generate_selfie(
    face_image: UploadFile = File(..., description="Face image file"),
    prompt: str = Form(..., description="Text prompt describing the desired image"),
    control_image: Optional[UploadFile] = File(None, description="Optional control image file")
):
    """
    Generate a selfie using the provided face image and prompt
    
    Args:
        face_image: The face image to use as identity
        prompt: Text description of how the person should appear
        control_image: Optional control image for pose/pose control
    """
    
    # Validate file types
    if not face_image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Face image must be an image file")
    
    if control_image and not control_image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Control image must be an image file")
    
    # Read image files
    try:
        face_image_data = await face_image.read()
        control_image_data = None
        if control_image:
            control_image_data = await control_image.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading image files: {str(e)}")
    
    # Convert images to base64
    id_image_base64 = image_to_base64(face_image_data)
    control_image_base64 = None
    if control_image_data:
        control_image_base64 = image_to_base64(control_image_data)
    
    # Call RunPod API
    try:
        print(f"🔍 Debug: Calling RunPod API with prompt: {prompt}")
        print(f"🔍 Debug: Image data length: {len(id_image_base64)}")
        result = await call_runpod_api(id_image_base64, prompt, control_image_base64)
        print(f"🔍 Debug: RunPod API returned: {result}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error calling RunPod API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error calling RunPod API: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "InfiniteYou RunPod API Service"}

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "InfiniteYou RunPod API Service",
        "version": "1.0.0",
        "endpoints": {
            "generate-selfie": "/generate-selfie",
            "health": "/health"
        },
        "environment": {
            "runpod_url_set": bool(os.getenv('RUNPOD_INFU_URL')),
            "runpod_api_key_set": bool(os.getenv('RUNPOD_API_KEY'))
        }
    }

if __name__ == "__main__":
    # Run the FastAPI server
    uvicorn.run(
        "image:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
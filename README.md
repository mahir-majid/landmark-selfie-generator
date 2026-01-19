## Project Overview

This project presents an AI powered selfie generation system that places you into iconic real world locations such as Niagara Falls or the Grand Canyon. Upload a face image, choose a location, and generate realistic photos of yourself in that environment.

## Tech Stack

Frontend: Next.js, React, Tailwind  
Backend: FastAPI  
Models: InfiniteYou, FLUX.1 Schnell  
Infra: RunPod GPU (Set VRAM usage to 48 GB)

## Structure

frontend/  
fastapi-backend/  
Infinite-You-Service/  

## Run Frontend Locally

Frontend (Available at http://localhost:3000)

```
cd frontend
npm install
npm run dev
```

## Model Service Deployment

The Infinite-You-Service folder needs to be pushed to its own GitHub repository and used directly by a RunPod serverless endpoint. RunPod handles the container build and deployment.

For proper HuggingFace model download access, set an environment variable called `HF_TOKEN` in the RunPod deployment with access to the following gated repo and custom LoRAs:

https://huggingface.co/black-forest-labs/FLUX.1-schnell  
https://huggingface.co/mahirmajid/Infinite-You-AI-Selfie-LoRAs/tree/main  

The FastAPI backend sends generation requests to this RunPod endpoint.

Configure environment variables `RUNPOD_INFU_URL` and `RUNPOD_API_KEY` in the `.env` file of the fastapi-backend folder based on your RunPod deployment.

## Run Backend Locally

Backend (Available at http://localhost:8000)

```
cd fastapi-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 image.py
```

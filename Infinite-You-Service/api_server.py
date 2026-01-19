import base64
import io
import json
import os
import traceback
from typing import Dict, Any, Optional, Union
from urllib.parse import urlparse

import requests
import runpod
import torch
from PIL import Image
from huggingface_hub import snapshot_download

from pipelines.pipeline_infu_flux import InfUFluxPipeline


class ModelVersion:
    STAGE_1 = "sim_stage1"
    STAGE_2 = "aes_stage2"
    DEFAULT_VERSION = STAGE_2


def log_info(message):
    """Log info message"""
    print(f"ℹ️  [INFO] {message}")

def log_success(message):
    """Log success message"""
    print(f"✅ [SUCCESS] {message}")

def log_warning(message):
    """Log warning message"""
    print(f"⚠️  [WARNING] {message}")

def log_error(message):
    """Log error message"""
    print(f"❌ [ERROR] {message}")

def log_step(message):
    """Log step message"""
    print(f"🔄 [STEP] {message}")

def verify_models():
    """Verify that all required models are available"""
    log_step("Verifying model availability...")
    
    required_paths = [
        './models/InfiniteYou/infu_flux_v1.0/sim_stage1',
        './models/InfiniteYou/infu_flux_v1.0/aes_stage2',
        './models/InfiniteYou/supports/insightface',
        './models/InfiniteYou/supports/optional_loras',
        # './models/FLUX.1-dev',  # Commented out for now
        './models/FLUX.1-schnell'
        # './models/FLUX.1-Krea-dev'  # Commented out for now
    ]
    
    missing_paths = []
    for path in required_paths:
        if not os.path.exists(path):
            missing_paths.append(path)
        else:
            log_info(f"✓ Found: {path}")
    
    if missing_paths:
        log_warning("Some model directories are missing:")
        for path in missing_paths:
            log_warning(f"   - {path}")
        log_info("Attempting to download missing models...")
        
        # Try to download missing models
        try:
            from download_models import main as download_models_main
            download_models_main()
            log_success("Models downloaded successfully")
            return True
        except Exception as e:
            log_error(f"Failed to download models: {e}")
            log_error("Please ensure you have access to the required models")
            log_info("Visit: https://huggingface.co/black-forest-labs/FLUX.1-dev")
            log_info("Set HF_TOKEN environment variable if needed")
            return False
    else:
        log_success("All required model directories found")
        return True

def check_gpu():
    """Check GPU availability"""
    log_step("Checking GPU availability...")
    
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        log_success(f"GPU available: {gpu_name}")
        log_info(f"GPU Memory: {gpu_memory:.1f} GB")
        return True
    else:
        log_error("No GPU available")
        return False


class InfiniteYouAPI:
    def __init__(self):
        self.pipeline = None
        self.model_version = None
        self.enable_realism = False
        self.enable_anti_blur = False
        
        # Verify models on startup
        if not verify_models():
            raise RuntimeError("Required models not found. Please ensure models are downloaded.")
        
        if not check_gpu():
            raise RuntimeError("GPU not available. This service requires GPU acceleration.")
        
        log_success("InfiniteYou API initialized successfully")
        
    def _load_image_from_base64(self, base64_string: str) -> Image.Image:
        """Load image from base64 string"""
        try:
            # Remove data URL prefix if present
            if base64_string.startswith('data:image'):
                base64_string = base64_string.split(',')[1]
            
            image_data = base64.b64decode(base64_string)
            image = Image.open(io.BytesIO(image_data))
            return image.convert('RGB')
        except Exception as e:
            raise ValueError(f"Failed to load image from base64: {str(e)}")
    
    def _prepare_pipeline(self, model_version: str, flux_model: str, 
                         enable_realism: bool = True, enable_anti_blur: bool = False,
                         enable_face_realism: bool = False, enable_realism_one: bool = False, enable_realism_two: bool = False,
                         realism_weight: float = 1.0, anti_blur_weight: float = 1.0,
                         face_realism_weight: float = 1.0, realism_one_weight: float = 1.0, realism_two_weight: float = 1.0):
        """Prepare the pipeline with specified configuration"""
        if (
            self.pipeline is not None
            and self.enable_realism == enable_realism 
            and self.enable_anti_blur == enable_anti_blur
            and self.enable_face_realism == enable_face_realism
            and self.enable_realism_one == enable_realism_one
            and self.enable_realism_two == enable_realism_two
            and model_version == self.model_version
            and flux_model == getattr(self, 'flux_model', None)
        ):
            return self.pipeline
        
        self.enable_realism = enable_realism
        self.enable_anti_blur = enable_anti_blur
        self.enable_face_realism = enable_face_realism
        self.enable_realism_one = enable_realism_one
        self.enable_realism_two = enable_realism_two
        self.model_version = model_version
        self.flux_model = flux_model

        # Validate flux_model parameter
        if flux_model not in ["flux-schnell"]:
            raise ValueError(f"Invalid flux_model: {flux_model}. Must be 'flux-schnell'")

        # Determine base model path
        if flux_model == "flux-schnell":
            base_model_path = './models/FLUX.1-schnell'


        # Check if the requested model exists
        if not os.path.exists(base_model_path):
            raise RuntimeError(f"{flux_model} models not found at {base_model_path}. Please ensure models are downloaded during startup.")

        if self.pipeline is None or self.pipeline.model_version != model_version or getattr(self, 'flux_model', None) != flux_model:
            log_info(f'Switching model to {model_version} with {flux_model}')
            del self.pipeline
            torch.cuda.empty_cache()

            model_path = f'./models/InfiniteYou/infu_flux_v1.0/{model_version}'
            log_info(f'Loading model from {model_path}')
            
            # Check if models exist before loading
            if not os.path.exists(model_path):
                raise RuntimeError(f"Model not found at {model_path}. Please ensure models are downloaded during startup.")

            self.pipeline = InfUFluxPipeline(
                base_model_path=base_model_path,
                infu_model_path=model_path,
                insightface_root_path='./models/InfiniteYou/supports/insightface',
                image_proj_num_tokens=8,
                infu_flux_version='v1.0',
                model_version=model_version,
            )

        # Apply LoRAs if enabled
        self.pipeline.pipe.delete_adapters(['realism', 'anti_blur', 'face_realism', 'realism_one', 'realism_two'])
        self.pipeline.pipe.unload_lora_weights()
        loras = []
        
        log_info(f"PREPARING THE LORAS IF ANY!")
        # Original LoRAs
        if enable_realism:
            loras.append(['./models/InfiniteYou/supports/optional_loras/flux_realism_lora.safetensors', 'realism', realism_weight])
        if enable_anti_blur:
            loras.append(['./models/InfiniteYou/supports/optional_loras/flux_anti_blur_lora.safetensors', 'anti_blur', anti_blur_weight])
        
        # Custom LoRAs
        if enable_face_realism:
            loras.append(['./models/InfiniteYou/supports/optional_loras/Canopus-LoRA-Flux-FaceRealism.safetensors', 'face_realism', face_realism_weight])
        if enable_realism_one:
            loras.append(['./models/InfiniteYou/supports/optional_loras/schnell-realism_v1.safetensors', 'realism_one', realism_one_weight])
        if enable_realism_two:
            loras.append(['./models/InfiniteYou/supports/optional_loras/schnell-realism_v2.3.safetensors', 'realism_two', realism_two_weight])
        
        # Log LoRA configuration
        if loras:
            log_info(f"Loading {len(loras)} LoRA(s):")
            for lora_path, adapter_name, weight in loras:
                log_info(f"  - {adapter_name} (weight: {weight})")
        else:
            log_info("No LoRAs enabled for this generation")
        
        for lora_path, adapter_name, weight in loras:
            if os.path.exists(lora_path):
                self.pipeline.pipe.load_lora_weights(lora_path, adapter_name=adapter_name, weight=weight)
                log_info(f"✅ Successfully loaded LoRA: {adapter_name} with weight {weight}")
            else:
                log_warning(f"❌ LoRA file not found: {lora_path}")

        return self.pipeline
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL image to base64 string"""
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return img_str
    
    def generate_image(self, 
                      id_image: Union[str, Image.Image],
                      prompt: str,
                      control_image: Optional[Union[str, Image.Image]] = None,
                      seed: int = 0,
                      width: int = 864,
                      height: int = 1152,
                      guidance_scale: float = 3.5,
                      num_steps: int = 30,
                      infusenet_conditioning_scale: float = 1.0,
                      infusenet_guidance_start: float = 0.0,
                      infusenet_guidance_end: float = 1.0,
                      enable_realism: bool = True,
                      enable_anti_blur: bool = False,
                      enable_face_realism: bool = False,
                      enable_realism_one: bool = False,
                      enable_realism_two: bool = False,
                      realism_weight: float = 1.0,
                      anti_blur_weight: float = 1.0,
                      face_realism_weight: float = 1.0,
                      realism_one_weight: float = 1.0,
                      realism_two_weight: float = 1.0,
                      infu_source_img_token: str = "PERSON_1",
                      model_version: str = ModelVersion.DEFAULT_VERSION,
                      flux_model: str = "flux-dev") -> Dict[str, Any]:
        """
        Generate image using InfiniteYou-FLUX model
        
        Args:
            id_image: Identity image (base64 string or PIL Image)
            prompt: Text prompt for generation
            control_image: Optional control image (base64 string or PIL Image)
            seed: Random seed (0 for random)
            width: Output image width
            height: Output image height
            guidance_scale: Guidance scale for generation
            num_steps: Number of inference steps
            infusenet_conditioning_scale: InfuseNet conditioning scale
            infusenet_guidance_start: InfuseNet guidance start
            infusenet_guidance_end: InfuseNet guidance end
            enable_realism: Enable realism LoRA
            enable_anti_blur: Enable anti-blur LoRA
            enable_face_realism: Enable face realism LoRA
            enable_realism_one: Enable realism one LoRA
            enable_realism_two: Enable realism two LoRA
            realism_weight: Weight for realism LoRA (0.0-2.0)
            anti_blur_weight: Weight for anti-blur LoRA (0.0-2.0)
            face_realism_weight: Weight for face realism LoRA (0.0-2.0)
            realism_one_weight: Weight for realism one LoRA (0.0-2.0)
            realism_two_weight: Weight for realism two LoRA (0.0-2.0)
            infu_source_img_token: Token to associate with input image identity (default: "PERSON_1")
            model_version: Model version to use
            
        Returns:
            Dictionary containing the generated image as base64 and metadata
        """
        try:
            # Load identity image
            if isinstance(id_image, str):
                id_image = self._load_image_from_base64(id_image)
            
            # Load control image if provided
            if control_image is not None:
                if isinstance(control_image, str):
                    control_image = self._load_image_from_base64(control_image)
            
            # Prepare pipeline
            pipeline = self._prepare_pipeline(
                model_version=model_version,
                flux_model=flux_model,
                enable_realism=enable_realism,
                enable_anti_blur=enable_anti_blur,
                enable_face_realism=enable_face_realism,
                enable_realism_one=enable_realism_one,
                enable_realism_two=enable_realism_two,
                realism_weight=realism_weight,
                anti_blur_weight=anti_blur_weight,
                face_realism_weight=face_realism_weight,
                realism_one_weight=realism_one_weight,
                realism_two_weight=realism_two_weight
            )
            
            # Set seed
            if seed == 0:
                seed = torch.seed() & 0xFFFFFFFF
            
            # Generate image
            generated_image = pipeline(
                id_image=id_image,
                prompt=prompt,
                control_image=control_image,
                seed=seed,
                width=width,
                height=height,
                guidance_scale=guidance_scale,
                num_steps=num_steps,
                infusenet_conditioning_scale=infusenet_conditioning_scale,
                infusenet_guidance_start=infusenet_guidance_start,
                infusenet_guidance_end=infusenet_guidance_end,
                infu_source_img_token=infu_source_img_token,
            )
            
            # Convert to base64
            image_base64 = self._image_to_base64(generated_image)
            
            return {
                "success": True,
                "image": image_base64,
                "metadata": {
                    "seed": seed,
                    "model_version": model_version,
                    "prompt": prompt,
                    "width": width,
                    "height": height,
                    "guidance_scale": guidance_scale,
                    "num_steps": num_steps,
                    "enable_realism": enable_realism,
                    "enable_anti_blur": enable_anti_blur,
                    "enable_face_realism": enable_face_realism,
                    "enable_realism_one": enable_realism_one,
                    "enable_realism_two": enable_realism_two,
                    "realism_weight": realism_weight,
                    "anti_blur_weight": anti_blur_weight,
                    "face_realism_weight": face_realism_weight,
                    "realism_one_weight": realism_one_weight,
                    "realism_two_weight": realism_two_weight,
                    "infu_source_img_token": infu_source_img_token
                }
            }
            
        except Exception as e:
            error_msg = f"Error generating image: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            return {
                "success": False,
                "error": error_msg
            }


# Initialize the API instance
api = InfiniteYouAPI()

def handler(job):
    """
    RunPod handler function
    
    Expected input format:
    {
        "id_images": [  # NEW: List of ID images with labels
            {
                "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ...",
                "label": "ENT1"
            },
            {
                "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ...", 
                "label": "ENT2"
            }
        ],
        "prompt": "ENT1 and ENT2 walking in the park",
        "control_image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ...",  # optional base64 string
        "seed": 42,  # optional, 0 for random
        "width": 864,  # optional
        "height": 1152,  # optional
        "guidance_scale": 3.5,  # optional
        "num_steps": 30,  # optional
        "infusenet_conditioning_scale": 1.0,  # optional
        "infusenet_guidance_start": 0.0,  # optional
        "infusenet_guidance_end": 1.0,  # optional
        "enable_realism": true,  # optional
        "enable_anti_blur": false,  # optional
        "enable_face_realism": false,  # optional
        "enable_realism_one": false,  # optional
        "enable_realism_two": false,  # optional
        "realism_weight": 1.0,  # optional, 0.0-2.0
        "anti_blur_weight": 1.0,  # optional, 0.0-2.0
        "face_realism_weight": 1.0,  # optional, 0.0-2.0
        "realism_one_weight": 1.0,  # optional, 0.0-2.0
        "realism_two_weight": 1.0,  # optional, 0.0-2.0
        "model_version": "sim_stage1",  # optional, "sim_stage1" or "aes_stage2"
        "flux_model": "flux-schnell"  # optional, "flux-schnell" only
    }
    
    LEGACY format still supported:
    {
        "id_image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ...",  # base64 string
        "prompt": "A sophisticated gentleman in a business suit",
        # ... other parameters
    }
    """
    try:
        # Parse input
        input_data = job["input"]
        
        # Check if using new multi-ID format or legacy single-ID format
        if "id_images" in input_data:
            # NEW: Multi-ID format
            id_images_data = input_data["id_images"]
            if not isinstance(id_images_data, list) or len(id_images_data) == 0:
                return {"error": "id_images must be a non-empty list"}
            
            # Validate each ID image entry
            for i, id_data in enumerate(id_images_data):
                if not isinstance(id_data, dict) or "image" not in id_data or "label" not in id_data:
                    return {"error": f"id_images[{i}] must have 'image' and 'label' fields"}
                if not isinstance(id_data["label"], str):
                    return {"error": f"id_images[{i}].label must be a string"}
            
            # Extract parameters with defaults
            prompt = input_data.get("prompt", "")
            if not prompt:
                return {"error": "prompt is required"}
                
            control_image = input_data.get("control_image")
            seed = input_data.get("seed", 0)
            width = input_data.get("width", 864)
            height = input_data.get("height", 1152)
            guidance_scale = input_data.get("guidance_scale", 3.5)
            num_steps = input_data.get("num_steps", 30)
            infusenet_conditioning_scale = input_data.get("infusenet_conditioning_scale", 1.0)
            infusenet_guidance_start = input_data.get("infusenet_guidance_start", 0.0)
            infusenet_guidance_end = input_data.get("infusenet_guidance_end", 1.0)
            enable_realism = input_data.get("enable_realism", True)
            enable_anti_blur = input_data.get("enable_anti_blur", False)
            enable_face_realism = input_data.get("enable_face_realism", False)
            enable_realism_one = input_data.get("enable_realism_one", False)
            enable_realism_two = input_data.get("enable_realism_two", False)
            realism_weight = input_data.get("realism_weight", 1.0)
            anti_blur_weight = input_data.get("anti_blur_weight", 1.0)
            face_realism_weight = input_data.get("face_realism_weight", 1.0)
            realism_one_weight = input_data.get("realism_one_weight", 1.0)
            realism_two_weight = input_data.get("realism_two_weight", 1.0)
            model_version = input_data.get("model_version", ModelVersion.DEFAULT_VERSION)
            flux_model = input_data.get("flux_model", "flux-schnell")
            
            # Validate model version
            if model_version not in [ModelVersion.STAGE_1, ModelVersion.STAGE_2]:
                return {"error": f"Invalid model_version. Must be one of: {ModelVersion.STAGE_1}, {ModelVersion.STAGE_2}"}
            
            # Validate flux_model
            if flux_model not in ["flux-schnell"]:
                return {"error": f"Invalid flux_model. Must be 'flux-schnell'"}
            
            # Generate image with multiple IDs
            result = api.generate_multi_image(
                id_images_data=id_images_data,
                prompt=prompt,
                control_image=control_image,
                seed=seed,
                width=width,
                height=height,
                guidance_scale=guidance_scale,
                num_steps=num_steps,
                infusenet_conditioning_scale=infusenet_conditioning_scale,
                infusenet_guidance_start=infusenet_guidance_start,
                infusenet_guidance_end=infusenet_guidance_end,
                enable_realism=enable_realism,
                enable_anti_blur=enable_anti_blur,
                enable_face_realism=enable_face_realism,
                enable_realism_one=enable_realism_one,
                enable_realism_two=enable_realism_two,
                realism_weight=realism_weight,
                anti_blur_weight=anti_blur_weight,
                face_realism_weight=face_realism_weight,
                realism_one_weight=realism_one_weight,
                realism_two_weight=realism_two_weight,
                model_version=model_version,
                flux_model=flux_model
            )
            
        elif "id_image" in input_data:
            # LEGACY: Single-ID format (backward compatibility)
            id_image = input_data["id_image"]
            prompt = input_data.get("prompt", "")
            if not prompt:
                return {"error": "prompt is required"}
                
            control_image = input_data.get("control_image")
            seed = input_data.get("seed", 0)
            width = input_data.get("width", 864)
            height = input_data.get("height", 1152)
            guidance_scale = input_data.get("guidance_scale", 3.5)
            num_steps = input_data.get("num_steps", 30)
            infusenet_conditioning_scale = input_data.get("infusenet_conditioning_scale", 1.0)
            infusenet_guidance_start = input_data.get("infusenet_guidance_start", 0.0)
            infusenet_guidance_end = input_data.get("infusenet_guidance_end", 1.0)
            enable_realism = input_data.get("enable_realism", True)
            enable_anti_blur = input_data.get("enable_anti_blur", False)
            enable_face_realism = input_data.get("enable_face_realism", False)
            enable_realism_one = input_data.get("enable_realism_one", False)
            enable_realism_two = input_data.get("enable_realism_two", False)
            realism_weight = input_data.get("realism_weight", 1.0)
            anti_blur_weight = input_data.get("anti_blur_weight", 1.0)
            face_realism_weight = input_data.get("face_realism_weight", 1.0)
            realism_one_weight = input_data.get("realism_one_weight", 1.0)
            realism_two_weight = input_data.get("realism_two_weight", 1.0)
            infu_source_img_token = input_data.get("infu_source_img_token", "PERSON_1")
            model_version = input_data.get("model_version", ModelVersion.DEFAULT_VERSION)
            flux_model = input_data.get("flux_model", "flux-schnell")
            
            # Validate model version
            if model_version not in [ModelVersion.STAGE_1, ModelVersion.STAGE_2]:
                return {"error": f"Invalid model_version. Must be one of: {ModelVersion.STAGE_1}, {ModelVersion.STAGE_2}"}
            
            # Validate flux_model
            if flux_model not in ["flux-schnell"]:
                return {"error": f"Invalid flux_model. Must be 'flux-schnell'"}
            
            # Generate image with single ID (legacy method)
            result = api.generate_image(
                id_image=id_image,
                prompt=prompt,
                control_image=control_image,
                seed=seed,
                width=width,
                height=height,
                guidance_scale=guidance_scale,
                num_steps=num_steps,
                infusenet_conditioning_scale=infusenet_conditioning_scale,
                infusenet_guidance_start=infusenet_guidance_start,
                infusenet_guidance_end=infusenet_guidance_end,
                enable_realism=enable_realism,
                enable_anti_blur=enable_anti_blur,
                enable_face_realism=enable_face_realism,
                enable_realism_one=enable_realism_one,
                enable_realism_two=enable_realism_two,
                realism_weight=realism_weight,
                anti_blur_weight=anti_blur_weight,
                face_realism_weight=face_realism_weight,
                realism_one_weight=realism_one_weight,
                realism_two_weight=realism_two_weight,
                infu_source_img_token=infu_source_img_token,
                model_version=model_version,
                flux_model=flux_model
            )
        else:
            return {"error": "Either 'id_images' (multi-ID) or 'id_image' (single-ID) must be provided"}
        
        return result
        
    except Exception as e:
        error_msg = f"Handler error: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        return {"error": error_msg}


# Start the RunPod serverless handler
runpod.serverless.start({"handler": handler})
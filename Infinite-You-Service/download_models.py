#!/usr/bin/env python3
"""
Download script for InfiniteYou-FLUX models
This script downloads all necessary models for the RunPod API server.
"""

import os
import sys
import time
import shutil
from pathlib import Path
from huggingface_hub import snapshot_download, login
import torch

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

def log_progress(message):
    """Log progress message"""
    print(f"📊 [PROGRESS] {message}")

def check_hf_token():
    """Check if HuggingFace token is available and valid"""
    token = os.getenv('HF_TOKEN')
    
    if token:
        print(f"HF_TOKEN found: {token[:10]}..." if len(token) > 10 else f"HF_TOKEN: {token}")
        try:
            login(token)
            log_success("Successfully logged in to HuggingFace")
            return True
        except Exception as e:
            log_error(f"Failed to login with token: {e}")
            return False
    else:
        log_warning("HF_TOKEN not set")
        log_info("You may need to set it for private model access")
        log_info("Visit: https://huggingface.co/settings/tokens")
        return False

def get_directory_size(path):
    """Get directory size in GB"""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
        return total_size / (1024**3)
    except Exception:
        return 0

def download_infiniteyou_models():
    """Download InfiniteYou models"""
    log_step("Downloading InfiniteYou models...")
    log_info("Repository: ByteDance/InfiniteYou")
    log_info("This model contains the core InfiniteYou architecture")
    
    # Get token
    token = os.getenv("HF_TOKEN")
    
    # Check if already downloaded
    if os.path.exists('./models/InfiniteYou'):
        size = get_directory_size('./models/InfiniteYou')
        log_info(f"InfiniteYou models already exist ({size:.1f} GB)")
        log_success("InfiniteYou models found")
        return True
    
    try:
        log_progress("Starting download...")
        start_time = time.time()
        
        snapshot_download(
            repo_id='ByteDance/InfiniteYou',
            local_dir='./models/InfiniteYou',
            local_dir_use_symlinks=False,
            resume_download=True,
            token=token
        )
        
        download_time = time.time() - start_time
        size = get_directory_size('./models/InfiniteYou')
        
        log_success(f"InfiniteYou models downloaded successfully")
        log_info(f"Download time: {download_time:.1f} seconds")
        log_info(f"Model size: {size:.1f} GB")
        return True
    except Exception as e:
        log_error(f"Error downloading InfiniteYou models: {e}")
        log_info("\n📋 Troubleshooting:")
        log_info("1. Make sure you have access to ByteDance/InfiniteYou")
        log_info("2. Set HF_TOKEN environment variable if needed")
        log_info("3. Check your internet connection")
        log_info("4. Visit: https://huggingface.co/ByteDance/InfiniteYou")
        return False

def download_flux_models():
    """Download both FLUX.1-dev and FLUX.1-schnell models"""
    log_step("Downloading FLUX models...")
    
    # Get token
    token = os.getenv("HF_TOKEN")
    
    # Download FLUX.1-schnell
    log_info("Downloading FLUX.1-schnell...")
    log_info("Repository: black-forest-labs/FLUX.1-schnell")
    
    if not os.path.exists('./models/FLUX.1-schnell'):
        try:
            log_progress("Starting FLUX.1-schnell download...")
            start_time = time.time()
            
            snapshot_download(
                repo_id='black-forest-labs/FLUX.1-schnell',
                local_dir='./models/FLUX.1-schnell',
                local_dir_use_symlinks=False,
                resume_download=True,
                token=token
            )
            
            download_time = time.time() - start_time
            size = get_directory_size('./models/FLUX.1-schnell')
            
            log_success(f"FLUX.1-schnell models downloaded successfully")
            log_info(f"Download time: {download_time:.1f} seconds")
            log_info(f"Model size: {size:.1f} GB")
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "restricted" in error_msg.lower() or "access" in error_msg.lower():
                log_error(f"Authentication required for FLUX.1-schnell model")
                log_info("Please visit: https://huggingface.co/black-forest-labs/FLUX.1-schnell")
                log_info("1. Request access to the model")
                log_info("2. Accept the terms and conditions")
                log_info("3. Set your HF_TOKEN environment variable")
                return False
            else:
                log_error(f"Error downloading FLUX.1-schnell models: {e}")
                return False
    else:
        size = get_directory_size('./models/FLUX.1-schnell')
        log_info(f"FLUX.1-schnell models already exist ({size:.1f} GB)")

    
    log_success("Neccessary FLUX models downloaded successfully")
    return True

def download_custom_loras():
    """Download custom LoRAs from private repository"""
    log_step("Downloading custom LoRAs...")
    log_info("Repository: mahirmajid/Infinite-You-AI-Selfie-LoRAs")
    
    # Get token
    token = os.getenv("HF_TOKEN")
    
    # Check if already downloaded
    if os.path.exists('./models/custom_loras'):
        size = get_directory_size('./models/custom_loras')
        log_info(f"Custom LoRAs already exist ({size:.1f} GB)")
        log_success("Custom LoRAs found")
        return True
    
    try:
        log_progress("Starting custom LoRAs download...")
        start_time = time.time()
        
        snapshot_download(
            repo_id='mahirmajid/Infinite-You-AI-Selfie-LoRAs',
            local_dir='./models/custom_loras',
            local_dir_use_symlinks=False,
            resume_download=True,
            token=token
        )
        
        download_time = time.time() - start_time
        size = get_directory_size('./models/custom_loras')
        
        log_success(f"Custom LoRAs downloaded successfully")
        log_info(f"Download time: {download_time:.1f} seconds")
        log_info(f"Model size: {size:.1f} GB")
        
        # Copy LoRAs to the InfiniteYou directory
        log_step("Copying LoRAs to InfiniteYou directory...")
        import shutil
        
        source_dir = './models/custom_loras'
        target_dir = './models/InfiniteYou/supports/optional_loras/'
        
        # Ensure target directory exists
        os.makedirs(target_dir, exist_ok=True)
        
        # Copy safetensors files
        for file in os.listdir(source_dir):
            if file.endswith('.safetensors'):
                source_file = os.path.join(source_dir, file)
                target_file = os.path.join(target_dir, file)
                shutil.copy2(source_file, target_file)
                log_info(f"Copied: {file}")
        
        log_success("Custom LoRAs copied to InfiniteYou directory")
        return True
        
    except Exception as e:
        log_error(f"Error downloading custom LoRAs: {e}")
        log_info("\n📋 Troubleshooting:")
        log_info("1. Make sure you have access to mahirmajid/Infinite-You-AI-Selfie-LoRAs")
        log_info("2. Check your HF_TOKEN environment variable")
        log_info("3. Check your internet connection")
        return False

def verify_model_structure():
    """Verify that all required model files are present"""
    log_step("Verifying model structure...")
    
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
        log_error("Missing model directories:")
        for path in missing_paths:
            log_error(f"   - {path}")
        return False
    else:
        log_success("All required model directories found")
        return True

def check_disk_space():
    """Check available disk space"""
    log_step("Checking disk space...")
    
    # Estimate required space (models are several GB)
    required_gb = 15  # Conservative estimate
    
    try:
        stat = os.statvfs('.')
        available_gb = (stat.f_frsize * stat.f_bavail) / (1024**3)
        
        log_info(f"Available: {available_gb:.1f} GB")
        log_info(f"Required: ~{required_gb} GB")
        
        if available_gb < required_gb:
            log_warning(f"Low disk space ({available_gb:.1f} GB available)")
            log_warning("Download may fail if insufficient space")
            return False
        else:
            log_success("Sufficient disk space available")
            return True
    except Exception as e:
        log_warning(f"Could not check disk space: {e}")
        return True  # Assume OK if we can't check

def check_network_connectivity():
    """Check network connectivity to HuggingFace"""
    log_step("Checking network connectivity...")
    
    try:
        import requests
        response = requests.get("https://huggingface.co", timeout=10)
        if response.status_code == 200:
            log_success("Network connectivity to HuggingFace confirmed")
            return True
        else:
            log_warning(f"HuggingFace returned status code: {response.status_code}")
            return False
    except Exception as e:
        log_error(f"Network connectivity check failed: {e}")
        log_info("Please check your internet connection")
        return False

def main():
    """Main download function"""
    print("🚀 InfiniteYou-FLUX Model Downloader")
    print("=" * 50)
    
    # Check environment
    log_step("Checking environment...")
    token_status = check_hf_token()
    
    # Show token status summary
    if token_status:
        log_info("✅ HF_TOKEN is valid and ready for private model access")
    else:
        log_warning("⚠️  HF_TOKEN is missing or invalid - FLUX.1-dev download may fail")
        log_info("Public models (InfiniteYou) will still download successfully")
    
    # Check network connectivity
    if not check_network_connectivity():
        log_error("Network connectivity issues detected")
        sys.exit(1)
    
    # Check disk space
    if not check_disk_space():
        log_warning("Proceeding with download despite low disk space")
    
    # Create models directory
    log_step("Setting up directories...")
    os.makedirs('./models', exist_ok=True)
    log_success("Models directory ready")
    
    # Download models
    success = True
    
    if not download_infiniteyou_models():
        success = False
    
    if not download_flux_models():
        success = False
    
    if not download_custom_loras():
        success = False
    
    # Verify structure
    if success and not verify_model_structure():
        success = False
    
    # Final status
    print("\n" + "=" * 50)
    if success:
        log_success("All models downloaded successfully!")
        log_info("Ready to run the InfiniteYou API server")
        
        # Show model sizes
        try:
            total_size = 0
            for root, dirs, files in os.walk('./models'):
                for file in files:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
            
            log_info(f"Total model size: {total_size / (1024**3):.1f} GB")
            
            # Show available disk space after download
            stat = os.statvfs('.')
            available_gb = (stat.f_frsize * stat.f_bavail) / (1024**3)
            log_info(f"Remaining disk space: {available_gb:.1f} GB")
            
        except Exception as e:
            log_warning(f"Could not calculate total size: {e}")
    else:
        log_error("Model download failed. Please check the errors above.")
        if not token_status:
            log_info("\n💡 To fix FLUX.1-dev download issues:")
            log_info("1. Get a new HF_TOKEN from: https://huggingface.co/settings/tokens")
            log_info("2. Accept FLUX.1-dev terms at: https://huggingface.co/black-forest-labs/FLUX.1-dev")
            log_info("3. Set HF_TOKEN environment variable")
            log_info("4. Restart the build process")
        sys.exit(1)

if __name__ == "__main__":
    main()

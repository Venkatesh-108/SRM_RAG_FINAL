#!/usr/bin/env python3
"""
Simple script to download Docling models to a local folder
Run this once in an environment with internet access
"""

import os
from pathlib import Path
from huggingface_hub import snapshot_download

def download_models():
    """Download Docling models to ./models folder"""
    
    # Create models directory
    models_dir = Path("./models")
    models_dir.mkdir(exist_ok=True)
    
    print(f"Downloading models to: {models_dir.absolute()}")
    
    # Download the required model
    snapshot_download(
        repo_id="ds4sd/docling-models",
        cache_dir=str(models_dir),
        local_files_only=False
    )
    
    print("✅ Models downloaded successfully!")
    print(f"📁 Models location: {models_dir.absolute()}")
    print("📋 Copy this 'models' folder to your customer location")

if __name__ == "__main__":
    download_models()

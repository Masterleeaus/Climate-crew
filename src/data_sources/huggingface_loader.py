import os
import logging
from typing import List, Dict, Any, Optional
from datasets import load_dataset
from PIL import Image
import requests
from io import BytesIO

# Allow large satellite images
Image.MAX_IMAGE_PIXELS = None

logger = logging.getLogger(__name__)

class HuggingFaceLoader:    
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir

    def load_text_dataset(
        self, 
        dataset_name: str, 
        split: str = "train", 
        text_column: str = "text", 
        format_string: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        try:
            logger.info(f"Loading dataset '{dataset_name}' (split={split})...")
            dataset = load_dataset(dataset_name, split=split, streaming=True)
            
            documents = []
            count = 0
            
            for row in dataset:
                if count >= limit:
                    break
                
                if format_string:
                    try:
                        text_content = format_string.format(**row)
                    except KeyError as e:
                        logger.warning(f"Row missing key for format string: {e}")
                        continue
                else:
                    text_content = row.get(text_column)

                if not text_content:
                    continue
                
                # Create metadata from other columns
                metadata = {k: v for k, v in row.items() if k != text_column}
                metadata["source"] = f"huggingface:{dataset_name}"
                
                documents.append({
                    "text": str(text_content),
                    "metadata": metadata
                })
                count += 1
                
            logger.info(f"Successfully loaded {len(documents)} text documents from {dataset_name}")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to load text dataset {dataset_name}: {e}")
            return []

    def download_image_samples(
        self, 
        dataset_name: str, 
        output_dir: str, 
        image_column: str = "image", 
        split: str = "train", 
        limit: int = 100
    ):
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            logger.info(f"Downloading {limit} sample images from '{dataset_name}' to {output_dir}...")
            dataset = load_dataset(dataset_name, split=split, streaming=True)
            
            count = 0
            for row in dataset:
                if count >= limit:
                    break
                
                # Debug logging
                if count == 0:
                    logger.info(f"First row keys: {row.keys()}")

                image_data = row.get(image_column)
                
                if image_data:
                    # Handle different image formats (PIL keys vs raw bytes)
                    img = None
                    if isinstance(image_data, Image.Image):
                        img = image_data
                    elif isinstance(image_data, dict) and "bytes" in image_data:
                         img = Image.open(BytesIO(image_data["bytes"]))
                    
                    if img:
                        file_path = os.path.join(output_dir, f"sample_{count}.png")
                        img.save(file_path)
                        logger.info(f"Saved {file_path}")
                        count += 1
                        
            logger.info(f"Finished downloading {count} images.")
            
        except Exception as e:
            logger.error(f"Failed to download images from {dataset_name}: {e}")

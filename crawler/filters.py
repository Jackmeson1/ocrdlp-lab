"""
Image filtering utilities for quality and size validation.
"""

import os
import asyncio
from typing import Union
from pathlib import Path
from PIL import Image
import logging


class ImageFilter:
    """Filter images based on size, format, and quality criteria."""
    
    def __init__(self, 
                 min_size: int = 300,
                 max_size: int = 4096,
                 min_file_size: int = 5000,  # 5KB
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 allowed_formats: tuple = ('JPEG', 'PNG', 'WEBP')):
        self.min_size = min_size
        self.max_size = max_size
        self.min_file_size = min_file_size
        self.max_file_size = max_file_size
        self.allowed_formats = allowed_formats
        self.logger = logging.getLogger(__name__)
    
    async def is_valid_image(self, filepath: Union[str, Path]) -> bool:
        """Check if image meets all filtering criteria."""
        filepath = Path(filepath)
        
        try:
            # Check file size
            file_size = filepath.stat().st_size
            if file_size < self.min_file_size or file_size > self.max_file_size:
                self.logger.debug(f"File size check failed for {filepath.name}: {file_size} bytes")
                return False
            
            # Run image checks in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._check_image_properties, filepath)
            
        except Exception as e:
            self.logger.error(f"Error validating image {filepath}: {e}")
            return False
    
    def _check_image_properties(self, filepath: Path) -> bool:
        """Check image properties (runs in thread pool)."""
        try:
            with Image.open(filepath) as img:
                # Check format
                if img.format not in self.allowed_formats:
                    self.logger.debug(f"Format check failed for {filepath.name}: {img.format}")
                    return False
                
                # Check dimensions
                width, height = img.size
                if (width < self.min_size or height < self.min_size or 
                    width > self.max_size or height > self.max_size):
                    self.logger.debug(f"Size check failed for {filepath.name}: {width}x{height}")
                    return False
                
                # Check aspect ratio (avoid extremely narrow images)
                aspect_ratio = max(width, height) / min(width, height)
                if aspect_ratio > 10:  # Too narrow/wide
                    self.logger.debug(f"Aspect ratio check failed for {filepath.name}: {aspect_ratio}")
                    return False
                
                # Check if image is corrupted by trying to load it
                img.load()
                
                return True
                
        except Exception as e:
            self.logger.debug(f"Image validation failed for {filepath.name}: {e}")
            return False
    
    def get_image_info(self, filepath: Union[str, Path]) -> dict:
        """Get detailed image information."""
        filepath = Path(filepath)
        
        try:
            with Image.open(filepath) as img:
                return {
                    'filename': filepath.name,
                    'format': img.format,
                    'size': img.size,
                    'mode': img.mode,
                    'file_size': filepath.stat().st_size,
                    'has_transparency': img.mode in ('RGBA', 'LA') or 'transparency' in img.info
                }
        except Exception as e:
            return {'filename': filepath.name, 'error': str(e)} 
"""
Image deduplication using perceptual hashing.
"""

import asyncio
import json
from typing import Union, Set, Dict
from pathlib import Path
import imagehash
from PIL import Image
import logging


class ImageDeduplicator:
    """Detect and remove duplicate images using perceptual hashing."""
    
    def __init__(self, 
                 hash_size: int = 8,
                 threshold: int = 5,
                 hash_db_path: str = "ocr_dataset/image_hashes.json"):
        self.hash_size = hash_size
        self.threshold = threshold
        self.hash_db_path = Path(hash_db_path)
        self.hash_db: Dict[str, str] = {}
        self.logger = logging.getLogger(__name__)
        
        # Load existing hash database
        self._load_hash_db()
    
    def _load_hash_db(self):
        """Load existing hash database from disk."""
        try:
            if self.hash_db_path.exists():
                with open(self.hash_db_path, 'r') as f:
                    self.hash_db = json.load(f)
                self.logger.info(f"Loaded {len(self.hash_db)} existing hashes")
        except Exception as e:
            self.logger.warning(f"Could not load hash database: {e}")
            self.hash_db = {}
    
    def _save_hash_db(self):
        """Save hash database to disk."""
        try:
            self.hash_db_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.hash_db_path, 'w') as f:
                json.dump(self.hash_db, f, indent=2)
        except Exception as e:
            self.logger.error(f"Could not save hash database: {e}")
    
    async def is_duplicate(self, filepath: Union[str, Path]) -> bool:
        """Check if image is a duplicate of existing images."""
        filepath = Path(filepath)
        
        try:
            # Calculate hash in thread pool
            loop = asyncio.get_event_loop()
            image_hash = await loop.run_in_executor(None, self._calculate_hash, filepath)
            
            if image_hash is None:
                return False
            
            # Check against existing hashes
            hash_str = str(image_hash)
            
            for existing_hash, existing_file in self.hash_db.items():
                # Calculate Hamming distance
                try:
                    existing_hash_obj = imagehash.hex_to_hash(existing_hash)
                    distance = image_hash - existing_hash_obj
                    
                    if distance <= self.threshold:
                        self.logger.debug(f"Duplicate found: {filepath.name} similar to {existing_file} (distance: {distance})")
                        return True
                except Exception as e:
                    self.logger.warning(f"Error comparing hashes: {e}")
                    continue
            
            # Add new hash to database
            self.hash_db[hash_str] = str(filepath)
            self._save_hash_db()
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking duplicate for {filepath}: {e}")
            return False
    
    def _calculate_hash(self, filepath: Path) -> Union[imagehash.ImageHash, None]:
        """Calculate perceptual hash for image."""
        try:
            with Image.open(filepath) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Calculate average hash (good balance of speed and accuracy)
                return imagehash.average_hash(img, hash_size=self.hash_size)
                
        except Exception as e:
            self.logger.error(f"Error calculating hash for {filepath}: {e}")
            return None
    
    def get_duplicate_groups(self) -> Dict[str, list]:
        """Find groups of similar images in the database."""
        groups = {}
        processed = set()
        
        for hash1, file1 in self.hash_db.items():
            if hash1 in processed:
                continue
                
            group = [file1]
            processed.add(hash1)
            
            try:
                hash1_obj = imagehash.hex_to_hash(hash1)
                
                for hash2, file2 in self.hash_db.items():
                    if hash2 in processed:
                        continue
                    
                    try:
                        hash2_obj = imagehash.hex_to_hash(hash2)
                        distance = hash1_obj - hash2_obj
                        
                        if distance <= self.threshold:
                            group.append(file2)
                            processed.add(hash2)
                    except Exception:
                        continue
                        
            except Exception:
                continue
            
            if len(group) > 1:
                groups[hash1] = group
        
        return groups
    
    def remove_duplicates_from_directory(self, directory: Union[str, Path]) -> int:
        """Remove duplicate images from a directory."""
        directory = Path(directory)
        removed_count = 0
        
        # Get all image files
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
            image_files.extend(directory.glob(ext))
            image_files.extend(directory.glob(ext.upper()))
        
        # Calculate hashes for all images
        file_hashes = {}
        for filepath in image_files:
            image_hash = self._calculate_hash(filepath)
            if image_hash:
                file_hashes[str(image_hash)] = filepath
        
        # Find and remove duplicates
        processed = set()
        for hash_str, filepath in file_hashes.items():
            if hash_str in processed:
                continue
            
            # Find similar images
            similar_files = [filepath]
            processed.add(hash_str)
            
            try:
                hash_obj = imagehash.hex_to_hash(hash_str)
                
                for other_hash, other_file in file_hashes.items():
                    if other_hash in processed:
                        continue
                    
                    try:
                        other_hash_obj = imagehash.hex_to_hash(other_hash)
                        distance = hash_obj - other_hash_obj
                        
                        if distance <= self.threshold:
                            similar_files.append(other_file)
                            processed.add(other_hash)
                    except Exception:
                        continue
                        
            except Exception:
                continue
            
            # Keep the first file, remove others
            if len(similar_files) > 1:
                for duplicate_file in similar_files[1:]:
                    try:
                        duplicate_file.unlink()
                        removed_count += 1
                        self.logger.info(f"Removed duplicate: {duplicate_file.name}")
                    except Exception as e:
                        self.logger.error(f"Could not remove {duplicate_file}: {e}")
        
        return removed_count 
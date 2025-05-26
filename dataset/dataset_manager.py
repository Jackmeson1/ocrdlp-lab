"""
Dataset manager for OCR+DLP data organization and management.
"""

import json
import shutil
from typing import Dict, List, Optional, Union
from pathlib import Path
import logging
from datetime import datetime


class DatasetManager:
    """Manage OCR+DLP dataset structure and metadata."""
    
    def __init__(self, base_dir: str = "ocr_dataset"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Standard dataset structure
        self.dirs = {
            'full': self.base_dir / 'full',           # All downloaded images
            'filtered': self.base_dir / 'filtered',   # Filtered/processed images
            'tagged': self.base_dir / 'tagged',       # Tagged images with metadata
            'train': self.base_dir / 'train',         # Training split
            'val': self.base_dir / 'val',             # Validation split
            'test': self.base_dir / 'test',           # Test split
        }
        
        # Create directories
        for dir_path in self.dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        
        self.metadata_file = self.base_dir / 'dataset_metadata.json'
        self.logger = logging.getLogger(__name__)
    
    def get_dataset_info(self) -> Dict:
        """Get comprehensive dataset information."""
        info = {
            'base_directory': str(self.base_dir),
            'created_at': datetime.now().isoformat(),
            'structure': {},
            'statistics': {},
            'total_images': 0
        }
        
        # Count images in each directory
        for name, dir_path in self.dirs.items():
            if dir_path.exists():
                image_count = self._count_images(dir_path)
                info['structure'][name] = {
                    'path': str(dir_path),
                    'image_count': image_count,
                    'exists': True
                }
                info['total_images'] += image_count
            else:
                info['structure'][name] = {
                    'path': str(dir_path),
                    'image_count': 0,
                    'exists': False
                }
        
        # Load existing metadata if available
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    existing_metadata = json.load(f)
                    info['statistics'] = existing_metadata.get('statistics', {})
            except Exception as e:
                self.logger.warning(f"Could not load existing metadata: {e}")
        
        return info
    
    def _count_images(self, directory: Path) -> int:
        """Count image files in directory."""
        count = 0
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
            count += len(list(directory.glob(ext)))
            count += len(list(directory.glob(ext.upper())))
        return count
    
    def save_metadata(self, metadata: Dict):
        """Save dataset metadata to file."""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Metadata saved to {self.metadata_file}")
        except Exception as e:
            self.logger.error(f"Failed to save metadata: {e}")
    
    def load_metadata(self) -> Optional[Dict]:
        """Load dataset metadata from file."""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load metadata: {e}")
        return None
    
    def move_images_to_filtered(self, source_dir: Optional[Union[str, Path]] = None) -> int:
        """Move valid images from full to filtered directory."""
        source_dir = Path(source_dir) if source_dir else self.dirs['full']
        target_dir = self.dirs['filtered']
        
        if not source_dir.exists():
            self.logger.warning(f"Source directory does not exist: {source_dir}")
            return 0
        
        moved_count = 0
        
        # Get all image files
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
            image_files.extend(source_dir.glob(ext))
            image_files.extend(source_dir.glob(ext.upper()))
        
        for image_file in image_files:
            try:
                target_file = target_dir / image_file.name
                
                # Avoid overwriting existing files
                if target_file.exists():
                    base_name = image_file.stem
                    extension = image_file.suffix
                    counter = 1
                    while target_file.exists():
                        target_file = target_dir / f"{base_name}_{counter}{extension}"
                        counter += 1
                
                shutil.move(str(image_file), str(target_file))
                moved_count += 1
                
            except Exception as e:
                self.logger.error(f"Failed to move {image_file}: {e}")
        
        self.logger.info(f"Moved {moved_count} images to filtered directory")
        return moved_count
    
    def create_train_val_test_split(self, 
                                  source_dir: Optional[Union[str, Path]] = None,
                                  train_ratio: float = 0.7,
                                  val_ratio: float = 0.15,
                                  test_ratio: float = 0.15,
                                  copy_files: bool = True) -> Dict[str, int]:
        """Split dataset into train/validation/test sets."""
        if abs(train_ratio + val_ratio + test_ratio - 1.0) > 0.001:
            raise ValueError("Split ratios must sum to 1.0")
        
        source_dir = Path(source_dir) if source_dir else self.dirs['filtered']
        
        if not source_dir.exists():
            self.logger.warning(f"Source directory does not exist: {source_dir}")
            return {'train': 0, 'val': 0, 'test': 0}
        
        # Get all image files
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
            image_files.extend(source_dir.glob(ext))
            image_files.extend(source_dir.glob(ext.upper()))
        
        if not image_files:
            self.logger.warning(f"No image files found in {source_dir}")
            return {'train': 0, 'val': 0, 'test': 0}
        
        # Shuffle and split
        import random
        random.shuffle(image_files)
        
        total_count = len(image_files)
        train_count = int(total_count * train_ratio)
        val_count = int(total_count * val_ratio)
        
        train_files = image_files[:train_count]
        val_files = image_files[train_count:train_count + val_count]
        test_files = image_files[train_count + val_count:]
        
        # Move/copy files to respective directories
        splits = {
            'train': (train_files, self.dirs['train']),
            'val': (val_files, self.dirs['val']),
            'test': (test_files, self.dirs['test'])
        }
        
        results = {}
        
        for split_name, (files, target_dir) in splits.items():
            moved_count = 0
            
            for image_file in files:
                try:
                    target_file = target_dir / image_file.name
                    
                    # Handle name conflicts
                    if target_file.exists():
                        base_name = image_file.stem
                        extension = image_file.suffix
                        counter = 1
                        while target_file.exists():
                            target_file = target_dir / f"{base_name}_{counter}{extension}"
                            counter += 1
                    
                    if copy_files:
                        shutil.copy2(str(image_file), str(target_file))
                    else:
                        shutil.move(str(image_file), str(target_file))
                    
                    moved_count += 1
                    
                except Exception as e:
                    self.logger.error(f"Failed to move {image_file} to {split_name}: {e}")
            
            results[split_name] = moved_count
            self.logger.info(f"Created {split_name} split with {moved_count} images")
        
        return results
    
    def cleanup_empty_directories(self):
        """Remove empty directories in the dataset."""
        for name, dir_path in self.dirs.items():
            if dir_path.exists() and not any(dir_path.iterdir()):
                try:
                    dir_path.rmdir()
                    self.logger.info(f"Removed empty directory: {name}")
                except Exception as e:
                    self.logger.warning(f"Could not remove directory {name}: {e}")
    
    def validate_dataset_structure(self) -> Dict[str, bool]:
        """Validate the dataset directory structure."""
        validation_results = {}
        
        for name, dir_path in self.dirs.items():
            validation_results[name] = dir_path.exists()
        
        # Check for required files
        validation_results['metadata_file'] = self.metadata_file.exists()
        
        return validation_results
    
    def get_dataset_summary(self) -> str:
        """Generate a human-readable dataset summary."""
        info = self.get_dataset_info()
        
        summary = f"""
OCR+DLP Dataset Summary
======================
Base Directory: {info['base_directory']}
Total Images: {info['total_images']}
Created: {info['created_at']}

Directory Structure:
"""
        
        for name, details in info['structure'].items():
            status = "✓" if details['exists'] else "✗"
            summary += f"  {status} {name}: {details['image_count']} images\n"
        
        if info['statistics']:
            summary += f"\nStatistics:\n"
            for key, value in info['statistics'].items():
                summary += f"  {key}: {value}\n"
        
        return summary 
"""
Data organizer for structuring dataset based on tags and metadata.
"""

import json
import shutil
from typing import Dict, List, Optional, Union
from pathlib import Path
import logging
from collections import defaultdict


class DataOrganizer:
    """Organize dataset based on tags and metadata."""
    
    def __init__(self, base_dir: str = "ocr_dataset"):
        self.base_dir = Path(base_dir)
        self.logger = logging.getLogger(__name__)
    
    def organize_by_document_type(self, 
                                tags_file: Union[str, Path],
                                source_dir: Union[str, Path],
                                target_base_dir: Optional[Union[str, Path]] = None) -> Dict[str, int]:
        """Organize images by document type based on tags."""
        tags_file = Path(tags_file)
        source_dir = Path(source_dir)
        target_base_dir = Path(target_base_dir) if target_base_dir else self.base_dir / "organized_by_type"
        
        if not tags_file.exists():
            self.logger.error(f"Tags file not found: {tags_file}")
            return {}
        
        if not source_dir.exists():
            self.logger.error(f"Source directory not found: {source_dir}")
            return {}
        
        # Load tags
        tags_data = self._load_tags_from_jsonl(tags_file)
        if not tags_data:
            return {}
        
        # Create mapping from filename to document type
        filename_to_type = {}
        for record in tags_data:
            filename = record.get('filename')
            doc_type = record.get('tags', {}).get('document_type', 'unknown')
            if filename:
                filename_to_type[filename] = doc_type
        
        # Organize files
        results = defaultdict(int)
        
        for image_file in source_dir.glob('*'):
            if image_file.is_file() and image_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
                doc_type = filename_to_type.get(image_file.name, 'unknown')
                
                # Create target directory
                target_dir = target_base_dir / doc_type
                target_dir.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                target_file = target_dir / image_file.name
                try:
                    shutil.copy2(str(image_file), str(target_file))
                    results[doc_type] += 1
                except Exception as e:
                    self.logger.error(f"Failed to copy {image_file}: {e}")
        
        self.logger.info(f"Organized {sum(results.values())} images by document type")
        return dict(results)
    
    def organize_by_privacy_level(self,
                                tags_file: Union[str, Path],
                                source_dir: Union[str, Path],
                                target_base_dir: Optional[Union[str, Path]] = None) -> Dict[str, int]:
        """Organize images by privacy level."""
        tags_file = Path(tags_file)
        source_dir = Path(source_dir)
        target_base_dir = Path(target_base_dir) if target_base_dir else self.base_dir / "organized_by_privacy"
        
        if not tags_file.exists():
            self.logger.error(f"Tags file not found: {tags_file}")
            return {}
        
        # Load tags
        tags_data = self._load_tags_from_jsonl(tags_file)
        if not tags_data:
            return {}
        
        # Create mapping from filename to privacy level
        filename_to_privacy = {}
        for record in tags_data:
            filename = record.get('filename')
            privacy_level = record.get('tags', {}).get('privacy_level', 'unknown')
            if filename:
                filename_to_privacy[filename] = privacy_level
        
        # Organize files
        results = defaultdict(int)
        
        for image_file in source_dir.glob('*'):
            if image_file.is_file() and image_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
                privacy_level = filename_to_privacy.get(image_file.name, 'unknown')
                
                # Create target directory
                target_dir = target_base_dir / privacy_level
                target_dir.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                target_file = target_dir / image_file.name
                try:
                    shutil.copy2(str(image_file), str(target_file))
                    results[privacy_level] += 1
                except Exception as e:
                    self.logger.error(f"Failed to copy {image_file}: {e}")
        
        self.logger.info(f"Organized {sum(results.values())} images by privacy level")
        return dict(results)
    
    def create_quality_filtered_dataset(self,
                                      tags_file: Union[str, Path],
                                      source_dir: Union[str, Path],
                                      target_dir: Union[str, Path],
                                      min_quality: float = 0.7) -> int:
        """Create dataset with only high-quality images."""
        tags_file = Path(tags_file)
        source_dir = Path(source_dir)
        target_dir = Path(target_dir)
        
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Load tags
        tags_data = self._load_tags_from_jsonl(tags_file)
        if not tags_data:
            return 0
        
        # Filter by quality
        high_quality_files = []
        for record in tags_data:
            filename = record.get('filename')
            quality_score = record.get('tags', {}).get('quality_score', 0.0)
            
            if filename and quality_score >= min_quality:
                high_quality_files.append(filename)
        
        # Copy high-quality files
        copied_count = 0
        for filename in high_quality_files:
            source_file = source_dir / filename
            if source_file.exists():
                target_file = target_dir / filename
                try:
                    shutil.copy2(str(source_file), str(target_file))
                    copied_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to copy {source_file}: {e}")
        
        self.logger.info(f"Created quality-filtered dataset with {copied_count} images (min quality: {min_quality})")
        return copied_count
    
    def create_language_specific_dataset(self,
                                       tags_file: Union[str, Path],
                                       source_dir: Union[str, Path],
                                       target_base_dir: Union[str, Path],
                                       languages: List[str]) -> Dict[str, int]:
        """Create language-specific datasets."""
        tags_file = Path(tags_file)
        source_dir = Path(source_dir)
        target_base_dir = Path(target_base_dir)
        
        # Load tags
        tags_data = self._load_tags_from_jsonl(tags_file)
        if not tags_data:
            return {}
        
        results = {}
        
        for language in languages:
            # Filter files by language
            language_files = []
            for record in tags_data:
                filename = record.get('filename')
                detected_language = record.get('tags', {}).get('language', '')
                
                if filename and detected_language == language:
                    language_files.append(filename)
            
            if language_files:
                # Create language-specific directory
                lang_dir = target_base_dir / language
                lang_dir.mkdir(parents=True, exist_ok=True)
                
                # Copy files
                copied_count = 0
                for filename in language_files:
                    source_file = source_dir / filename
                    if source_file.exists():
                        target_file = lang_dir / filename
                        try:
                            shutil.copy2(str(source_file), str(target_file))
                            copied_count += 1
                        except Exception as e:
                            self.logger.error(f"Failed to copy {source_file}: {e}")
                
                results[language] = copied_count
                self.logger.info(f"Created {language} dataset with {copied_count} images")
        
        return results
    
    def create_content_field_index(self, tags_file: Union[str, Path]) -> Dict[str, List[str]]:
        """Create index of images by content fields."""
        tags_file = Path(tags_file)
        
        # Load tags
        tags_data = self._load_tags_from_jsonl(tags_file)
        if not tags_data:
            return {}
        
        field_index = defaultdict(list)
        
        for record in tags_data:
            filename = record.get('filename')
            content_fields = record.get('tags', {}).get('content_fields', [])
            
            if filename:
                for field in content_fields:
                    field_index[field].append(filename)
        
        # Convert to regular dict and sort
        result = {}
        for field, files in field_index.items():
            result[field] = sorted(list(set(files)))  # Remove duplicates and sort
        
        return result
    
    def generate_dataset_report(self, tags_file: Union[str, Path]) -> Dict:
        """Generate comprehensive dataset report."""
        tags_file = Path(tags_file)
        
        # Load tags
        tags_data = self._load_tags_from_jsonl(tags_file)
        if not tags_data:
            return {}
        
        report = {
            'total_images': len(tags_data),
            'document_types': defaultdict(int),
            'languages': defaultdict(int),
            'privacy_levels': defaultdict(int),
            'content_fields': defaultdict(int),
            'quality_distribution': {
                'high': 0,      # >= 0.8
                'medium': 0,    # 0.5 - 0.8
                'low': 0        # < 0.5
            },
            'features': {
                'has_handwriting': 0,
                'has_stamps_seals': 0,
                'has_tables': 0,
                'has_logos': 0
            },
            'layout_complexity': defaultdict(int),
            'text_density': defaultdict(int)
        }
        
        quality_scores = []
        
        for record in tags_data:
            tags = record.get('tags', {})
            
            # Document types
            doc_type = tags.get('document_type', 'unknown')
            report['document_types'][doc_type] += 1
            
            # Languages
            language = tags.get('language', 'unknown')
            report['languages'][language] += 1
            
            # Privacy levels
            privacy = tags.get('privacy_level', 'unknown')
            report['privacy_levels'][privacy] += 1
            
            # Content fields
            for field in tags.get('content_fields', []):
                report['content_fields'][field] += 1
            
            # Quality distribution
            quality = tags.get('quality_score', 0.0)
            quality_scores.append(quality)
            if quality >= 0.8:
                report['quality_distribution']['high'] += 1
            elif quality >= 0.5:
                report['quality_distribution']['medium'] += 1
            else:
                report['quality_distribution']['low'] += 1
            
            # Features
            for feature in report['features']:
                if tags.get(feature, False):
                    report['features'][feature] += 1
            
            # Layout complexity
            complexity = tags.get('layout_complexity', 'unknown')
            report['layout_complexity'][complexity] += 1
            
            # Text density
            density = tags.get('text_density', 'unknown')
            report['text_density'][density] += 1
        
        # Add quality statistics
        if quality_scores:
            report['quality_stats'] = {
                'mean': sum(quality_scores) / len(quality_scores),
                'min': min(quality_scores),
                'max': max(quality_scores)
            }
        
        # Convert defaultdicts to regular dicts
        for key in ['document_types', 'languages', 'privacy_levels', 'content_fields', 'layout_complexity', 'text_density']:
            report[key] = dict(report[key])
        
        return report
    
    def _load_tags_from_jsonl(self, jsonl_file: Path) -> List[Dict]:
        """Load tags from JSONL file."""
        tags = []
        try:
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        tags.append(json.loads(line))
            return tags
        except Exception as e:
            self.logger.error(f"Error loading tags from {jsonl_file}: {e}")
            return [] 
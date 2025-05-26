#!/usr/bin/env python3
"""
Image Labeling Test Script
Tests the complete workflow for OCR_DLP dataset classification.
"""

import os
import json
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any
from PIL import Image
import time

# Import modules
from crawler.search import search_images, download_images
from gpt4v_image_labeler import GPT4VImageLabeler, classify_images_batch, validate_classification_labels


class ImageLabelingTester:
    """Test image labeling workflow for OCR_DLP dataset preparation"""
    
    def __init__(self):
        self.temp_dir = None
        self.test_results = {}
        self.start_time = None
        
    async def setup(self):
        """Test environment setup"""
        self.start_time = time.time()
        
        # Create temporary directory
        self.temp_dir = Path(tempfile.mkdtemp(prefix="image_labeling_test_"))
        print(f"🔧 Created temp directory: {self.temp_dir}")
        
        # Check API keys
        self.serper_key = os.getenv('SERPER_API_KEY')
        self.openai_key = os.getenv('OPENAI_API_KEY')
        
        if not self.serper_key:
            raise ValueError("❌ SERPER_API_KEY not found in environment")
        if not self.openai_key:
            raise ValueError("❌ OPENAI_API_KEY not found in environment")
            
        print("✅ API keys validated")
        
    async def cleanup(self):
        """Clean up test environment"""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            print(f"🧹 Cleaned up temp directory: {self.temp_dir}")
    
    async def test_download_sample_images(self) -> List[str]:
        """Download sample images for OCR_DLP testing"""
        print(f"\n🔍 Step 1: Downloading sample images for OCR_DLP testing")
        
        # Define search queries for different document types
        search_queries = [
            "indian invoice blurry photo",
            "aadhaar card photo",
            "passport document image",
            "bank statement document",
            "receipt photo blurry"
        ]
        
        downloaded_images = []
        
        for i, query in enumerate(search_queries, 1):
            print(f"\n📥 Downloading image {i}/{len(search_queries)}: '{query}'")
            
            try:
                # Search for images
                urls = await search_images(query, engine='serper', limit=2)
                
                if not urls:
                    print(f"  ⚠️ No images found for: {query}")
                    continue
                
                # Download first image
                results = await download_images([urls[0]], output_dir=str(self.temp_dir))
                
                if results:
                    image_path = list(results.values())[0]
                    
                    # Validate image
                    try:
                        with Image.open(image_path) as img:
                            width, height = img.size
                            file_size = os.path.getsize(image_path)
                            
                        if width >= 100 and height >= 100 and file_size >= 5000:
                            downloaded_images.append(image_path)
                            print(f"  ✅ Downloaded: {Path(image_path).name} ({width}x{height}, {file_size:,} bytes)")
                        else:
                            print(f"  ⚠️ Image too small or corrupted: {width}x{height}, {file_size} bytes")
                            
                    except Exception as e:
                        print(f"  ❌ Invalid image: {e}")
                else:
                    print(f"  ❌ Download failed for: {query}")
                    
            except Exception as e:
                print(f"  ❌ Error processing '{query}': {e}")
        
        print(f"\n✅ Downloaded {len(downloaded_images)} valid images")
        
        self.test_results['image_download'] = {
            'status': 'success',
            'downloaded_count': len(downloaded_images),
            'image_paths': downloaded_images
        }
        
        return downloaded_images
    
    async def test_image_classification(self, image_paths: List[str]) -> List[Dict[str, Any]]:
        """Test image classification for OCR_DLP dataset"""
        print(f"\n🤖 Step 2: Classifying images for OCR_DLP dataset")
        
        if not image_paths:
            raise RuntimeError("❌ No images to classify")
        
        # Initialize labeler
        labeler = GPT4VImageLabeler(self.openai_key)
        
        classification_results = []
        
        for i, image_path in enumerate(image_paths, 1):
            print(f"\n📸 Classifying image {i}/{len(image_paths)}: {Path(image_path).name}")
            
            try:
                # Classify image
                result = await labeler.classify_image(image_path)
                
                if 'error' in result:
                    print(f"  ❌ Classification failed: {result['error']}")
                    classification_results.append(result)
                    continue
                
                # Display classification results
                print(f"  ✅ Classification successful:")
                print(f"    📋 Category: {result.get('document_category', 'N/A')}")
                print(f"    📄 Subcategory: {result.get('document_subcategory', 'N/A')}")
                print(f"    🌐 Language: {result.get('language_primary', 'N/A')}")
                print(f"    📊 Text Clarity: {result.get('text_clarity', 'N/A')}")
                print(f"    🎯 Image Quality: {result.get('image_quality', 'N/A')}")
                print(f"    🔍 OCR Difficulty: {result.get('ocr_difficulty', 'N/A')}")
                print(f"    📈 Confidence: {result.get('confidence_score', 'N/A')}")
                
                # Show testing scenarios
                scenarios = result.get('testing_scenarios', [])
                if scenarios:
                    print(f"    🧪 Testing Scenarios: {', '.join(scenarios[:3])}")
                
                # Show challenge factors
                challenges = result.get('challenge_factors', [])
                if challenges:
                    print(f"    ⚠️ Challenge Factors: {', '.join(challenges[:3])}")
                
                classification_results.append(result)
                
            except Exception as e:
                error_result = {
                    'error': f'Classification failed: {str(e)}',
                    '_metadata': {'image_path': image_path}
                }
                print(f"  ❌ Classification error: {e}")
                classification_results.append(error_result)
        
        # Calculate success rate
        successful = sum(1 for r in classification_results if 'error' not in r)
        success_rate = successful / len(classification_results) * 100
        
        print(f"\n📊 Classification Summary:")
        print(f"  ✅ Successful: {successful}/{len(classification_results)} ({success_rate:.1f}%)")
        
        self.test_results['image_classification'] = {
            'status': 'success',
            'total_images': len(classification_results),
            'successful_classifications': successful,
            'success_rate': success_rate,
            'results': classification_results
        }
        
        return classification_results
    
    async def test_batch_classification(self) -> str:
        """Test batch classification functionality"""
        print(f"\n📦 Step 3: Testing batch classification")
        
        if not self.temp_dir:
            raise RuntimeError("❌ Temp directory not initialized")
        
        # Create images subdirectory
        images_dir = self.temp_dir / "images"
        images_dir.mkdir(exist_ok=True)
        
        # Copy downloaded images to images directory
        image_paths = self.test_results.get('image_download', {}).get('image_paths', [])
        
        if not image_paths:
            print("  ⚠️ No images available for batch testing")
            return ""
        
        # Copy images to batch directory
        for image_path in image_paths:
            src = Path(image_path)
            dst = images_dir / src.name
            shutil.copy2(src, dst)
        
        print(f"  📁 Copied {len(image_paths)} images to batch directory")
        
        # Run batch classification
        output_file = str(self.temp_dir / "batch_labels.jsonl")
        
        try:
            results = await classify_images_batch(str(images_dir), output_file)
            
            if results:
                print(f"  ✅ Batch classification completed")
                print(f"  📁 Results saved to: {output_file}")
                
                # Validate results
                validation_results = validate_classification_labels(output_file)
                
                if validation_results:
                    print(f"  📊 Validation: {validation_results['valid_classifications']}/{validation_results['total_records']} valid")
                
                self.test_results['batch_classification'] = {
                    'status': 'success',
                    'output_file': output_file,
                    'validation_results': validation_results
                }
                
                return output_file
            else:
                raise RuntimeError("Batch classification returned no results")
                
        except Exception as e:
            self.test_results['batch_classification'] = {
                'status': 'failed',
                'error': str(e)
            }
            raise
    
    async def test_complete_labeling_workflow(self) -> Dict[str, Any]:
        """Test complete image labeling workflow"""
        print(f"\n🚀 Starting Complete Image Labeling Workflow Test")
        print("=" * 60)
        print("🎯 Purpose: OCR_DLP dataset preparation and classification")
        print("=" * 60)
        
        try:
            # Step 1: Download sample images
            image_paths = await self.test_download_sample_images()
            
            if not image_paths:
                raise RuntimeError("❌ No images downloaded for testing")
            
            # Step 2: Classify individual images
            classification_results = await self.test_image_classification(image_paths)
            
            # Step 3: Test batch classification
            batch_output_file = await self.test_batch_classification()
            
            # Calculate execution time
            execution_time = time.time() - self.start_time
            
            print(f"\n✅ COMPLETE WORKFLOW SUCCESS!")
            print(f"⏱️ Total execution time: {execution_time:.2f} seconds")
            
            # Generate final summary
            self.generate_workflow_summary()
            
            self.test_results['complete_workflow'] = {
                'status': 'success',
                'execution_time': execution_time,
                'batch_output_file': batch_output_file
            }
            
            return {
                'image_paths': image_paths,
                'classification_results': classification_results,
                'batch_output_file': batch_output_file,
                'execution_time': execution_time
            }
            
        except Exception as e:
            self.test_results['complete_workflow'] = {
                'status': 'failed',
                'error': str(e)
            }
            raise
    
    def generate_workflow_summary(self):
        """Generate workflow summary report"""
        print(f"\n📊 WORKFLOW SUMMARY REPORT")
        print("=" * 50)
        
        # Download summary
        download_result = self.test_results.get('image_download', {})
        if download_result.get('status') == 'success':
            print(f"✅ Image Download: {download_result['downloaded_count']} images")
        else:
            print(f"❌ Image Download: Failed")
        
        # Classification summary
        classification_result = self.test_results.get('image_classification', {})
        if classification_result.get('status') == 'success':
            success_rate = classification_result['success_rate']
            print(f"✅ Image Classification: {classification_result['successful_classifications']}/{classification_result['total_images']} ({success_rate:.1f}%)")
        else:
            print(f"❌ Image Classification: Failed")
        
        # Batch processing summary
        batch_result = self.test_results.get('batch_classification', {})
        if batch_result.get('status') == 'success':
            validation = batch_result.get('validation_results', {})
            valid_count = validation.get('valid_classifications', 0)
            total_count = validation.get('total_records', 0)
            print(f"✅ Batch Processing: {valid_count}/{total_count} valid classifications")
        else:
            print(f"❌ Batch Processing: Failed")
        
        # Overall status
        all_success = all(
            result.get('status') == 'success' 
            for result in self.test_results.values() 
            if 'status' in result
        )
        
        if all_success:
            print(f"\n🎉 ALL TESTS PASSED - OCR_DLP LABELING SYSTEM READY!")
        else:
            print(f"\n⚠️ Some tests failed - check individual results")
        
        # Save summary to file
        if self.temp_dir:
            summary_file = self.temp_dir / "labeling_workflow_summary.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            print(f"\n📄 Detailed results saved to: {summary_file}")


async def run_image_labeling_test():
    """Run complete image labeling test"""
    
    print("🚀 Image Labeling Test for OCR_DLP Dataset")
    print("=" * 60)
    print("🎯 Testing image classification for OCR_DLP system performance evaluation")
    print("=" * 60)
    
    tester = ImageLabelingTester()
    
    try:
        # Setup
        await tester.setup()
        
        # Run complete workflow
        result = await tester.test_complete_labeling_workflow()
        
        print("\n" + "=" * 60)
        print("🎉 IMAGE LABELING TEST COMPLETED SUCCESSFULLY!")
        print("✅ OCR_DLP dataset classification system is functional")
        print("=" * 60)
        
        return result
        
    except Exception as e:
        print(f"\n❌ IMAGE LABELING TEST FAILED: {e}")
        
        # Show error analysis
        if "429" in str(e) or "quota" in str(e).lower():
            print("  💡 This appears to be an API rate limit issue")
            print("  💡 Wait a few minutes and try again")
        elif "401" in str(e) or "unauthorized" in str(e).lower():
            print("  💡 This appears to be an API authentication issue")
            print("  💡 Check your OpenAI API key")
        else:
            print(f"  💡 Unexpected error: {e}")
        
        raise
        
    finally:
        # Cleanup
        await tester.cleanup()


if __name__ == "__main__":
    # Check environment variables
    if not os.getenv('SERPER_API_KEY'):
        print("❌ Please set SERPER_API_KEY environment variable")
        exit(1)
    
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Please set OPENAI_API_KEY environment variable")
        exit(1)
    
    # Run test
    try:
        result = asyncio.run(run_image_labeling_test())
        print("\n✅ Image labeling test completed successfully!")
        exit(0)
    except Exception as e:
        print(f"\n❌ Image labeling test failed: {e}")
        exit(1) 
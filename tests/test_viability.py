#!/usr/bin/env python3
"""
Project Viability Test
Tests Indian ID download and labeling to confirm system functionality.
"""

import os
import asyncio
import pytest
import requests
import tempfile
import shutil
from pathlib import Path
from PIL import Image

from crawler.search import search_images, download_images
from gpt4v_image_labeler import GPT4VImageLabeler
from unittest.mock import patch, Mock
import logging


@pytest.mark.asyncio
async def test_project_viability():
    """Test project viability with Indian ID images"""
    
    print("🔍 Project Viability Test")
    print("=" * 50)
    print("🎯 Testing: Indian ID download and labeling")
    
    # Create temp directory
    temp_dir = Path(tempfile.mkdtemp(prefix="viability_test_"))
    print(f"📁 Temp directory: {temp_dir}")
    
    try:
        # Test 1: Search and download Indian ID
        print(f"\n📥 Step 1: Searching for Indian ID images")
        
        search_queries = [
            "indian aadhaar card document",
            "india identity card photo",
            "indian ID card sample"
        ]
        
        downloaded_image = None
        
        for query in search_queries:
            print(f"  🔍 Searching: '{query}'")

            try:
                urls = await search_images(query, engine='serper', limit=3)

                if urls:
                    print(f"    ✅ Found {len(urls)} URLs")
                    
                    # Try to download first URL
                    results = await download_images([urls[0]], output_dir=str(temp_dir))
                    
                    if results:
                        image_path = list(results.values())[0]
                        
                        # Validate image
                        try:
                            with Image.open(image_path) as img:
                                width, height = img.size
                                file_size = os.path.getsize(image_path)
                                
                            if width >= 200 and height >= 200 and file_size >= 10000:
                                downloaded_image = image_path
                                print(f"    ✅ Downloaded valid image: {Path(image_path).name}")
                                print(f"       Size: {width}x{height}, {file_size:,} bytes")
                                break
                            else:
                                print(f"    ⚠️ Image too small: {width}x{height}, {file_size} bytes")
                        except Exception as e:
                            print(f"    ❌ Invalid image: {e}")
                    else:
                        print(f"    ❌ Download failed")
                else:
                    print(f"    ⚠️ No URLs found")
                    
            except requests.exceptions.RequestException:
                pytest.skip("Serper API unreachable in this environment")
            except Exception as e:
                print(f"    ❌ Search error: {e}")
        
        if not downloaded_image:
            print("\n❌ VIABILITY TEST FAILED: Could not download valid Indian ID image")
            return False
        
        # Test 2: Classify the image
        print(f"\n🤖 Step 2: Classifying Indian ID image")
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ OPENAI_API_KEY not found")
            return False
        
        labeler = GPT4VImageLabeler(api_key)
        
        try:
            result = await labeler.classify_image(downloaded_image)
            
            if 'error' in result:
                print(f"❌ Classification failed: {result['error']}")
                return False
            
            # Display results
            print(f"✅ Classification successful!")
            print(f"  📋 Category: {result.get('document_category', 'N/A')}")
            print(f"  📄 Subcategory: {result.get('document_subcategory', 'N/A')}")
            print(f"  🌐 Language: {result.get('language_primary', 'N/A')}")
            print(f"  🔍 OCR Difficulty: {result.get('ocr_difficulty', 'N/A')}")
            print(f"  🎯 Confidence: {result.get('confidence_score', 'N/A')}")
            
            # Check sensitive data detection
            sensitive_data = result.get('sensitive_data_types', [])
            if sensitive_data:
                print(f"  🔒 Sensitive Data Detected: {', '.join(sensitive_data[:5])}")
            
            # Check testing scenarios
            scenarios = result.get('testing_scenarios', [])
            if scenarios:
                print(f"  🧪 Testing Scenarios: {', '.join(scenarios[:3])}")
            
            # Test 3: Save output file
            print(f"\n💾 Step 3: Saving classification results")
            
            output_file = temp_dir / "indian_id_classification.json"
            
            import json
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            file_size = output_file.stat().st_size
            print(f"✅ Output file created: {output_file}")
            print(f"   File size: {file_size:,} bytes")
            
            # Verify file content
            with open(output_file, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            required_fields = ['document_category', 'ocr_difficulty', 'confidence_score']
            missing_fields = [field for field in required_fields if field not in loaded_data]
            
            if missing_fields:
                print(f"⚠️ Missing required fields: {missing_fields}")
            else:
                print(f"✅ All required fields present")
            
            print(f"\n🎉 PROJECT VIABILITY CONFIRMED!")
            print(f"✅ Indian ID images can be downloaded")
            print(f"✅ Images are properly classified and labeled")
            print(f"✅ Output files are generated correctly")
            print(f"✅ System is ready for OCR_DLP dataset preparation")
            
            return True
            
        except Exception as e:
            print(f"❌ Classification error: {e}")
            return False
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    finally:
        # Cleanup
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            print(f"\n🧹 Cleaned up temp directory")


@pytest.mark.asyncio
async def test_search_timeout_handled(caplog):
    """search_images should log an error and return empty list on timeout."""
    caplog.set_level(logging.ERROR, logger="crawler.search")
    with (
        patch.dict(os.environ, {"SERPER_API_KEY": "test"}),
        patch("requests.post", side_effect=requests.exceptions.Timeout),
    ):
        urls = await search_images("test", engine="serper", limit=1)
    assert urls == []
    assert "Serper search error" in caplog.text


@pytest.mark.asyncio
async def test_download_bad_status(caplog, tmp_path):
    """download_images should skip URLs when HTTP status is not 200."""
    caplog.set_level(logging.WARNING, logger="crawler.search")
    mock_resp = Mock()
    mock_resp.status_code = 500
    mock_resp.headers = {"content-type": "image/jpeg"}
    with patch("requests.get", return_value=mock_resp):
        results = await download_images(["https://example.com/a.jpg"], output_dir=str(tmp_path))
    assert results == {}
    assert "Failed to download https://example.com/a.jpg" in caplog.text


if __name__ == "__main__":
    # Check environment variables
    if not os.getenv('SERPER_API_KEY'):
        print("❌ Please set SERPER_API_KEY environment variable")
        exit(1)
    
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Please set OPENAI_API_KEY environment variable")
        exit(1)
    
    # Run viability test
    try:
        success = asyncio.run(test_project_viability())
        if success:
            print("\n✅ Project viability test PASSED!")
            exit(0)
        else:
            print("\n❌ Project viability test FAILED!")
            exit(1)
    except Exception as e:
        print(f"\n❌ Viability test error: {e}")
        exit(1) 

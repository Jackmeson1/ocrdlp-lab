#!/usr/bin/env python3
"""
Demo: Image Labeling vs Content Extraction
Shows the difference between classification/labeling and content extraction.
"""

import os
import json
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

# Import both modules
from gpt4v_analyzer import GPT4VAnalyzer  # Content extraction
from gpt4v_image_labeler import GPT4VImageLabeler  # Image labeling
from crawler.search import search_images, download_images


async def demo_comparison():
    """Demonstrate the difference between labeling and extraction"""
    
    print("🔍 Demo: Image Labeling vs Content Extraction")
    print("=" * 60)
    print("🎯 Purpose: Show the difference between classification and extraction")
    print("=" * 60)
    
    # Check API keys
    serper_key = os.getenv('SERPER_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    if not serper_key or not openai_key:
        print("❌ API keys not found")
        return
    
    # Create temp directory
    temp_dir = Path(tempfile.mkdtemp(prefix="demo_comparison_"))
    print(f"🔧 Created temp directory: {temp_dir}")
    
    try:
        # Step 1: Download a sample image
        print(f"\n📥 Step 1: Downloading sample invoice image")
        
        urls = await search_images("indian invoice document", engine='serper', limit=3)
        if not urls:
            print("❌ No images found")
            return
        
        results = await download_images([urls[0]], output_dir=str(temp_dir))
        if not results:
            print("❌ Download failed")
            return
        
        image_path = list(results.values())[0]
        print(f"✅ Downloaded: {Path(image_path).name}")
        
        # Step 2: Content Extraction (Old Approach)
        print(f"\n🔍 Step 2: Content Extraction (Old Approach)")
        print("-" * 40)
        
        analyzer = GPT4VAnalyzer(openai_key)
        extraction_result = await analyzer.analyze_invoice(image_path)
        
        if 'error' not in extraction_result:
            print("✅ Content Extraction Results:")
            print(f"  📋 Document Type: {extraction_result.get('document_type', 'N/A')}")
            print(f"  💰 Total Amount: {extraction_result.get('total_amount', 'N/A')} {extraction_result.get('currency', 'N/A')}")
            print(f"  🏢 Vendor: {extraction_result.get('vendor_name', 'N/A')}")
            print(f"  📄 Invoice #: {extraction_result.get('invoice_number', 'N/A')}")
            print(f"  📅 Date: {extraction_result.get('invoice_date', 'N/A')}")
            print(f"  🌐 Language: {extraction_result.get('language', 'N/A')}")
            
            print(f"\n📊 Purpose: Extract specific data values from document")
            print(f"📊 Use Case: Data entry, accounting, compliance")
        else:
            print(f"❌ Content extraction failed: {extraction_result['error']}")
        
        # Step 3: Image Labeling (New Approach)
        print(f"\n🏷️ Step 3: Image Labeling (New Approach)")
        print("-" * 40)
        
        labeler = GPT4VImageLabeler(openai_key)
        labeling_result = await labeler.classify_image(image_path)
        
        if 'error' not in labeling_result:
            print("✅ Image Classification Results:")
            print(f"  📋 Category: {labeling_result.get('document_category', 'N/A')}")
            print(f"  📄 Subcategory: {labeling_result.get('document_subcategory', 'N/A')}")
            print(f"  🌐 Language: {labeling_result.get('language_primary', 'N/A')}")
            print(f"  📊 Text Clarity: {labeling_result.get('text_clarity', 'N/A')}")
            print(f"  🎯 Image Quality: {labeling_result.get('image_quality', 'N/A')}")
            print(f"  🔍 OCR Difficulty: {labeling_result.get('ocr_difficulty', 'N/A')}")
            print(f"  📈 Confidence: {labeling_result.get('confidence_score', 'N/A')}")
            
            # Show testing scenarios
            scenarios = labeling_result.get('testing_scenarios', [])
            if scenarios:
                print(f"  🧪 Testing Scenarios: {', '.join(scenarios[:3])}")
            
            # Show challenge factors
            challenges = labeling_result.get('challenge_factors', [])
            if challenges:
                print(f"  ⚠️ Challenge Factors: {', '.join(challenges[:3])}")
            
            # Show sensitive data types
            sensitive_types = labeling_result.get('sensitive_data_types', [])
            if sensitive_types:
                print(f"  🔒 Sensitive Data Types: {', '.join(sensitive_types[:3])}")
            
            print(f"\n📊 Purpose: Classify and categorize for testing")
            print(f"📊 Use Case: OCR_DLP performance evaluation, dataset organization")
        else:
            print(f"❌ Image labeling failed: {labeling_result['error']}")
        
        # Step 4: Comparison Summary
        print(f"\n📊 COMPARISON SUMMARY")
        print("=" * 60)
        
        print(f"\n🔍 CONTENT EXTRACTION (gpt4v_analyzer.py):")
        print(f"  🎯 Purpose: Extract specific data values")
        print(f"  📋 Output: Structured data (amounts, names, dates)")
        print(f"  🏢 Use Case: Business process automation")
        print(f"  📊 Focus: What information is IN the document")
        print(f"  💼 Example: Invoice processing, data entry")
        
        print(f"\n🏷️ IMAGE LABELING (gpt4v_image_labeler.py):")
        print(f"  🎯 Purpose: Classify and categorize images")
        print(f"  📋 Output: Classification labels and metadata")
        print(f"  🧪 Use Case: OCR_DLP system testing and evaluation")
        print(f"  📊 Focus: What TYPE of document and its characteristics")
        print(f"  🔬 Example: Dataset preparation, performance testing")
        
        print(f"\n🔄 KEY DIFFERENCES:")
        print(f"  📊 Extraction → 'What does it say?' (Content)")
        print(f"  🏷️ Labeling → 'What is it?' (Classification)")
        print(f"  📊 Extraction → Business data processing")
        print(f"  🏷️ Labeling → ML/AI system evaluation")
        
        # Save comparison results
        comparison_data = {
            'image_path': image_path,
            'content_extraction': extraction_result,
            'image_labeling': labeling_result,
            'comparison_summary': {
                'extraction_purpose': 'Extract specific data values from documents',
                'labeling_purpose': 'Classify documents for OCR_DLP testing',
                'extraction_use_case': 'Business process automation, data entry',
                'labeling_use_case': 'ML system evaluation, dataset preparation',
                'extraction_focus': 'Document content and data',
                'labeling_focus': 'Document type and characteristics'
            }
        }
        
        output_file = temp_dir / "comparison_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(comparison_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Comparison results saved to: {output_file}")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        
    finally:
        # Cleanup
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            print(f"\n🧹 Cleaned up temp directory")


if __name__ == "__main__":
    # Check environment variables
    if not os.getenv('SERPER_API_KEY'):
        print("❌ Please set SERPER_API_KEY environment variable")
        exit(1)
    
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Please set OPENAI_API_KEY environment variable")
        exit(1)
    
    # Run demo
    asyncio.run(demo_comparison()) 
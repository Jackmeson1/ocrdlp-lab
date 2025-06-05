#!/usr/bin/env python3
"""
GPT-4V Image Labeling Script
Classifies images into fine-grained categories for OCR_DLP system testing.
"""

import asyncio
import base64
import json
import os
from pathlib import Path
from typing import Any

import requests
import requests.exceptions
from PIL import Image

from http_client import post_with_retry


class GPT4VImageLabeler:
    """GPT-4V image labeler for document classification."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    def encode_image(self, image_path: str) -> str:
        """Encode image to base64."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def get_image_info(self, image_path: str) -> dict[str, Any]:
        """Get basic image information."""
        try:
            with Image.open(image_path) as img:
                return {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode,
                    "size_bytes": os.path.getsize(image_path),
                }
        except Exception as e:
            return {"error": str(e)}

    def _classify_image_sync(self, image_path: str) -> dict[str, Any]:
        """Synchronously classify an image using the GPT-4V API."""

        # Encode image
        base64_image = self.encode_image(image_path)

        # Build classification prompt
        prompt = """
        Please classify this image for OCR_DLP system performance testing. Return classification labels in JSON format:

        {
            "document_category": "Main document type (e.g., invoice, receipt, identity_card, passport, driver_license, bank_card, contract, certificate, etc.)",
            "document_subcategory": "Document subcategory (e.g., GST_invoice, commercial_invoice, restaurant_receipt, taxi_receipt, id_card_front, id_card_back, etc.)",
            "language_primary": "Primary language (e.g., English, Chinese, Hindi, Tamil, Arabic, Portuguese, Spanish, etc.)",
            "language_secondary": "Secondary language (if multilingual document)",
            "text_density": "Text density (dense/medium/sparse)",
            "text_clarity": "Text clarity (clear/blurry/partially_blurry)",
            "image_quality": "Image quality (high/medium/low)",
            "orientation": "Image orientation (upright/rotated_90/rotated_180/rotated_270/skewed)",
            "background_complexity": "Background complexity (simple/medium/complex)",
            "ocr_difficulty": "OCR difficulty level (easy/medium/hard/very_hard)",
            "sensitive_data_types": ["List of sensitive data types (e.g., name, id_number, bank_account, address, phone, etc.)"],
            "layout_type": "Layout type (table/list/paragraph/mixed/handwritten)",
            "special_features": ["Special features (e.g., watermark, stamp, signature, barcode, qr_code, logo, etc.)"],
            "testing_scenarios": ["Applicable testing scenarios (e.g., identity_verification, financial_audit, compliance_check, data_extraction, etc.)"],
            "challenge_factors": ["Challenge factors (e.g., small_font, background_noise, uneven_lighting, skewed, blurry, multilingual, etc.)"],
            "confidence_score": "Classification confidence (0-1)",
            "recommended_preprocessing": ["Recommended preprocessing steps (e.g., denoising, correction, contrast_enhancement, etc.)"]
        }

        Please ensure:
        1. Classifications are precise and specific for OCR_DLP system performance evaluation
        2. Identify all factors that may affect OCR performance
        3. Provide practical testing scenario suggestions
        4. If unable to determine a field, set it to null
        5. Return only JSON, no other explanatory text
        6. Use English for all field values
        """

        # Build request
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high",
                            },
                        },
                    ],
                }
            ],
            "max_tokens": 1500,
            "temperature": 0.1,
        }

        # Send request synchronously. The caller may choose to run this in a
        # thread pool to avoid blocking the event loop.
        try:
            response = post_with_retry(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=60,
            )

            if response.status_code == 200:
                result = response.json()

                # Extract GPT-4V response
                content = result['choices'][0]['message']['content']

                # Parse JSON
                try:
                    # Clean response text, extract JSON part
                    if '```json' in content:
                        json_start = content.find('```json') + 7
                        json_end = content.find('```', json_start)
                        content = content[json_start:json_end].strip()
                    elif '{' in content:
                        json_start = content.find('{')
                        json_end = content.rfind('}') + 1
                        content = content[json_start:json_end]

                    classification_data = json.loads(content)

                    # Add metadata
                    classification_data['_metadata'] = {
                        'image_path': image_path,
                        'image_info': self.get_image_info(image_path),
                        'classification_timestamp': asyncio.get_event_loop().time(),
                        'model_used': 'gpt-4o',
                        'api_response_tokens': result.get('usage', {}),
                        'purpose': 'OCR_DLP_performance_testing',
                    }

                    return classification_data

                except json.JSONDecodeError as e:
                    return {
                        'error': 'JSON解析失败',
                        'raw_response': content,
                        'json_error': str(e),
                        '_metadata': {
                            'image_path': image_path,
                            'image_info': self.get_image_info(image_path),
                        },
                    }
            else:
                error_text = response.text
                return {
                    'error': f'API请求失败: {response.status_code}',
                    'error_details': error_text,
                    '_metadata': {
                        'image_path': image_path,
                        'image_info': self.get_image_info(image_path),
                    },
                }

        except requests.exceptions.Timeout:
            return {
                'error': 'API request timed out',
                '_metadata': {
                    'image_path': image_path,
                    'image_info': self.get_image_info(image_path),
                },
            }
        except requests.exceptions.RequestException as e:
            return {
                'error': f'Network error: {str(e)}',
                '_metadata': {
                    'image_path': image_path,
                    'image_info': self.get_image_info(image_path),
                },
            }
        except Exception as e:
            return {
                'error': f'请求异常: {str(e)}',
                '_metadata': {
                    'image_path': image_path,
                    'image_info': self.get_image_info(image_path),
                },
            }

    async def classify_image(self, image_path: str) -> dict[str, Any]:
        """Asynchronously classify an image by running the sync logic in a thread."""
        return await asyncio.to_thread(self._classify_image_sync, image_path)


async def classify_images_batch(image_dir: str, output_file: str = "labels.jsonl"):
    """Classify images in batch and save results to JSONL file."""

    # Check OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not found")
        return

    # Initialize labeler
    labeler = GPT4VImageLabeler(api_key)

    # Find image files
    image_dir = Path(image_dir)
    if not image_dir.exists():
        print(f"❌ Image directory not found: {image_dir}")
        return

    image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}
    image_files = [f for f in image_dir.iterdir() if f.suffix.lower() in image_extensions]

    if not image_files:
        print(f"❌ No image files found in: {image_dir}")
        return

    print(f"🔍 Found {len(image_files)} image files")

    # Process images
    results = []
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, image_file in enumerate(image_files, 1):
            print(f"\n📸 Processing {i}/{len(image_files)}: {image_file.name}")

            try:
                # Classify image
                result = await labeler.classify_image(str(image_file))

                # Add file info
                result['_file_info'] = {
                    'filename': image_file.name,
                    'file_path': str(image_file),
                    'processing_order': i,
                }

                # Save to JSONL
                f.write(json.dumps(result, ensure_ascii=False) + '\n')
                f.flush()

                # Show classification summary
                if 'error' not in result:
                    print(f"  ✅ Category: {result.get('document_category', 'N/A')}")
                    print(f"  📋 Subcategory: {result.get('document_subcategory', 'N/A')}")
                    print(f"  🌐 Language: {result.get('language_primary', 'N/A')}")
                    print(f"  📊 OCR Difficulty: {result.get('ocr_difficulty', 'N/A')}")
                    print(f"  🎯 Confidence: {result.get('confidence_score', 'N/A')}")
                else:
                    print(f"  ❌ Error: {result['error']}")

                results.append(result)

            except Exception as e:
                error_result = {
                    'error': f'Processing failed: {str(e)}',
                    '_file_info': {
                        'filename': image_file.name,
                        'file_path': str(image_file),
                        'processing_order': i,
                    },
                }
                f.write(json.dumps(error_result, ensure_ascii=False) + '\n')
                f.flush()
                print(f"  ❌ Processing failed: {e}")
                results.append(error_result)

    print("\n✅ Classification completed!")
    print(f"📁 Results saved to: {output_file}")

    # Generate summary
    generate_classification_summary(results, output_file)

    return results


def generate_classification_summary(results: list[dict], output_file: str):
    """Generate classification summary report."""

    total_images = len(results)
    successful = sum(1 for r in results if 'error' not in r)
    failed = total_images - successful

    # Count categories
    categories = {}
    difficulties = {}
    languages = {}

    for result in results:
        if 'error' not in result:
            # Document categories
            cat = result.get('document_category', 'Unknown')
            categories[cat] = categories.get(cat, 0) + 1

            # OCR difficulties
            diff = result.get('ocr_difficulty', 'Unknown')
            difficulties[diff] = difficulties.get(diff, 0) + 1

            # Languages
            lang = result.get('language_primary', 'Unknown')
            languages[lang] = languages.get(lang, 0) + 1

    # Generate report
    report_file = output_file.replace('.jsonl', '_summary.md')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Image Classification Summary Report\n")
        f.write("=" * 50 + "\n\n")

        f.write("## Overview\n")
        f.write(f"- Total Images: {total_images}\n")
        f.write(f"- Successfully Classified: {successful}\n")
        f.write(f"- Failed: {failed}\n")
        success_rate = successful / total_images * 100 if total_images else 0
        f.write(f"- Success Rate: {success_rate:.1f}%\n\n")

        f.write("## Document Categories\n")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            percentage = count / successful * 100 if successful else 0.0
            f.write(f"- {cat}: {count} ({percentage:.1f}%)\n")
        f.write("\n")

        f.write("## OCR Difficulty Distribution\n")
        for diff, count in sorted(difficulties.items(), key=lambda x: x[1], reverse=True):
            percentage = count / successful * 100 if successful else 0.0
            f.write(f"- {diff}: {count} ({percentage:.1f}%)\n")
        f.write("\n")

        f.write("## Language Distribution\n")
        for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
            percentage = count / successful * 100 if successful else 0.0
            f.write(f"- {lang}: {count} ({percentage:.1f}%)\n")
        f.write("\n")

    print(f"📊 Summary report saved to: {report_file}")


def validate_classification_labels(jsonl_file: str = "labels.jsonl"):
    """Validate classification labels and generate quality report."""

    if not os.path.exists(jsonl_file):
        print(f"❌ File not found: {jsonl_file}")
        return

    print(f"🔍 Validating classification labels in: {jsonl_file}")

    # Required fields for classification
    required_fields = [
        'document_category',
        'document_subcategory',
        'language_primary',
        'text_clarity',
        'image_quality',
        'ocr_difficulty',
    ]

    # Optional but important fields
    important_fields = ['sensitive_data_types', 'testing_scenarios', 'challenge_factors']

    results = []
    with open(jsonl_file, encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line.strip())
                results.append(data)
            except json.JSONDecodeError as e:
                print(f"❌ Line {line_num}: Invalid JSON - {e}")

    print(f"📊 Loaded {len(results)} classification records")

    # Validation statistics
    valid_count = 0
    field_completeness = dict.fromkeys(required_fields + important_fields, 0)

    for result in results:
        if 'error' in result:
            continue

        # Check required fields
        has_all_required = True
        for field in required_fields:
            if field in result and result[field] is not None:
                field_completeness[field] += 1
            else:
                has_all_required = False

        # Check important fields
        for field in important_fields:
            if field in result and result[field] is not None:
                field_completeness[field] += 1

        if has_all_required:
            valid_count += 1

    # Generate validation report
    print("\n📋 Validation Results:")
    print(
        f"✅ Valid classifications: {valid_count}/{len(results)} ({valid_count/len(results)*100:.1f}%)"
    )

    print("\n📊 Field Completeness:")
    for field, count in field_completeness.items():
        percentage = count / len(results) * 100
        status = (
            "✅"
            if field in required_fields and percentage >= 90
            else "⚠️" if percentage >= 70 else "❌"
        )
        print(f"  {status} {field}: {count}/{len(results)} ({percentage:.1f}%)")

    return {
        'total_records': len(results),
        'valid_classifications': valid_count,
        'field_completeness': field_completeness,
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python gpt4v_image_labeler.py <image_directory> [output_file]")
        print("Example: python gpt4v_image_labeler.py ./images labels.jsonl")
        sys.exit(1)

    image_dir = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "labels.jsonl"

    # Check API key
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Please set OPENAI_API_KEY environment variable")
        sys.exit(1)

    # Run classification
    asyncio.run(classify_images_batch(image_dir, output_file))

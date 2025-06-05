#!/usr/bin/env python3
"""
GPT-4V Invoice Analysis Script
Analyzes invoice images and extracts structured tags.
"""

import base64
import json
import os
import time
from pathlib import Path
from typing import Any

from PIL import Image

from http_client import post_with_retry


class GPT4VAnalyzer:
    """GPT-4V image analyzer for invoice documents."""

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

    def analyze_invoice(self, image_path: str) -> dict[str, Any]:
        """Analyze invoice image using GPT-4V."""

        # Encode image
        base64_image = self.encode_image(image_path)

        # Build the analysis prompt
        prompt = """
        请分析这张发票图像，提取以下结构化信息并以JSON格式返回：

        {
            "document_type": "发票类型（如：GST发票、商业发票、税务发票等）",
            "language": "主要语言（如：英语、印地语、泰米尔语等）",
            "currency": "货币类型（如：INR、USD等）",
            "total_amount": "总金额数字",
            "tax_amount": "税额",
            "invoice_number": "发票号码",
            "invoice_date": "发票日期",
            "vendor_name": "供应商/卖方名称",
            "customer_name": "客户/买方名称",
            "items": [
                {
                    "description": "商品描述",
                    "quantity": "数量",
                    "unit_price": "单价",
                    "amount": "金额"
                }
            ],
            "tax_details": {
                "gst_number": "GST号码",
                "tax_rate": "税率",
                "cgst": "中央GST",
                "sgst": "州GST",
                "igst": "综合GST"
            },
            "addresses": {
                "vendor_address": "供应商地址",
                "customer_address": "客户地址"
            },
            "payment_terms": "付款条款",
            "confidence_score": "整体识别置信度(0-1)",
            "extracted_text_sample": "提取的部分文本示例",
            "document_quality": "图像质量评估（清晰/模糊/部分可读）"
        }

        请确保：
        1. 如果某个字段无法识别，设置为null
        2. 金额字段提取纯数字，去除货币符号
        3. 日期格式统一为YYYY-MM-DD
        4. 置信度基于文本清晰度和完整性
        5. 只返回JSON，不要其他解释文字
        """

        # Build request payload
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
            "max_tokens": 2000,
            "temperature": 0.1,
        }

        # Send request
        try:
            response = post_with_retry(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=60,
            )

            if response.status_code == 200:
                result = response.json()

                # Extract the GPT-4V response
                content = result['choices'][0]['message']['content']

                # Attempt to parse JSON
                try:
                    # Clean response text and extract JSON section
                    if '```json' in content:
                        json_start = content.find('```json') + 7
                        json_end = content.find('```', json_start)
                        content = content[json_start:json_end].strip()
                    elif '{' in content:
                        json_start = content.find('{')
                        json_end = content.rfind('}') + 1
                        content = content[json_start:json_end]

                    extracted_data = json.loads(content)

                    # Add metadata to the parsed result
                    extracted_data['_metadata'] = {
                        'image_path': image_path,
                        'image_info': self.get_image_info(image_path),
                        'analysis_timestamp': time.time(),
                        'model_used': 'gpt-4o',
                        'api_response_tokens': result.get('usage', {}),
                    }

                    return extracted_data

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
                return {
                    'error': f'API请求失败: {response.status_code}',
                    'error_details': response.text,
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


def analyze_invoice_images(image_dir: str, output_file: str = "tags.jsonl"):
    """Analyze invoice images and save results to a JSONL file."""

    # Check OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found!")
        return

    analyzer = GPT4VAnalyzer(api_key)

    # Find image files in the directory
    image_dir = Path(image_dir)
    image_files = []
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
        image_files.extend(image_dir.glob(ext))

    if not image_files:
        print(f"❌ No image files found in {image_dir}")
        return

    print(f"🔍 Found {len(image_files)} images to analyze")

    # Analyze each image
    results = []
    for i, image_path in enumerate(image_files, 1):
        print(f"\n📊 Analyzing image {i}/{len(image_files)}: {image_path.name}")

        try:
            result = analyzer.analyze_invoice(str(image_path))
            results.append(result)

            # Show a brief summary
            if 'error' not in result:
                print(f"  ✅ 文档类型: {result.get('document_type', 'N/A')}")
                print(
                    f"  💰 总金额: {result.get('total_amount', 'N/A')} {result.get('currency', 'N/A')}"
                )
                print(f"  🏢 供应商: {result.get('vendor_name', 'N/A')}")
                print(f"  🌐 语言: {result.get('language', 'N/A')}")
                print(f"  📊 置信度: {result.get('confidence_score', 'N/A')}")
            else:
                print(f"  ❌ 分析失败: {result.get('error', 'Unknown error')}")

        except Exception as e:
            error_result = {
                'error': f'处理异常: {str(e)}',
                '_metadata': {
                    'image_path': str(image_path),
                    'image_info': analyzer.get_image_info(str(image_path)),
                },
            }
            results.append(error_result)
            print(f"  ❌ 处理异常: {e}")

    # Save results to JSONL file
    output_path = Path(output_file)
    with open(output_path, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False, indent=None) + '\n')

    print(f"\n💾 Results saved to: {output_path}")
    print(f"📊 Total analyzed: {len(results)} images")

    # Report success rate
    successful = sum(1 for r in results if 'error' not in r)
    print(f"✅ Successful: {successful}/{len(results)} ({successful/len(results)*100:.1f}%)")

    return results


def validate_extracted_fields(jsonl_file: str = "tags.jsonl"):
    """Check that the extracted fields are complete."""

    print(f"\n🔍 Validating extracted fields from {jsonl_file}")

    required_fields = [
        'document_type',
        'language',
        'currency',
        'total_amount',
        'vendor_name',
        'invoice_number',
        'invoice_date',
    ]

    optional_fields = [
        'tax_amount',
        'customer_name',
        'items',
        'tax_details',
        'addresses',
        'payment_terms',
        'confidence_score',
    ]

    try:
        with open(jsonl_file, encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                try:
                    data = json.loads(line.strip())

                    if 'error' in data:
                        print(f"  Record {i}: ❌ Analysis failed - {data['error']}")
                        continue

                    print(
                        f"\n  📄 Record {i} ({data.get('_metadata', {}).get('image_path', 'unknown')}):"
                    )

                    # Check required fields
                    missing_required = []
                    present_required = []
                    for field in required_fields:
                        if field in data and data[field] is not None:
                            present_required.append(field)
                        else:
                            missing_required.append(field)

                    # Check optional fields
                    present_optional = []
                    for field in optional_fields:
                        if field in data and data[field] is not None:
                            present_optional.append(field)

                    print(
                        f"    ✅ Required fields present: {len(present_required)}/{len(required_fields)}"
                    )
                    print(
                        f"    📋 Optional fields present: {len(present_optional)}/{len(optional_fields)}"
                    )

                    if missing_required:
                        print(f"    ❌ Missing required: {', '.join(missing_required)}")

                    # Display key information
                    key_info = {
                        '文档类型': data.get('document_type'),
                        '语言': data.get('language'),
                        '货币': data.get('currency'),
                        '总金额': data.get('total_amount'),
                        '置信度': data.get('confidence_score'),
                    }

                    for key, value in key_info.items():
                        if value is not None:
                            print(f"    📊 {key}: {value}")

                except json.JSONDecodeError as e:
                    print(f"  Record {i}: ❌ JSON parsing error - {e}")

    except FileNotFoundError:
        print(f"❌ File not found: {jsonl_file}")


if __name__ == "__main__":
    import sys

    # Set the image directory
    image_dir = "datasets/invoice_dataset/images"
    if len(sys.argv) > 1:
        image_dir = sys.argv[1]

    # Verify API key
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Please set OPENAI_API_KEY environment variable")
        print("Example: $env:OPENAI_API_KEY='your-api-key-here'")
        exit(1)

    # Run the analysis
    print("🚀 Starting GPT-4V Invoice Analysis")
    results = analyze_invoice_images(image_dir)

    # Validate extracted fields
    if results:
        validate_extracted_fields()

    print("\n🎉 Analysis completed!")

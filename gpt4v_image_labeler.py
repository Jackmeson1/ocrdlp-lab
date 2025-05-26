#!/usr/bin/env python3
"""
GPT-4V Image Labeling Script
Classifies images into fine-grained categories for OCR_DLP system testing.
"""

import os
import json
import base64
import asyncio
from pathlib import Path
from typing import Dict, List, Any
import aiohttp
from PIL import Image


class GPT4VImageLabeler:
    """GPT-4V image labeler for document classification."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    
    def encode_image(self, image_path: str) -> str:
        """Encode image to base64."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def get_image_info(self, image_path: str) -> Dict[str, Any]:
        """Get basic image information."""
        try:
            with Image.open(image_path) as img:
                return {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode,
                    "size_bytes": os.path.getsize(image_path)
                }
        except Exception as e:
            return {"error": str(e)}
    
    async def classify_image(self, image_path: str) -> Dict[str, Any]:
        """Classify image into fine-grained categories for OCR_DLP testing."""
        
        # Encode image
        base64_image = self.encode_image(image_path)
        
        # Build classification prompt
        prompt = """
        请对这张图像进行精细分类，用于OCR_DLP系统性能测试。请返回JSON格式的分类标签：

        {
            "document_category": "文档主类别（如：发票、收据、身份证、护照、驾照、银行卡、合同、证书等）",
            "document_subcategory": "文档子类别（如：GST发票、商业发票、餐厅收据、出租车收据、身份证正面、身份证背面等）",
            "language_primary": "主要语言（如：英语、中文、印地语、泰米尔语、阿拉伯语等）",
            "language_secondary": "次要语言（如果有多语言）",
            "text_density": "文本密度（密集/中等/稀疏）",
            "text_clarity": "文本清晰度（清晰/模糊/部分模糊）",
            "image_quality": "图像质量（高/中/低）",
            "orientation": "图像方向（正向/旋转90度/旋转180度/旋转270度/倾斜）",
            "background_complexity": "背景复杂度（简单/中等/复杂）",
            "ocr_difficulty": "OCR难度等级（简单/中等/困难/极困难）",
            "sensitive_data_types": ["敏感数据类型列表（如：姓名、身份证号、银行卡号、地址、电话等）"],
            "layout_type": "版面类型（表格/列表/段落/混合/手写）",
            "special_features": ["特殊特征（如：水印、印章、签名、条码、二维码、logo等）"],
            "testing_scenarios": ["适用测试场景（如：身份验证、财务审计、合规检查、数据提取等）"],
            "challenge_factors": ["挑战因素（如：字体小、背景干扰、光照不均、倾斜、模糊、多语言等）"],
            "confidence_score": "分类置信度(0-1)",
            "recommended_preprocessing": ["建议预处理步骤（如：去噪、矫正、增强对比度等）"]
        }

        请确保：
        1. 分类要精确和具体，便于OCR_DLP系统性能评估
        2. 识别所有可能影响OCR性能的因素
        3. 提供实用的测试场景建议
        4. 如果无法确定某个字段，设置为null
        5. 只返回JSON，不要其他解释文字
        """
        
        # Build request
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 1500,
            "temperature": 0.1
        }
        
        # Send request
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.base_url, 
                    headers=self.headers, 
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        
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
                                'purpose': 'OCR_DLP_performance_testing'
                            }
                            
                            return classification_data
                            
                        except json.JSONDecodeError as e:
                            return {
                                'error': 'JSON解析失败',
                                'raw_response': content,
                                'json_error': str(e),
                                '_metadata': {
                                    'image_path': image_path,
                                    'image_info': self.get_image_info(image_path)
                                }
                            }
                    else:
                        error_text = await response.text()
                        return {
                            'error': f'API请求失败: {response.status}',
                            'error_details': error_text,
                            '_metadata': {
                                'image_path': image_path,
                                'image_info': self.get_image_info(image_path)
                            }
                        }
                        
            except Exception as e:
                return {
                    'error': f'请求异常: {str(e)}',
                    '_metadata': {
                        'image_path': image_path,
                        'image_info': self.get_image_info(image_path)
                    }
                }


async def classify_images_batch(image_dir: str, output_file: str = "image_labels.jsonl"):
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
    image_files = [f for f in image_dir.iterdir() 
                   if f.suffix.lower() in image_extensions]
    
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
                    'processing_order': i
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
                        'processing_order': i
                    }
                }
                f.write(json.dumps(error_result, ensure_ascii=False) + '\n')
                f.flush()
                print(f"  ❌ Processing failed: {e}")
                results.append(error_result)
    
    print(f"\n✅ Classification completed!")
    print(f"📁 Results saved to: {output_file}")
    
    # Generate summary
    generate_classification_summary(results, output_file)
    
    return results


def generate_classification_summary(results: List[Dict], output_file: str):
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
        f.write(f"- Success Rate: {successful/total_images*100:.1f}%\n\n")
        
        f.write("## Document Categories\n")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            f.write(f"- {cat}: {count} ({count/successful*100:.1f}%)\n")
        f.write("\n")
        
        f.write("## OCR Difficulty Distribution\n")
        for diff, count in sorted(difficulties.items(), key=lambda x: x[1], reverse=True):
            f.write(f"- {diff}: {count} ({count/successful*100:.1f}%)\n")
        f.write("\n")
        
        f.write("## Language Distribution\n")
        for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
            f.write(f"- {lang}: {count} ({count/successful*100:.1f}%)\n")
        f.write("\n")
    
    print(f"📊 Summary report saved to: {report_file}")


def validate_classification_labels(jsonl_file: str = "image_labels.jsonl"):
    """Validate classification labels and generate quality report."""
    
    if not os.path.exists(jsonl_file):
        print(f"❌ File not found: {jsonl_file}")
        return
    
    print(f"🔍 Validating classification labels in: {jsonl_file}")
    
    # Required fields for classification
    required_fields = [
        'document_category', 'document_subcategory', 'language_primary',
        'text_clarity', 'image_quality', 'ocr_difficulty'
    ]
    
    # Optional but important fields
    important_fields = [
        'sensitive_data_types', 'testing_scenarios', 'challenge_factors'
    ]
    
    results = []
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line.strip())
                results.append(data)
            except json.JSONDecodeError as e:
                print(f"❌ Line {line_num}: Invalid JSON - {e}")
    
    print(f"📊 Loaded {len(results)} classification records")
    
    # Validation statistics
    valid_count = 0
    field_completeness = {field: 0 for field in required_fields + important_fields}
    
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
    print(f"\n📋 Validation Results:")
    print(f"✅ Valid classifications: {valid_count}/{len(results)} ({valid_count/len(results)*100:.1f}%)")
    
    print(f"\n📊 Field Completeness:")
    for field, count in field_completeness.items():
        percentage = count / len(results) * 100
        status = "✅" if field in required_fields and percentage >= 90 else "⚠️" if percentage >= 70 else "❌"
        print(f"  {status} {field}: {count}/{len(results)} ({percentage:.1f}%)")
    
    return {
        'total_records': len(results),
        'valid_classifications': valid_count,
        'field_completeness': field_completeness
    }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python gpt4v_image_labeler.py <image_directory> [output_file]")
        print("Example: python gpt4v_image_labeler.py ./images image_labels.jsonl")
        sys.exit(1)
    
    image_dir = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "image_labels.jsonl"
    
    # Check API key
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Please set OPENAI_API_KEY environment variable")
        sys.exit(1)
    
    # Run classification
    asyncio.run(classify_images_batch(image_dir, output_file)) 
# Image Labeling System for OCR_DLP Dataset

## Overview

This system provides **image classification and labeling** functionality specifically designed for **OCR_DLP (Optical Character Recognition - Data Loss Prevention) system testing**. Unlike content extraction, this system focuses on categorizing and labeling images to create fine-grained datasets for performance evaluation.

## 🎯 Purpose

The image labeling system is designed to:
- **Classify documents** into fine-grained categories
- **Identify OCR difficulty levels** and challenge factors
- **Prepare datasets** for OCR_DLP system performance testing
- **Organize images** by document type, quality, and complexity
- **Support testing scenarios** for compliance and security systems

## 🔄 Key Difference: Labeling vs Extraction

| Aspect | **Content Extraction** | **Image Labeling** |
|--------|----------------------|-------------------|
| **Purpose** | Extract specific data values | Classify and categorize images |
| **Output** | Structured data (amounts, names, dates) | Classification labels and metadata |
| **Use Case** | Business process automation | OCR_DLP system testing |
| **Focus** | "What does it say?" (Content) | "What is it?" (Classification) |
| **Example** | Invoice processing, data entry | Dataset preparation, performance testing |

## 📁 File Structure

```
ocrdlp-lab/
├── gpt4v_image_labeler.py          # Main image labeling module
├── test_image_labeling.py          # Comprehensive test suite
├── demo_labeling_vs_extraction.py  # Comparison demonstration
├── run_image_labeling_test.bat     # Batch execution file
└── README_IMAGE_LABELING.md        # This documentation
```

## 🚀 Quick Start

### 1. Set Environment Variables
```bash
set SERPER_API_KEY=your_serper_key
set OPENAI_API_KEY=your_openai_key
```

### 2. Run Image Labeling Test
```bash
python test_image_labeling.py
```

### 3. Run Comparison Demo
```bash
python demo_labeling_vs_extraction.py
```

### 4. Batch Classification
```bash
python gpt4v_image_labeler.py ./images output_labels.jsonl
```

## 📋 Classification Schema

The system provides comprehensive classification with the following fields:

### Core Classification Fields
- **`document_category`**: Main document type (发票, 收据, 身份证, 护照, etc.)
- **`document_subcategory`**: Specific subtype (GST发票, 餐厅收据, 身份证正面, etc.)
- **`language_primary`**: Primary language (英语, 中文, 印地语, etc.)
- **`language_secondary`**: Secondary language (if multilingual)

### Quality Assessment Fields
- **`text_density`**: Text density level (密集/中等/稀疏)
- **`text_clarity`**: Text clarity (清晰/模糊/部分模糊)
- **`image_quality`**: Overall image quality (高/中/低)
- **`orientation`**: Image orientation (正向/旋转90度/倾斜, etc.)

### OCR Performance Fields
- **`ocr_difficulty`**: OCR difficulty level (简单/中等/困难/极困难)
- **`background_complexity`**: Background complexity (简单/中等/复杂)
- **`layout_type`**: Layout type (表格/列表/段落/混合/手写)

### Testing and Security Fields
- **`sensitive_data_types`**: List of sensitive data types (姓名, 身份证号, 银行卡号, etc.)
- **`testing_scenarios`**: Applicable testing scenarios (身份验证, 财务审计, 合规检查, etc.)
- **`challenge_factors`**: Challenge factors (字体小, 背景干扰, 光照不均, etc.)
- **`special_features`**: Special features (水印, 印章, 签名, 条码, etc.)

### Metadata Fields
- **`confidence_score`**: Classification confidence (0-1)
- **`recommended_preprocessing`**: Suggested preprocessing steps

## 🧪 Testing Scenarios

The system identifies images suitable for various OCR_DLP testing scenarios:

### 1. Identity Verification (身份验证)
- ID cards, passports, driver's licenses
- Focus on personal information extraction accuracy

### 2. Financial Auditing (财务审计)
- Invoices, receipts, bank statements
- Focus on numerical data accuracy and compliance

### 3. Compliance Checking (合规检查)
- Legal documents, contracts, certificates
- Focus on sensitive data detection and redaction

### 4. Data Extraction (数据提取)
- Forms, applications, structured documents
- Focus on field extraction accuracy

## 📊 Usage Examples

### Example 1: Single Image Classification
```python
from gpt4v_image_labeler import GPT4VImageLabeler

labeler = GPT4VImageLabeler(api_key)
result = await labeler.classify_image("invoice.jpg")

print(f"Category: {result['document_category']}")
print(f"OCR Difficulty: {result['ocr_difficulty']}")
print(f"Testing Scenarios: {result['testing_scenarios']}")
```

### Example 2: Batch Classification
```python
from gpt4v_image_labeler import classify_images_batch

results = await classify_images_batch(
    image_dir="./dataset_images",
    output_file="labels.jsonl"
)
```

### Example 3: Validation
```python
from gpt4v_image_labeler import validate_classification_labels

validation_results = validate_classification_labels("labels.jsonl")
print(f"Valid classifications: {validation_results['valid_classifications']}")
```

## 📈 Output Format

### JSONL Output Example
```json
{
  "document_category": "发票",
  "document_subcategory": "GST发票",
  "language_primary": "英语",
  "text_clarity": "清晰",
  "image_quality": "高",
  "ocr_difficulty": "简单",
  "sensitive_data_types": ["姓名", "地址", "电话"],
  "testing_scenarios": ["财务审计", "数据提取"],
  "challenge_factors": ["多语言"],
  "confidence_score": 0.95,
  "_metadata": {
    "image_path": "invoice.jpg",
    "classification_timestamp": 1234567890,
    "purpose": "OCR_DLP_performance_testing"
  }
}
```

### Summary Report Example
```markdown
# Image Classification Summary Report

## Overview
- Total Images: 100
- Successfully Classified: 95
- Success Rate: 95.0%

## Document Categories
- 发票: 45 (47.4%)
- 收据: 25 (26.3%)
- 身份证: 15 (15.8%)
- 护照: 10 (10.5%)

## OCR Difficulty Distribution
- 简单: 30 (31.6%)
- 中等: 40 (42.1%)
- 困难: 20 (21.1%)
- 极困难: 5 (5.3%)
```

## 🔧 Configuration

### API Requirements
- **OpenAI API**: GPT-4V for image analysis
- **Serper API**: For image search and download

### Supported Image Formats
- JPEG (.jpg, .jpeg)
- PNG (.png)
- WebP (.webp)
- BMP (.bmp)
- TIFF (.tiff)

### Performance Considerations
- **Rate Limits**: Respects OpenAI API rate limits
- **Token Usage**: Optimized prompts for efficient token usage
- **Error Handling**: Comprehensive error handling and retry logic

## 🎯 OCR_DLP Testing Applications

### 1. Dataset Preparation
- Organize images by difficulty level
- Create balanced test sets
- Identify edge cases and challenging scenarios

### 2. Performance Benchmarking
- Test OCR accuracy across different document types
- Evaluate performance on various image qualities
- Measure sensitivity to different challenge factors

### 3. Compliance Testing
- Verify sensitive data detection capabilities
- Test redaction accuracy
- Validate privacy protection measures

### 4. System Optimization
- Identify preprocessing requirements
- Optimize OCR parameters for different document types
- Improve accuracy for challenging scenarios

## 🚀 Test Results

### Recent Test Execution
```
🎉 IMAGE LABELING TEST COMPLETED SUCCESSFULLY!
✅ OCR_DLP dataset classification system is functional

📊 WORKFLOW SUMMARY REPORT
✅ Image Download: 1 images
✅ Image Classification: 1/1 (100.0%)
✅ Batch Processing: 1/1 valid classifications

🎉 ALL TESTS PASSED - OCR_DLP LABELING SYSTEM READY!
```

### Classification Example
```
📸 Classifying image: invoice.jpg
  ✅ Classification successful:
    📋 Category: 发票
    📄 Subcategory: GST发票
    🌐 Language: 英语
    📊 Text Clarity: 清晰
    🎯 Image Quality: 高
    🔍 OCR Difficulty: 简单
    📈 Confidence: 0.95
    🧪 Testing Scenarios: 财务审计, 数据提取
    ⚠️ Challenge Factors: 多语言
```

## 🔄 Integration with Existing System

The image labeling system integrates seamlessly with the existing OCR_DLP infrastructure:

1. **Search Integration**: Uses existing Serper API integration for image acquisition
2. **Download System**: Leverages existing image download functionality
3. **Testing Framework**: Compatible with existing test infrastructure
4. **API Management**: Uses same OpenAI API key management

## 📚 Additional Resources

- **Test Scripts**: `test_image_labeling.py` for comprehensive testing
- **Comparison Demo**: `demo_labeling_vs_extraction.py` for understanding differences
- **Batch Processing**: `gpt4v_image_labeler.py` for production use
- **Validation Tools**: Built-in validation and quality assessment functions

## 🎉 Conclusion

The image labeling system provides a robust foundation for OCR_DLP dataset preparation and performance testing. By focusing on classification rather than extraction, it enables fine-grained analysis of document types, quality levels, and challenge factors essential for comprehensive OCR system evaluation. 
# OCR_DLP Crawler: Dataset Generation Workflow

## Purpose
This application is a **CRAWLER** that generates **LABELED DATASETS** for downstream model training. It is NOT an evaluation tool - it creates training data for OCR, DLP, and document classification models.

## Workflow: CRAWLER → DATASET → DOWNSTREAM MODELS

### Step 1: Search & Download Images (Crawler Function)
```bash
# Search for document images
python ocrdlp.py search "invoice documents" --engine serper --limit 100 --output invoice_urls.txt

# Download images to dataset
python ocrdlp.py download --urls-file invoice_urls.txt --output-dir ./datasets/invoice_images
```

### Step 2: Generate Labels (AI Labeling)
```bash
# Create dataset structure
mkdir datasets/invoice_dataset/images
mkdir datasets/invoice_dataset/labels

# Copy images to dataset
copy datasets/invoice_images/*.* datasets/invoice_dataset/images/

# Generate comprehensive labels
python ocrdlp.py classify datasets/invoice_dataset/images --output datasets/invoice_dataset/labels/labels.jsonl
```

### Step 3: Package Dataset for Downstream Use
```bash
# Validate dataset quality
python ocrdlp.py validate datasets/invoice_dataset/labels/labels.jsonl

# Dataset is now ready for model training
```

## Generated Dataset Structure
```
datasets/
└── invoice_dataset/
    ├── images/              # Raw images for training
    │   ├── image_001.jpg
    │   ├── image_002.png
    │   └── ...
    ├── labels/              # AI-generated labels
    │   ├── labels.jsonl     # Comprehensive labels
    │   └── summary.md       # Dataset statistics
    └── README.md            # Usage instructions
```

## Downstream Model Usage

### OCR Model Training
The generated dataset provides:
- Image difficulty assessment
- Text clarity ratings
- Language identification
- OCR challenge factors

### DLP Model Training
The generated dataset provides:
- Sensitive data type identification
- Privacy risk assessment
- Document categorization
- Compliance scenarios

### Document Classification Training
The generated dataset provides:
- Document categories/subcategories
- Confidence scores
- Feature extraction guidance
- Quality assessments

## Key Benefits

1. **Automated Labeling**: Uses GPT-4V to generate comprehensive labels
2. **Scalable**: Can process thousands of images
3. **Comprehensive**: Provides multiple label types for different use cases
4. **Production-Ready**: Generates standard dataset formats
5. **Quality Assured**: Built-in validation and quality checks

## This is NOT an evaluation tool
- ❌ This is not for testing existing models
- ❌ This is not for performance benchmarking
- ✅ This IS for generating training datasets
- ✅ This IS for creating labeled data for model development

## Next Steps After Dataset Generation
1. Load dataset into your ML training framework
2. Split into train/validation/test sets
3. Train your OCR/DLP/Classification models
4. Use the comprehensive labels for supervised learning
5. Iterate and expand dataset as needed 
# OCR_DLP Image Crawler & Dataset Generator

A comprehensive CLI application for **crawling images** and **generating labeled datasets** for OCR (Optical Character Recognition) and DLP (Data Loss Prevention) model training.

## 🎯 Purpose

This is a **CRAWLER APPLICATION** that generates **LABELED DATASETS** for downstream model training. It crawls images from various sources and uses AI to generate comprehensive labels for training OCR, DLP, and document classification models.

**Workflow: CRAWLER → LABELED DATASET → DOWNSTREAM MODEL TRAINING**

### Key Features

- 🔍 **Multi-Engine Image Search**: Serper, Google, Bing, DuckDuckGo integration
- 📥 **Robust Image Download**: Automated download with validation and error handling
- 🤖 **AI-Powered Labeling**: GPT-4V integration for intelligent document labeling
- 🏷️ **Comprehensive Labels**: Multi-purpose labels for OCR, DLP, and classification training
- 📁 **Dataset Generation**: Creates production-ready datasets with standard structure
- ⚡ **CLI Interface**: Professional command-line tool with subcommands
- ✅ **Quality Validation**: Built-in dataset quality checks

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key (for GPT-4V labeling)
- Serper API key (for image search)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ocrdlp-lab
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables**
   ```bash
   # Windows
   set SERPER_API_KEY=your_serper_api_key
   set OPENAI_API_KEY=your_openai_api_key
   
   # Linux/Mac
   export SERPER_API_KEY=your_serper_api_key
   export OPENAI_API_KEY=your_openai_api_key
   ```

### Verify Installation

```bash
python ocrdlp.py --help
```

## 📋 Dataset Generation Workflow

### 1. Search for Images

```bash
# Search for document images
python ocrdlp.py search "invoice documents" --engine serper --limit 100 --output urls.txt
```

### 2. Download Images

```bash
# Download images directly into the dataset
python ocrdlp.py download --urls-file urls.txt --output-dir ./datasets/invoice_dataset
```

### 3. Generate Dataset with Labels

```bash
# Generate comprehensive labels
python ocrdlp.py classify datasets/invoice_dataset/images --output datasets/invoice_dataset/labels/invoice_dataset_labels.jsonl
```

### 4. Validate Dataset Quality

```bash
# Validate generated dataset
python ocrdlp.py validate datasets/invoice_dataset/labels/invoice_dataset_labels.jsonl
```

## 🏗️ Generated Dataset Structure

```
datasets/
└── invoice_dataset/
    ├── images/              # Raw images for training
    │   ├── image_001.jpg
    │   ├── image_002.png
    │   └── ...
    ├── labels/              # AI-generated labels
    │   ├── <dataset>_labels.jsonl     # Comprehensive labels
    │   └── <dataset>_labels_summary.md       # Dataset statistics
    └── README.md            # Usage instructions for ML engineers
```

## 📊 Label Schema

Each image gets comprehensive labels for multiple downstream use cases:

- **Document Classification**: `document_category`, `document_subcategory`
- **OCR Training**: `ocr_difficulty`, `text_clarity`, `language_primary`
- **DLP Training**: `sensitive_data_types`, `testing_scenarios`
- **Quality Assessment**: `image_quality`, `background_complexity`
- **Processing Hints**: `recommended_preprocessing`, `challenge_factors`

## 🎯 Downstream Model Usage

### OCR Model Training
```python
import json

def load_ocr_dataset(dataset_path):
    labels_path = f"{dataset_path}/labels/<dataset>_labels.jsonl"
    with open(labels_path, 'r') as f:
        labels = [json.loads(line) for line in f]
    
    return [{
        'image_path': label['_file_info']['file_path'],
        'difficulty': label['ocr_difficulty'],
        'text_clarity': label['text_clarity'],
        'language': label['language_primary']
    } for label in labels]
```

### DLP Model Training
```python
def load_dlp_dataset(dataset_path):
    labels_path = f"{dataset_path}/labels/<dataset>_labels.jsonl"
    with open(labels_path, 'r') as f:
        labels = [json.loads(line) for line in f]
    
    return [{
        'image_path': label['_file_info']['file_path'],
        'sensitive_data': label['sensitive_data_types'],
        'document_type': label['document_category']
    } for label in labels]
```

## 🔧 CLI Commands

### Search Command
```bash
python ocrdlp.py search "document type" --engine serper --limit 50 --output urls.txt
```

### Download Command
```bash
python ocrdlp.py download --urls-file urls.txt --output-dir ./datasets/invoice_dataset
# OR
python ocrdlp.py download --query "invoice" --output-dir ./datasets/invoice_dataset --limit 20
```

### Classify Command
```bash
python ocrdlp.py classify ./datasets/invoice_dataset/images --output ./datasets/invoice_dataset/labels/invoice_dataset_labels.jsonl --validate
```

### Pipeline Command (Complete Workflow)
```bash
python ocrdlp.py pipeline "invoice documents" --output-dir ./datasets/invoice_dataset --limit 50
```

### Validate Command
```bash
python ocrdlp.py validate ./datasets/invoice_dataset/labels/invoice_dataset_labels.jsonl
```

## 🎉 Example: Creating Invoice Dataset

```bash
# Complete workflow to create invoice training dataset
python ocrdlp.py pipeline "invoice documents" --output-dir ./datasets/invoices --limit 100

# Dataset is now ready at ./datasets/invoices/
# - images/ contains downloaded invoice images
# - labels/invoices_labels.jsonl contains comprehensive labels
```

## 🛠️ Development

### Run Tests
```bash
python test_viability.py
python test_image_labeling.py
```

### Direct Labeling (Alternative)
```bash
python gpt4v_image_labeler.py ./images invoice_labels.jsonl
```

## 📈 Key Benefits

1. **Automated Dataset Creation** - No manual labeling required
2. **Multi-Purpose Labels** - One dataset serves multiple model types  
3. **Production-Ready** - Standard ML dataset format
4. **Scalable** - Can generate thousands of labeled images
5. **Quality Assured** - Built-in validation and quality checks

---

**This is a CRAWLER for DATASET GENERATION, not a model evaluation tool.**

Generated datasets are ready for use in training OCR, DLP, and document classification models. 
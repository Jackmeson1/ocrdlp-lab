# OCR_DLP Image Crawler - MVP

> This guide covers GPT-4V based image labeling for OCR / DLP.

## Purpose
**CRAWLER APPLICATION** for generating **LABELED DATASETS** for downstream model training.

## Core Functionality
1. **Search & Download Images** - Multi-engine image crawling
2. **AI-Powered Labeling** - GPT-4V generates comprehensive labels
3. **Dataset Generation** - Creates production-ready training datasets

## MVP Workflow
```bash
# Complete dataset generation in one command
python ocrdlp.py pipeline "invoice documents" --output-dir ./datasets/invoices --limit 100
```

## Generated Output
```
datasets/
└── invoices/
    ├── images/                            # Downloaded images
    └── labels/
        ├── invoices_labels.jsonl          # AI-generated labels
        └── invoices_labels_summary.md
```

## Key Features
- ✅ Multi-engine image search (Serper, Google, Bing, DuckDuckGo)
- ✅ Automated image download with validation
- ✅ GPT-4V powered comprehensive labeling
- ✅ Production-ready dataset structure
- ✅ Built-in quality validation
- ✅ CLI interface with pipeline command

## Use Cases
- **OCR Model Training** - Text extraction difficulty assessment
- **DLP Model Training** - Sensitive data identification
- **Document Classification** - Category and subcategory labeling

## MVP Status: ✅ COMPLETE
- Core crawler functionality working
- AI labeling generating comprehensive labels
- Standard dataset output format
- CLI interface operational
- Quality validation included

## Next Steps for Users
1. Set API keys (OpenAI + Serper)
2. Run pipeline command with desired document type
3. Use generated dataset for model training
4. Iterate and expand datasets as needed 
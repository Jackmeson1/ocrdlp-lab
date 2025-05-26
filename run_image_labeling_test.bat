@echo off
echo ========================================
echo Image Labeling Test for OCR_DLP Dataset
echo ========================================

REM Set API keys
set SERPER_API_KEY=5302dc9d13040cc26ac9fcefa4956ec15fc1eba3
set OPENAI_API_KEY=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

echo 🔧 Environment variables set
echo 🎯 Testing image classification for OCR_DLP system
echo 📋 Focus: Document categorization and labeling
echo.

python test_image_labeling.py

echo.
echo ========================================
echo Image labeling test completed
echo ========================================
pause 
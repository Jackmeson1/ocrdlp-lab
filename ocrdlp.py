#!/usr/bin/env python3
"""
OCR_DLP Image Labeling System - Command Line Interface
A comprehensive CLI tool for image classification and labeling for OCR/DLP testing.
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
from typing import List, Optional

# Import core modules
from crawler.search import search_images, download_images
from gpt4v_image_labeler import GPT4VImageLabeler, classify_images_batch, validate_classification_labels


class OCRDLPCli:
    """Main CLI application for OCR_DLP Image Labeling System"""
    
    def __init__(self):
        self.serper_key = os.getenv('SERPER_API_KEY')
        self.openai_key = os.getenv('OPENAI_API_KEY')
        
    def check_api_keys(self):
        """Check if required API keys are available"""
        missing_keys = []
        
        if not self.serper_key:
            missing_keys.append('SERPER_API_KEY')
        if not self.openai_key:
            missing_keys.append('OPENAI_API_KEY')
            
        if missing_keys:
            print(f"❌ Missing required environment variables: {', '.join(missing_keys)}")
            print("Please set them before running the application.")
            return False
        return True
    
    async def search_command(self, args):
        """Search for images based on query"""
        print(f"🔍 Searching for images: '{args.query}'")
        print(f"📊 Engine: {args.engine}, Limit: {args.limit}")
        
        try:
            urls = await search_images(
                query=args.query,
                engine=args.engine,
                limit=args.limit
            )
            
            if urls:
                print(f"✅ Found {len(urls)} image URLs")
                
                # Save URLs to file if requested
                if args.output:
                    output_file = Path(args.output)
                    with open(output_file, 'w') as f:
                        for url in urls:
                            f.write(f"{url}\n")
                    print(f"💾 URLs saved to: {output_file}")
                else:
                    # Display URLs
                    for i, url in enumerate(urls, 1):
                        print(f"  {i}. {url}")
            else:
                print("❌ No images found")
                
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return 1
        
        return 0
    
    async def download_command(self, args):
        """Download images from URLs or search results"""
        print(f"📥 Downloading images to: {args.output_dir}")
        
        # Create output directory
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        urls = []
        
        if args.urls_file:
            # Read URLs from file
            print(f"📄 Reading URLs from: {args.urls_file}")
            with open(args.urls_file, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
        elif args.query:
            # Search for images first
            print(f"🔍 Searching for: '{args.query}'")
            urls = await search_images(
                query=args.query,
                engine=args.engine,
                limit=args.limit
            )
        else:
            print("❌ Either --query or --urls-file must be provided")
            return 1
        
        if not urls:
            print("❌ No URLs to download")
            return 1
        
        print(f"📥 Downloading {len(urls)} images...")
        
        try:
            results = await download_images(urls, output_dir=str(output_dir))
            
            if results:
                print(f"✅ Downloaded {len(results)} images successfully")
                for url, path in results.items():
                    print(f"  ✅ {Path(path).name}")
            else:
                print("❌ No images downloaded successfully")
                return 1
                
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return 1
        
        return 0
    
    async def classify_command(self, args):
        """Classify images in a directory"""
        print(f"🤖 Classifying images in: {args.input_dir}")
        print(f"💾 Output file: {args.output}")
        
        input_dir = Path(args.input_dir)
        if not input_dir.exists():
            print(f"❌ Input directory not found: {input_dir}")
            return 1
        
        try:
            results = await classify_images_batch(
                image_dir=str(input_dir),
                output_file=args.output
            )
            
            if results:
                successful = sum(1 for r in results if 'error' not in r)
                print(f"✅ Classification completed: {successful}/{len(results)} successful")
                
                # Validate results if requested
                if args.validate:
                    print(f"🔍 Validating classification results...")
                    validation_results = validate_classification_labels(args.output)
                    if validation_results:
                        valid_count = validation_results['valid_classifications']
                        total_count = validation_results['total_records']
                        print(f"📊 Validation: {valid_count}/{total_count} valid classifications")
            else:
                print("❌ Classification failed")
                return 1
                
        except Exception as e:
            print(f"❌ Classification failed: {e}")
            return 1
        
        return 0
    
    async def pipeline_command(self, args):
        """Run complete pipeline: search -> download -> classify"""
        print(f"🚀 Running complete pipeline for: '{args.query}'")
        
        # Create output directory
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Step 1: Search
            print(f"\n🔍 Step 1: Searching for images...")
            urls = await search_images(
                query=args.query,
                engine=args.engine,
                limit=args.limit
            )
            
            if not urls:
                print("❌ No images found")
                return 1
            
            print(f"✅ Found {len(urls)} image URLs")
            
            # Step 2: Download
            print(f"\n📥 Step 2: Downloading images...")
            results = await download_images(urls, output_dir=str(output_dir))
            
            if not results:
                print("❌ No images downloaded")
                return 1
            
            print(f"✅ Downloaded {len(results)} images")
            
            # Step 3: Classify
            print(f"\n🤖 Step 3: Classifying images...")
            output_file = output_dir / "classifications.jsonl"
            
            classification_results = await classify_images_batch(
                image_dir=str(output_dir),
                output_file=str(output_file)
            )
            
            if classification_results:
                successful = sum(1 for r in classification_results if 'error' not in r)
                print(f"✅ Pipeline completed successfully!")
                print(f"📊 Results: {successful}/{len(classification_results)} images classified")
                print(f"💾 Classifications saved to: {output_file}")
            else:
                print("❌ Classification step failed")
                return 1
                
        except Exception as e:
            print(f"❌ Pipeline failed: {e}")
            return 1
        
        return 0
    
    async def validate_command(self, args):
        """Validate classification results"""
        print(f"🔍 Validating classification file: {args.input}")
        
        if not Path(args.input).exists():
            print(f"❌ File not found: {args.input}")
            return 1
        
        try:
            validation_results = validate_classification_labels(args.input)
            
            if validation_results:
                print(f"✅ Validation completed")
                print(f"📊 Total records: {validation_results['total_records']}")
                print(f"📊 Valid classifications: {validation_results['valid_classifications']}")
                
                success_rate = validation_results['valid_classifications'] / validation_results['total_records'] * 100
                print(f"📊 Success rate: {success_rate:.1f}%")
                
                # Show field completeness
                print(f"\n📋 Field Completeness:")
                for field, count in validation_results['field_completeness'].items():
                    percentage = count / validation_results['total_records'] * 100
                    print(f"  {field}: {count}/{validation_results['total_records']} ({percentage:.1f}%)")
            else:
                print("❌ Validation failed")
                return 1
                
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            return 1
        
        return 0
    
    def create_parser(self):
        """Create argument parser"""
        parser = argparse.ArgumentParser(
            prog='ocrdlp',
            description='OCR_DLP Image Labeling System - CLI Tool for image classification and labeling',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Search for images
  ocrdlp search "indian aadhaar card" --engine serper --limit 10 --output urls.txt
  
  # Download images
  ocrdlp download --query "invoice document" --output-dir ./images --limit 5
  
  # Classify images
  ocrdlp classify ./images --output classifications.jsonl --validate
  
  # Run complete pipeline
  ocrdlp pipeline "indian passport" --output-dir ./passport_data --limit 20
  
  # Validate results
  ocrdlp validate classifications.jsonl
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Search command
        search_parser = subparsers.add_parser('search', help='Search for images')
        search_parser.add_argument('query', help='Search query')
        search_parser.add_argument('--engine', choices=['serper', 'google', 'bing', 'duckduckgo', 'mixed'], 
                                 default='serper', help='Search engine to use')
        search_parser.add_argument('--limit', type=int, default=10, help='Maximum number of images to find')
        search_parser.add_argument('--output', help='Save URLs to file')
        
        # Download command
        download_parser = subparsers.add_parser('download', help='Download images')
        download_group = download_parser.add_mutually_exclusive_group(required=True)
        download_group.add_argument('--query', help='Search query for images')
        download_group.add_argument('--urls-file', help='File containing URLs to download')
        download_parser.add_argument('--output-dir', required=True, help='Output directory for images')
        download_parser.add_argument('--engine', choices=['serper', 'google', 'bing', 'duckduckgo', 'mixed'], 
                                   default='serper', help='Search engine (when using --query)')
        download_parser.add_argument('--limit', type=int, default=10, help='Maximum images to download (when using --query)')
        
        # Classify command
        classify_parser = subparsers.add_parser('classify', help='Classify images')
        classify_parser.add_argument('input_dir', help='Directory containing images to classify')
        classify_parser.add_argument('--output', default='classifications.jsonl', help='Output JSONL file')
        classify_parser.add_argument('--validate', action='store_true', help='Validate results after classification')
        
        # Pipeline command
        pipeline_parser = subparsers.add_parser('pipeline', help='Run complete pipeline')
        pipeline_parser.add_argument('query', help='Search query')
        pipeline_parser.add_argument('--output-dir', required=True, help='Output directory')
        pipeline_parser.add_argument('--engine', choices=['serper', 'google', 'bing', 'duckduckgo', 'mixed'], 
                                   default='serper', help='Search engine to use')
        pipeline_parser.add_argument('--limit', type=int, default=10, help='Maximum number of images')
        
        # Validate command
        validate_parser = subparsers.add_parser('validate', help='Validate classification results')
        validate_parser.add_argument('input', help='JSONL file to validate')
        
        return parser
    
    async def run(self, args=None):
        """Main entry point"""
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)
        
        if not parsed_args.command:
            parser.print_help()
            return 1
        
        # Check API keys for commands that need them
        if parsed_args.command in ['search', 'download', 'classify', 'pipeline']:
            if not self.check_api_keys():
                return 1
        
        # Route to appropriate command
        if parsed_args.command == 'search':
            return await self.search_command(parsed_args)
        elif parsed_args.command == 'download':
            return await self.download_command(parsed_args)
        elif parsed_args.command == 'classify':
            return await self.classify_command(parsed_args)
        elif parsed_args.command == 'pipeline':
            return await self.pipeline_command(parsed_args)
        elif parsed_args.command == 'validate':
            return await self.validate_command(parsed_args)
        else:
            parser.print_help()
            return 1


def main():
    """Main entry point for CLI"""
    cli = OCRDLPCli()
    
    try:
        exit_code = asyncio.run(cli.run())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 
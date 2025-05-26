"""
Image crawler for collecting images from various sources.
"""

import asyncio
import aiohttp
import aiofiles
import os
import json
from typing import List, Dict, Optional, Set
from urllib.parse import urlparse, urljoin
from pathlib import Path
import logging
from tqdm.asyncio import tqdm

from .filters import ImageFilter
from .deduplicator import ImageDeduplicator
from .search import ImageSearchEngine


class ImageCrawler:
    """Async image crawler with filtering and deduplication."""
    
    def __init__(self, 
                 output_dir: str = "ocr_dataset/full",
                 max_concurrent: int = 10,
                 retry_attempts: int = 3):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_concurrent = max_concurrent
        self.retry_attempts = retry_attempts
        self.session: Optional[aiohttp.ClientSession] = None
        self.filter = ImageFilter()
        self.deduplicator = ImageDeduplicator()
        self.downloaded_urls: Set[str] = set()
        self.search_engine: Optional[ImageSearchEngine] = None
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def __aenter__(self):
        """Async context manager entry."""
        connector = aiohttp.TCPConnector(limit=self.max_concurrent)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        self.search_engine = ImageSearchEngine(self.session)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def search_images(self, keywords: List[str], max_per_keyword: int = 100, 
                           engine: str = "mixed") -> List[str]:
        """
        Search for image URLs using multiple sources or a specific engine.
        
        Args:
            keywords: List of search keywords
            max_per_keyword: Maximum URLs per keyword
            engine: Search engine to use ("mixed", "serper", "serpapi", "unsplash", "flickr")
        """
        all_urls = []
        
        for keyword in keywords:
            self.logger.info(f"Searching images for keyword: {keyword}")
            
            if engine == "mixed":
                # Use multiple sources (legacy behavior)
                urls = []
                urls.extend(await self._search_engine_wrapper("serper", keyword, max_per_keyword // 4))
                urls.extend(await self._search_engine_wrapper("unsplash", keyword, max_per_keyword // 4))
                urls.extend(await self._search_engine_wrapper("serpapi", keyword, max_per_keyword // 4))
                urls.extend(await self._search_engine_wrapper("flickr", keyword, max_per_keyword // 4))
            else:
                # Use specific engine
                urls = await self._search_engine_wrapper(engine, keyword, max_per_keyword)
            
            # Remove duplicates and add to main list
            unique_urls = list(set(urls))[:max_per_keyword]
            all_urls.extend(unique_urls)
            
            self.logger.info(f"Found {len(unique_urls)} unique URLs for '{keyword}' using {engine}")
        
        return list(set(all_urls))  # Remove global duplicates
    
    async def _search_engine_wrapper(self, engine: str, keyword: str, limit: int) -> List[str]:
        """Wrapper for the unified search engine interface."""
        try:
            return await self.search_engine.search_images(keyword, engine, limit)
        except Exception as e:
            self.logger.error(f"Error searching with {engine}: {e}")
            return []

    # Legacy methods for backward compatibility
    async def _search_unsplash(self, keyword: str, limit: int) -> List[str]:
        """Search Unsplash for images."""
        return await self._search_engine_wrapper("unsplash", keyword, limit)
    
    async def _search_google_images(self, keyword: str, limit: int) -> List[str]:
        """Search Google Images via SerpAPI."""
        return await self._search_engine_wrapper("serpapi", keyword, limit)
    
    async def _search_flickr(self, keyword: str, limit: int) -> List[str]:
        """Search Flickr for images."""
        return await self._search_engine_wrapper("flickr", keyword, limit)
    
    async def _search_serper(self, keyword: str, limit: int) -> List[str]:
        """Search images using Serper.dev API."""
        return await self._search_engine_wrapper("serper", keyword, limit)

    async def download_images(self, urls: List[str]) -> Dict[str, str]:
        """Download images with filtering and deduplication."""
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # Create download tasks
        tasks = []
        for i, url in enumerate(urls):
            if url not in self.downloaded_urls:
                task = self._download_single_image(semaphore, url, f"image_{i:06d}")
                tasks.append(task)
        
        # Execute downloads with progress bar
        results = {}
        if tasks:
            completed_tasks = await tqdm.gather(*tasks, desc="Downloading images")
            for result in completed_tasks:
                if result:
                    results.update(result)
        
        self.logger.info(f"Successfully downloaded {len(results)} images")
        return results
    
    async def _download_single_image(self, semaphore: asyncio.Semaphore, 
                                   url: str, filename_base: str) -> Optional[Dict[str, str]]:
        """Download a single image with retry logic."""
        async with semaphore:
            for attempt in range(self.retry_attempts):
                try:
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            content = await response.read()
                            
                            # Determine file extension
                            content_type = response.headers.get('content-type', '')
                            if 'jpeg' in content_type or 'jpg' in content_type:
                                ext = '.jpg'
                            elif 'png' in content_type:
                                ext = '.png'
                            elif 'webp' in content_type:
                                ext = '.webp'
                            else:
                                # Try to guess from URL
                                parsed = urlparse(url)
                                path_ext = os.path.splitext(parsed.path)[1].lower()
                                ext = path_ext if path_ext in ['.jpg', '.jpeg', '.png', '.webp'] else '.jpg'
                            
                            filename = f"{filename_base}{ext}"
                            filepath = self.output_dir / filename
                            
                            # Save image
                            async with aiofiles.open(filepath, 'wb') as f:
                                await f.write(content)
                            
                            # Apply filters
                            if await self.filter.is_valid_image(filepath):
                                # Check for duplicates
                                if not await self.deduplicator.is_duplicate(filepath):
                                    self.downloaded_urls.add(url)
                                    return {url: str(filepath)}
                                else:
                                    # Remove duplicate
                                    os.remove(filepath)
                                    self.logger.debug(f"Removed duplicate image: {filename}")
                            else:
                                # Remove invalid image
                                os.remove(filepath)
                                self.logger.debug(f"Removed invalid image: {filename}")
                            
                            break
                        
                        elif response.status in [404, 403, 410]:
                            # Don't retry for these errors
                            break
                            
                except Exception as e:
                    if attempt == self.retry_attempts - 1:
                        self.logger.error(f"Failed to download {url} after {self.retry_attempts} attempts: {e}")
                    else:
                        await asyncio.sleep(1)  # Wait before retry
        
        return None
    
    async def crawl_keywords(self, keywords: List[str], max_images: int = 500) -> Dict[str, str]:
        """Main crawling method."""
        self.logger.info(f"Starting crawl for {len(keywords)} keywords, max {max_images} images")
        
        # Search for image URLs
        max_per_keyword = max_images // len(keywords) if keywords else max_images
        urls = await self.search_images(keywords, max_per_keyword)
        
        # Limit total URLs
        urls = urls[:max_images]
        self.logger.info(f"Found {len(urls)} total URLs to download")
        
        # Download images
        results = await self.download_images(urls)
        
        return results 
"""
Unified image search interface supporting multiple search engines.
"""

import aiohttp
import requests
import os
import logging
from typing import List, Dict, Optional
from urllib.parse import urlparse


class ImageSearchEngine:
    """Unified image search engine supporting multiple providers."""

    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        self.session = session
        self.logger = logging.getLogger(__name__)

    async def search_images(self, query: str, engine: str = "serper", limit: int = 100) -> List[str]:
        """
        Unified interface for image search across multiple engines.

        Args:
            query: Search query string
            engine: Search engine to use ("serper", "serpapi", "unsplash", "flickr")
            limit: Maximum number of URLs to return

        Returns:
            List of image URLs
        """
        if engine == "serper":
            return await self._search_serper(query, limit)
        elif engine == "serpapi":
            return await self._search_serpapi(query, limit)
        elif engine == "unsplash":
            return await self._search_unsplash(query, limit)
        elif engine == "flickr":
            return await self._search_flickr(query, limit)
        else:
            raise ValueError(f"Unsupported search engine: {engine}")

    async def _search_serper(self, query: str, limit: int) -> List[str]:
        """Search images using Serper.dev API."""
        api_key = os.getenv('SERPER_API_KEY')
        if not api_key:
            self.logger.warning("SERPER_API_KEY not found, skipping Serper search")
            return []

        url = "https://google.serper.dev/images"
        headers = {
            'X-API-KEY': api_key,
            'Content-Type': 'application/json'
        }
        payload = {
            'q': query,
            'num': min(limit, 100)
        }

        async with self.session.post(url, headers=headers, json=payload, timeout=10) as response:
            if response.status != 200:
                return []
            data = await response.json()
            images = data.get('images', [])
            urls = []
            for img in images:
                if 'imageUrl' in img:
                    urls.append(img['imageUrl'])
                elif 'link' in img:
                    urls.append(img['link'])
            return urls[:limit]

    async def _search_serpapi(self, query: str, limit: int) -> List[str]:
        """Search Google Images via SerpAPI."""
        api_key = os.getenv('SERPAPI_KEY')
        if not api_key:
            self.logger.warning("SERPAPI_KEY not found, skipping SerpAPI search")
            return []

        try:
            url = "https://serpapi.com/search"
            params = {
                'engine': 'google_images',
                'q': query,
                'api_key': api_key,
                'num': min(limit, 100),
                'safe': 'off'
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    images = data.get('images_results', [])
                    return [img['original'] for img in images if 'original' in img][:limit]
        except Exception as e:
            self.logger.error(f"SerpAPI search error: {e}")

        return []

    async def _search_unsplash(self, query: str, limit: int) -> List[str]:
        """Search Unsplash for images."""
        access_key = os.getenv('UNSPLASH_ACCESS_KEY')
        if not access_key:
            self.logger.warning("UNSPLASH_ACCESS_KEY not found, skipping Unsplash search")
            return []

        try:
            url = f"https://api.unsplash.com/search/photos"
            params = {
                'query': query,
                'per_page': min(limit, 30),
                'orientation': 'all'
            }
            headers = {'Authorization': f'Client-ID {access_key}'}

            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return [photo['urls']['regular'] for photo in data.get('results', [])][:limit]
        except Exception as e:
            self.logger.error(f"Unsplash search error: {e}")

        return []

    async def _search_flickr(self, query: str, limit: int) -> List[str]:
        """Search Flickr for images."""
        api_key = os.getenv('FLICKR_KEY')
        if not api_key:
            self.logger.warning("FLICKR_KEY not found, skipping Flickr search")
            return []

        try:
            url = "https://api.flickr.com/services/rest/"
            params = {
                'method': 'flickr.photos.search',
                'api_key': api_key,
                'text': query,
                'format': 'json',
                'nojsoncallback': 1,
                'per_page': min(limit, 100),
                'media': 'photos'
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    photos = data.get('photos', {}).get('photo', [])
                    urls = []
                    for photo in photos:
                        # Construct Flickr image URL
                        farm = photo['farm']
                        server = photo['server']
                        photo_id = photo['id']
                        secret = photo['secret']
                        url = f"https://farm{farm}.staticflickr.com/{server}/{photo_id}_{secret}_b.jpg"
                        urls.append(url)
                    return urls[:limit]
        except Exception as e:
            self.logger.error(f"Flickr search error: {e}")

        return []


# Convenience function for direct usage
async def search_images(query: str, engine: str = "serper", limit: int = 100,
                       session: Optional[aiohttp.ClientSession] = None) -> List[str]:
    """
    Convenience function for searching images with a unified interface.

    Args:
        query: Search query string
        engine: Search engine to use ("serper", "serpapi", "unsplash", "flickr")
        limit: Maximum number of URLs to return
        session: Optional aiohttp session (will create one if not provided)

    Returns:
        List of image URLs
    """
    close_session = False
    if session is None:
        timeout = aiohttp.ClientTimeout(total=30)
        session = aiohttp.ClientSession(
            timeout=timeout,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        close_session = True

    try:
        search_engine = ImageSearchEngine(session)
        return await search_engine.search_images(query, engine, limit)
    finally:
        if close_session:
            await session.close()


# Download function for testing
async def download_images(urls: List[str], output_dir: str = "test_downloads",
                         session: Optional[aiohttp.ClientSession] = None) -> Dict[str, str]:
    """
    Download images from URLs for testing purposes.

    Args:
        urls: List of image URLs to download
        output_dir: Directory to save images
        session: Optional aiohttp session

    Returns:
        Dictionary mapping URLs to local file paths
    """
    import aiofiles
    from pathlib import Path

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    close_session = False
    if session is None:
        timeout = aiohttp.ClientTimeout(total=30)
        session = aiohttp.ClientSession(
            timeout=timeout,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        close_session = True

    results = {}
    logger = logging.getLogger(__name__)

    try:
        for i, url in enumerate(urls):
            try:
                async with session.get(url) as response:
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

                        filename = f"image_{i:06d}{ext}"
                        filepath = output_path / filename

                        # Save image
                        async with aiofiles.open(filepath, 'wb') as f:
                            await f.write(content)

                        results[url] = str(filepath)
                        logger.info(f"Downloaded: {filename}")
                    else:
                        logger.warning(f"Failed to download {url}: HTTP {response.status}")
            except Exception as e:
                logger.error(f"Error downloading {url}: {e}")
    finally:
        if close_session:
            await session.close()

    return results

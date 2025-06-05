"""
Unified image search interface supporting multiple search engines.
"""

import asyncio
import logging
import os
from urllib.parse import urlparse

import requests


class ImageSearchEngine:
    """Unified image search engine supporting multiple providers."""

    def __init__(self, session=None):
        self.logger = logging.getLogger(__name__)
        self.session = session

    async def search_images(
        self, query: str, engine: str = "serper", limit: int = 100
    ) -> list[str]:
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
            return await asyncio.to_thread(self._search_serper, query, limit)
        elif engine == "serpapi":
            return await asyncio.to_thread(self._search_serpapi, query, limit)
        elif engine == "unsplash":
            return await asyncio.to_thread(self._search_unsplash, query, limit)
        elif engine == "flickr":
            return await asyncio.to_thread(self._search_flickr, query, limit)
        else:
            raise ValueError(f"Unsupported search engine: {engine}")

    def _search_serper(self, query: str, limit: int) -> list[str]:
        """Search images using Serper.dev API."""
        api_key = os.getenv('SERPER_API_KEY')
        if not api_key:
            self.logger.warning("SERPER_API_KEY not found, skipping Serper search")
            return []

        url = "https://google.serper.dev/images"
        headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}
        payload = {'q': query, 'num': min(limit, 100)}

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code != 200:
                return []
            data = response.json()
            images = data.get('images', [])
            urls = []
            for img in images:
                if 'imageUrl' in img:
                    urls.append(img['imageUrl'])
                elif 'link' in img:
                    urls.append(img['link'])
            return urls[:limit]
        except requests.exceptions.Timeout:
            self.logger.warning("Serper search timed out")
            return []
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Serper search error: {e}")
            return []

    def _search_serpapi(self, query: str, limit: int) -> list[str]:
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
                'safe': 'off',
            }

            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                images = data.get('images_results', [])
                return [img['original'] for img in images if 'original' in img][:limit]
        except requests.exceptions.Timeout:
            self.logger.warning("SerpAPI search timed out")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"SerpAPI search error: {e}")

        return []

    def _search_unsplash(self, query: str, limit: int) -> list[str]:
        """Search Unsplash for images."""
        access_key = os.getenv('UNSPLASH_ACCESS_KEY')
        if not access_key:
            self.logger.warning("UNSPLASH_ACCESS_KEY not found, skipping Unsplash search")
            return []

        try:
            url = "https://api.unsplash.com/search/photos"
            params = {'query': query, 'per_page': min(limit, 30), 'orientation': 'all'}
            headers = {'Authorization': f'Client-ID {access_key}'}

            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [photo['urls']['regular'] for photo in data.get('results', [])][:limit]
        except requests.exceptions.Timeout:
            self.logger.warning("Unsplash search timed out")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Unsplash search error: {e}")

        return []

    def _search_flickr(self, query: str, limit: int) -> list[str]:
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
                'media': 'photos',
            }

            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                photos = data.get('photos', {}).get('photo', [])
                urls = []
                for photo in photos:
                    farm = photo['farm']
                    server = photo['server']
                    photo_id = photo['id']
                    secret = photo['secret']
                    url = f"https://farm{farm}.staticflickr.com/{server}/{photo_id}_{secret}_b.jpg"
                    urls.append(url)
                return urls[:limit]
        except requests.exceptions.Timeout:
            self.logger.warning("Flickr search timed out")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Flickr search error: {e}")

        return []


# Convenience function for direct usage
async def search_images(query: str, engine: str = "serper", limit: int = 100) -> list[str]:
    """
    Convenience function for searching images with a unified interface.

    Args:
        query: Search query string
        engine: Search engine to use ("serper", "serpapi", "unsplash", "flickr")
        limit: Maximum number of URLs to return

    Returns:
        List of image URLs
    """
    search_engine = ImageSearchEngine()
    return await search_engine.search_images(query, engine, limit)


# Download function for testing
async def download_images(urls: list[str], output_dir: str = "test_downloads") -> dict[str, str]:
    """
    Download images from URLs for testing purposes.

    Args:
        urls: List of image URLs to download
        output_dir: Directory to save images

    Returns:
        Dictionary mapping URLs to local file paths
    """
    from pathlib import Path

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    results = {}
    logger = logging.getLogger(__name__)

    for i, url in enumerate(urls):
        try:
            response = await asyncio.to_thread(requests.get, url, timeout=30)
            if response.status_code == 200:
                content = response.content

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
                await asyncio.to_thread(filepath.write_bytes, content)

                results[url] = str(filepath)
                logger.info(f"Downloaded: {filename}")
            else:
                logger.warning(f"Failed to download {url}: HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")

    return results

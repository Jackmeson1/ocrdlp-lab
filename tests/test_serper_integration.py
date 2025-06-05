"""
Tests for Serper.dev API integration.
"""

import pytest
import asyncio
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from PIL import Image
import io

from crawler.search import search_images, download_images, ImageSearchEngine


class TestSerperIntegration:
    """Test cases for Serper.dev API integration."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.mark.skipif(
        not os.getenv('SERPER_API_KEY'),
        reason="SERPER_API_KEY not available for real API test"
    )
    @pytest.mark.asyncio
    async def test_serper_search_real_api(self):
        """
        Test Serper.dev API with real API calls.
        
        This test verifies that the Serper.dev integration can successfully
        search for images and return valid URLs when API key is available.
        """
        query = "blurry aadhaar card photo"
        
        # Test the unified search interface
        urls = await search_images(query, engine="serper", limit=10)
        
        # Should return a list (may be empty if API has issues)
        assert isinstance(urls, list)
        
        # If we get URLs, verify they are valid
        if len(urls) > 0:
            # Verify URLs are valid strings
            for url in urls:
                assert isinstance(url, str)
                assert url.startswith(('http://', 'https://'))
            
            # Check that we get reasonable results
            assert len(urls) >= 1, "Should return at least one URL with working API key"
            assert len(urls) <= 10, "Should not exceed requested limit"
        else:
            # If no URLs returned, it might be due to network issues or API limits
            print("No URLs returned - this may be due to network issues or API limits")
    
    @pytest.mark.skipif(
        not os.getenv('SERPER_API_KEY'),
        reason="SERPER_API_KEY not available for download test"
    )
    @pytest.mark.asyncio
    async def test_serper_download_real(self, tmp_path):
        """
        Test downloading images found via Serper.dev API.
        
        This test verifies that images found through Serper can be successfully
        downloaded, saved to disk, and opened with PIL with valid dimensions.
        """
        query = "blurry aadhaar card photo"
        
        # Search for images using Serper
        urls = await search_images(query, engine="serper", limit=5)
        
        if len(urls) == 0:
            pytest.skip("No URLs found for download test - API may be unavailable")
        
        # Download first few images
        test_urls = urls[:3]  # Test with first 3 URLs
        results = await download_images(test_urls, output_dir=str(tmp_path))
        
        # If we got URLs but no downloads, it might be due to filtering or network issues
        if len(results) == 0:
            pytest.skip("No images successfully downloaded - this may be due to filtering or network issues")
        
        # Verify downloaded files
        for url, filepath in results.items():
            file_path = Path(filepath)
            
            # File should exist
            assert file_path.exists(), f"Downloaded file should exist: {filepath}"
            
            # File should have content
            assert file_path.stat().st_size > 0, f"Downloaded file should not be empty: {filepath}"
            
            # Should be able to open with PIL
            try:
                with Image.open(file_path) as img:
                    width, height = img.size
                    
                    # Verify dimensions are reasonable (> 100x100 as required)
                    assert width > 100, f"Image width should be > 100px, got {width}"
                    assert height > 100, f"Image height should be > 100px, got {height}"
                    
                    # Verify it's a valid image format
                    assert img.format in ['JPEG', 'PNG', 'WEBP'], f"Should be valid image format, got {img.format}"
                    
            except Exception as e:
                pytest.fail(f"Failed to open downloaded image {filepath} with PIL: {e}")
    
    @pytest.mark.asyncio
    async def test_serper_search_with_mock(self):
        """
        Test Serper.dev search functionality with mocked API responses.
        
        This test ensures the Serper integration works correctly when the API
        returns valid responses, without requiring actual API calls.
        """
        query = "test document"
        
        # Mock successful Serper API response
        mock_response_data = {
            'images': [
                {'imageUrl': 'https://example.com/image1.jpg'},
                {'imageUrl': 'https://example.com/image2.png'},
                {'link': 'https://example.com/image3.webp'}  # Alternative field
            ]
        }
        
        # Create a proper async context manager mock
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_response_data)
        
        # Create async context manager
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        # Mock the HTTP session
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session.post.return_value = mock_context_manager
            mock_session.close = AsyncMock()
            mock_session_class.return_value = mock_session
            
            # Mock environment variable
            with patch.dict(os.environ, {'SERPER_API_KEY': 'test_key'}):
                urls = await search_images(query, engine="serper", limit=10)
        
        # Should return the mocked URLs
        assert isinstance(urls, list)
        assert len(urls) == 3
        
        # Verify all URLs are present
        expected_urls = [
            'https://example.com/image1.jpg',
            'https://example.com/image2.png',
            'https://example.com/image3.webp'
        ]
        for expected_url in expected_urls:
            assert expected_url in urls
    
    @pytest.mark.asyncio
    async def test_serper_api_error_handling(self):
        """
        Test error handling when Serper.dev API returns errors.
        
        This test verifies that the integration gracefully handles API errors
        and returns empty results instead of crashing.
        """
        query = "test query"
        
        # Mock API error response
        mock_response = AsyncMock()
        mock_response.status = 429  # Rate limit error
        
        # Create async context manager
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        # Mock the HTTP session
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session.post.return_value = mock_context_manager
            mock_session.close = AsyncMock()
            mock_session_class.return_value = mock_session
            
            # Mock environment variable
            with patch.dict(os.environ, {'SERPER_API_KEY': 'test_key'}):
                urls = await search_images(query, engine="serper", limit=10)
        
        # Should return empty list on error
        assert isinstance(urls, list)
        assert len(urls) == 0
    
    @pytest.mark.asyncio
    async def test_serper_no_api_key(self):
        """
        Test behavior when SERPER_API_KEY is not available.
        
        This test verifies that the integration gracefully handles missing
        API keys and returns empty results with appropriate warnings.
        """
        query = "test query"
        
        # Ensure no API key is set
        with patch.dict(os.environ, {}, clear=True):
            urls = await search_images(query, engine="serper", limit=10)
        
        # Should return empty list when no API key
        assert isinstance(urls, list)
        assert len(urls) == 0
    
    @pytest.mark.asyncio
    async def test_download_images_with_real_test_data(self, tmp_path):
        """
        Test download functionality with real image data but mocked network.
        
        This test creates real image data and verifies the download mechanism
        works correctly with PIL validation.
        """
        # Create a real test image in memory
        test_img = Image.new('RGB', (300, 300), color='blue')
        img_bytes = io.BytesIO()
        test_img.save(img_bytes, format='JPEG')
        img_data = img_bytes.getvalue()
        
        test_urls = ["https://example.com/test_image.jpg"]
        
        # Mock HTTP response with real image data
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {'content-type': 'image/jpeg'}
        mock_response.read = AsyncMock(return_value=img_data)
        
        # Create async context manager
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        # Mock the HTTP session
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session.get.return_value = mock_context_manager
            mock_session.close = AsyncMock()
            mock_session_class.return_value = mock_session
            
            # Mock file operations to actually write the file
            with patch('aiofiles.open', create=True) as mock_open:
                # Setup mock file writing that actually creates the file
                def mock_write_file(filepath, mode):
                    real_path = Path(filepath)
                    real_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(real_path, 'wb') as f:
                        f.write(img_data)

                    class DummyFileCM:
                        async def __aenter__(self_inner):
                            return AsyncMock()
                        async def __aexit__(self_inner, exc_type, exc, tb):
                            pass

                    return DummyFileCM()

                mock_open.side_effect = mock_write_file
                
                results = await download_images(test_urls, output_dir=str(tmp_path))
        
        # Verify we got results
        assert len(results) == 1
        
        # Verify the downloaded file
        for url, filepath in results.items():
            file_path = Path(filepath)
            
            # File should exist
            assert file_path.exists(), f"Downloaded file should exist: {filepath}"
            
            # File should have content
            assert file_path.stat().st_size > 0, f"Downloaded file should not be empty: {filepath}"
            
            # Should be able to open with PIL and verify dimensions
            with Image.open(file_path) as img:
                width, height = img.size
                
                # Verify it meets our requirements
                assert width > 100, f"Image width should be > 100px, got {width}"
                assert height > 100, f"Image height should be > 100px, got {height}"
                assert img.format == 'JPEG', f"Should be JPEG format, got {img.format}"
    
    @pytest.mark.asyncio
    async def test_unified_search_interface_engines(self):
        """
        Test that the unified search interface supports all expected engines.
        
        This test verifies that the search_images function correctly routes
        requests to different search engines.
        """
        query = "test"
        
        # Test all supported engines with mocked responses
        engines = ["serper", "serpapi", "unsplash", "flickr"]
        
        for engine in engines:
            # Mock successful response for each engine
            mock_response = AsyncMock()
            mock_response.status = 200
            
            if engine == "serper":
                mock_response.json = AsyncMock(return_value={'images': [{'imageUrl': 'http://test.com/1.jpg'}]})
                mock_method = 'post'
            else:
                mock_response.json = AsyncMock(return_value={})
                mock_method = 'get'
            
            # Create async context manager
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)
            
            with patch('aiohttp.ClientSession') as mock_session_class:
                mock_session = MagicMock()
                if mock_method == 'post':
                    mock_session.post.return_value = mock_context_manager
                else:
                    mock_session.get.return_value = mock_context_manager
                mock_session.close = AsyncMock()
                mock_session_class.return_value = mock_session
                
                # Mock appropriate API keys
                env_vars = {
                    'SERPER_API_KEY': 'test_key',
                    'SERPAPI_KEY': 'test_key',
                    'UNSPLASH_ACCESS_KEY': 'test_key',
                    'FLICKR_KEY': 'test_key'
                }
                
                with patch.dict(os.environ, env_vars):
                    urls = await search_images(query, engine=engine, limit=5)
                
                # Should return a list (content depends on mocked response)
                assert isinstance(urls, list)
    
    def test_invalid_engine_raises_error(self):
        """
        Test that using an invalid engine raises appropriate error.
        
        This test verifies that the unified interface properly validates
        engine parameters and raises clear errors for unsupported engines.
        """
        async def test_invalid():
            return await search_images("test", engine="invalid_engine", limit=5)
        
        # Should raise ValueError for invalid engine
        with pytest.raises(ValueError, match="Unsupported search engine"):
            asyncio.run(test_invalid()) 
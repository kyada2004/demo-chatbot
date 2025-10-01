import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.features.g4f_adapter import generate_text, generate_image

@pytest.mark.asyncio
@patch('app.features.g4f_adapter.client.chat.completions.create', new_callable=AsyncMock)
async def test_generate_text_retry(mock_create_async):
    """Test that generate_text retries on failure."""
    # Simulate failure then success
    async def async_generator():
        yield "Success"

    mock_create_async.side_effect = [Exception("API Error"), async_generator()]
    
    chunks = [chunk async for chunk in generate_text("test prompt", retries=2)]
    
    assert "Success" in chunks
    assert mock_create_async.call_count == 2

@pytest.mark.asyncio
@patch('app.features.g4f_adapter.client.images.generate', new_callable=AsyncMock)
async def test_generate_image_retry(mock_create_async):
    """Test that generate_image retries on failure."""
    # Simulate failure then success
    mock_response = MagicMock()
    mock_response.data = [MagicMock()]
    mock_response.data[0].url = "image_url"
    mock_create_async.side_effect = [Exception("API Error"), mock_response]
    
    result = await generate_image("test prompt", retries=2)
    
    assert result == "image_url"
    assert mock_create_async.call_count == 2

@pytest.mark.asyncio
@patch('app.features.g4f_adapter.client.chat.completions.create', new_callable=AsyncMock)
async def test_generate_text_failure(mock_create_async):
    """Test that generate_text returns an error message after all retries fail."""
    mock_create_async.side_effect = Exception("API Error")
    
    chunks = [chunk async for chunk in generate_text("test prompt", retries=2)]
    
    assert "Error: Unable to generate text after 2 retries." in chunks
    assert mock_create_async.call_count == 2

@pytest.mark.asyncio
@patch('app.features.g4f_adapter.client.images.generate', new_callable=AsyncMock)
async def test_generate_image_failure(mock_create_async):
    """Test that generate_image returns an error message after all retries fail."""
    mock_create_async.side_effect = Exception("API Error")
    
    result = await generate_image("test prompt", retries=2)
    
    assert result == "Error: Unable to generate image after 2 retries."
    assert mock_create_async.call_count == 2
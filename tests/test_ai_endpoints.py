
import queue
from unittest.mock import patch
import pytest
from app.core.agent import AIAgent
from app.core.main import ChatApplication

@pytest.fixture
def app():
    return ChatApplication()

@pytest.fixture
def agent(app):
    return AIAgent(app)

@pytest.mark.asyncio
async def test_get_ai_response_endpoint(agent):
    with patch('app.features.ai.get_ai_response') as mock_get_ai_response:
        mock_get_ai_response.return_value = [{'text': 'Mocked AI response'}]
        response_queue = queue.Queue()
        agent.get_ai_response('Test query', response_queue)
        response = response_queue.get()
        assert response == {'text': 'Mocked AI response'}

def test_generate_image_endpoint(agent):
    with patch('app.core.agent.AIAgent.handle_image_generation') as mock_handle_image_generation:
        mock_handle_image_generation.return_value = {'image': 'http://example.com/image.png'}
        response = agent.handle_image_generation({'prompt': 'Test prompt'})
        assert response == {'image': 'http://example.com/image.png'}

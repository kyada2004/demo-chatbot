from app.features.g4f_adapter import generate_text
from app.core.safety import is_content_safe
import asyncio

async def get_ai_response(query, message_history=None, brain_context=None, stream=False, rag_context=None):
    # Safety check
    is_safe, message = is_content_safe(query)
    if not is_safe:
        async def error_generator():
            yield {"text": message}
        return error_generator() if stream else {"text": message}

    # Default message history
    if message_history is None:
        message_history = []

    # Context string from RAG
    context_string = f"Context:\n{rag_context}\n\n---\n\n" if rag_context else ""

    # System message
    system_message = {"role": "system", "content": brain_context or "You are a helpful assistant."}
    if not message_history or message_history[0]['role'] != 'system':
        messages = [system_message] + message_history + [{"role": "user", "content": query}]
    else:
        if message_history[0]['content'] != system_message['content']:
            message_history[0] = system_message
        messages = message_history + [{"role": "user", "content": query}]
    
    prompt = context_string + "\n".join([f"{m['role']}: {m['content']}" for m in messages])

    # Streamed response generator
    async def _stream_response():
        try:
            async for chunk in generate_text(prompt):
                if hasattr(chunk, "choices") and chunk.choices:
                    yield chunk.choices[0].delta.content or ""
        except Exception as e:
            print(f"[AI Response Error] {e}")
            yield "Sorry, I encountered an error while generating the response."

    # Return either streamed or full response
    if stream:
        return _stream_response()
    else:
        try:
            response_chunks = [chunk.choices[0].delta.content or "" async for chunk in generate_text(prompt) if hasattr(chunk, "choices")]
            full_response = "".join(response_chunks)
            return {"text": full_response.strip() or "I am sorry, I cannot answer this question."}
        except Exception as e:
            print(f"[AI Response Error] {e}")
            return {"text": "Sorry, I encountered an error while generating the response."}

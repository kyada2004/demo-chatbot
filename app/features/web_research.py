import chromadb
from sentence_transformers import SentenceTransformer
from typing import List
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# -----------------------
# Setup ChromaDB
# -----------------------
client = chromadb.PersistentClient(path="web_vectors")
web_collection = client.get_or_create_collection(name="web_content")

# -----------------------
# Embedding model
# -----------------------
embedding_model = None

def get_embedding_model():
    global embedding_model
    if embedding_model is None:
        print("Loading embedding model...")
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Embedding model loaded.")
    return embedding_model

# -----------------------
# Scrape dynamic/static webpage and store
# -----------------------
def scrape_and_store_url(url: str) -> str:
    try:
        model = get_embedding_model()

        # Use Playwright to get fully rendered HTML
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=15000)
            html = page.content()
            browser.close()

        soup = BeautifulSoup(html, 'html.parser')

        # Extract all visible text from common and container elements
        page_text = ' '.join(s.strip() for s in soup.stripped_strings if s.strip())

        if not page_text:
            return f"No readable text found on {url}"

        # Chunking text (500 chars per chunk)
        chunks: List[str] = []
        chunk_size = 500
        text = page_text.strip()
        for i in range(0, len(text), chunk_size):
            chunks.append(text[i:i+chunk_size])

        # Generate embeddings
        embeddings = model.encode(chunks).tolist()

        # Store in ChromaDB
        for i, chunk in enumerate(chunks):
            web_collection.add(
                embeddings=[embeddings[i]],
                documents=[chunk],
                metadatas=[{"source": url, "chunk_index": i}],
                ids=[f"{url}_{i}"]
            )
        return f"Successfully scraped and stored content from {url}"

    except Exception as e:
        return f"Error processing URL {url}: {e}"

# -----------------------
# Query web content
# -----------------------
def query_web_content(query: str) -> str:
    try:
        model = get_embedding_model()
        query_embedding = model.encode([query])[0].tolist()

        results = web_collection.query(
            query_embeddings=[query_embedding],
            n_results=3
        )
        retrieved_chunks = results['documents'][0]

        if not retrieved_chunks:
            return "I couldn't find any relevant information in the scraped web content."

        # Friendly AI-style summary
        response = "Here’s what I found about your query:\n\n"
        for idx, chunk in enumerate(retrieved_chunks, start=1):
            response += f"{idx}. {chunk}\n\n"
        return response.strip()

    except Exception as e:
        return f"Error querying web content: {e}"

# -----------------------
# Demo
# -----------------------
if __name__ == "__main__":
    url_to_scrape = "https://kyada2004.github.io/portfolio/"
    print(scrape_and_store_url(url_to_scrape))

    query = "score of ai and ml?"
    print(query_web_content(query))

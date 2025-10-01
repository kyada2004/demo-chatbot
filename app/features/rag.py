import chromadb
from sentence_transformers import SentenceTransformer
import os

class RAG:
    def __init__(self, persist_directory="file_vectors"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.collection = self.client.get_or_create_collection(name="documents")

    def index_document(self, file_path):
        """Reads a document, splits it into chunks, and indexes the chunks."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return

        # Simple chunking by paragraph
        chunks = content.split('\n\n')
        
        # Filter out empty chunks
        chunks = [chunk for chunk in chunks if chunk.strip()]

        if not chunks:
            return

        # Generate embeddings
        embeddings = self.model.encode(chunks)

        # Create unique IDs for each chunk
        ids = [f"{file_path}_{i}" for i in range(len(chunks))]

        # Store in ChromaDB
        self.collection.add(
            embeddings=embeddings,
            documents=chunks,
            metadatas=[{"source": file_path} for _ in chunks],
            ids=ids
        )

    def retrieve_context(self, query, n_results=3):
        """Retrieves the most relevant document chunks for a given query."""
        query_embedding = self.model.encode([query])
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results
        )
        return results['documents'][0]

# Example usage (for testing)
if __name__ == '__main__':
    rag = RAG()
    # Create a dummy file for testing
    with open("test_document.txt", "w") as f:
        f.write("This is a test document about Gemini.\n\nGemini is a large language model from Google.")
    
    rag.index_document("test_document.txt")
    context = rag.retrieve_context("What is Gemini?")
    print(context)

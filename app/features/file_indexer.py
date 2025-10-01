import os
from app.features.rag import RAG
import argparse

def index_directory(directory):
    """Indexes all .txt files in a given directory."""
    rag = RAG()
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".txt"):
                file_path = os.path.join(root, file)
                print(f"Indexing {file_path}...")
                rag.index_document(file_path)
    print("Indexing complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index documents for RAG.")
    parser.add_argument("directory", type=str, help="The directory to index.")
    args = parser.parse_args()
    index_directory(args.directory)
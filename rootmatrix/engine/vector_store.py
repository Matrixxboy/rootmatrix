import os
import chromadb
from pathlib import Path
from typing import List, Dict, Any
import hashlib

from rootmatrix.engine.config import find_project_root, PROJECT_DIR_NAME
from chromadb.utils import embedding_functions

def get_db_path(file_path: str) -> Path:
    """Gets the path to the local vector DB for the given project."""
    root = find_project_root(file_path)
    if not root:
        # If not inside a project, we can create a temporary or global one,
        # but the prompt requires project-local control.
        # Let's fallback to global for safety if the user hasn't init'd yet.
        db_path = Path.home() / ".rootmatrix" / "global_vectordb"
    else:
        db_path = root / PROJECT_DIR_NAME / "vectordb"
        
    db_path.mkdir(parents=True, exist_ok=True)
    return db_path

def get_client(file_path: str) -> chromadb.ClientAPI:
    """Returns a persistent ChromaDB client for the project."""
    db_path = get_db_path(file_path)
    return chromadb.PersistentClient(path=str(db_path))

def _get_collection(client: chromadb.ClientAPI):
    """Gets or creates the 'codebase' collection."""
    # The default embedding function uses all-MiniLM-L6-v2 which is lightweight
    ef = embedding_functions.DefaultEmbeddingFunction()
    return client.get_or_create_collection(name="codebase", embedding_function=ef)

def upsert_files(file_path: str, files_data: List[Dict[str, Any]]):
    """
    Upserts a batch of files into the project's vector DB.
    files_data = [{"path": str, "content": str, "metadata": dict}]
    """
    client = get_client(file_path)
    collection = _get_collection(client)
    
    ids = []
    documents = []
    metadatas = []
    
    for item in files_data:
        path = item["path"]
        content = item["content"]
        meta = item.get("metadata", {})
        meta["path"] = path
        
        doc_id = hashlib.sha256(path.encode("utf-8")).hexdigest()
        
        ids.append(doc_id)
        documents.append(content)
        metadatas.append(meta)
        
    if ids:
        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

def delete_file(file_path: str, target_path: str):
    """
    Deletes a file from the vector DB.
    """
    client = get_client(file_path)
    collection = _get_collection(client)
    doc_id = hashlib.sha256(target_path.encode("utf-8")).hexdigest()
    try:
        collection.delete(ids=[doc_id])
    except Exception:
        pass

def search(file_path: str, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
    """
    Searches the vector DB for the given query.
    Returns a list of dictionaries with search results.
    """
    client = get_client(file_path)
    collection = _get_collection(client)
    
    # Check if collection is empty
    if collection.count() == 0:
        return []
        
    results = collection.query(
        query_texts=[query],
        n_results=min(n_results, collection.count())
    )
    
    formatted_results = []
    if results and results.get("ids") and results["ids"][0]:
        for i in range(len(results["ids"][0])):
            formatted_results.append({
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if results.get("distances") else None
            })
            
    return formatted_results

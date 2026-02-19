"""
RAG Knowledge Base using ChromaDB
Stores and retrieves regulatory documents
"""

import chromadb
from chromadb.utils import embedding_functions
import os

class RAGKnowledgeBase:
    def __init__(self, persist_directory="data/chromadb"):
        """Initialize ChromaDB for RAG"""
        
        # Persistent client (data saved between runs)
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Create or get collection
        try:
            self.collection = self.client.get_collection("sar_knowledge")
            print("✓ Loaded existing knowledge base")
        except:
            self.collection = self.client.create_collection(
                name="sar_knowledge",
                embedding_function=embedding_functions.DefaultEmbeddingFunction()
            )
            print("✓ Created new knowledge base")
            self._load_initial_documents()
    
    def _load_initial_documents(self):
        """Load all regulatory documents into ChromaDB"""
        
        documents = []
        ids = []
        metadatas = []
        
        # Load PMLA guidelines
        pmla_path = 'data/knowledge_base/pmla_guidelines.txt'
        if os.path.exists(pmla_path):
            with open(pmla_path, 'r', encoding='utf-8') as f:
                text = f.read()
                chunks = self._chunk_text(text, 500)
                
                for i, chunk in enumerate(chunks):
                    documents.append(chunk)
                    ids.append(f"pmla_{i}")
                    metadatas.append({
                        "source": "PMLA Guidelines",
                        "type": "regulation",
                        "section": f"chunk_{i}"
                    })
        
        # Load typologies
        typology_path = 'data/knowledge_base/money_laundering_typologies.txt'
        if os.path.exists(typology_path):
            with open(typology_path, 'r', encoding='utf-8') as f:
                text = f.read()
                chunks = self._chunk_text(text, 500)
                
                for i, chunk in enumerate(chunks):
                    documents.append(chunk)
                    ids.append(f"typology_{i}")
                    metadatas.append({
                        "source": "Typologies",
                        "type": "pattern",
                        "section": f"chunk_{i}"
                    })
        
        # Load SAR template
        template_path = 'data/sar_templates/base_template.txt'
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                documents.append(f.read())
                ids.append("sar_template")
                metadatas.append({
                    "source": "SAR Template",
                    "type": "format"
                })
        
        if documents:
            self.collection.add(
                documents=documents,
                ids=ids,
                metadatas=metadatas
            )
            print(f"✓ Loaded {len(documents)} document chunks into RAG")
    
    def _chunk_text(self, text, chunk_size=500):
        """Split text into chunks of ~chunk_size words"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i:i+chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks
    
    def retrieve(self, query, n_results=5):
        """Retrieve most relevant documents for query"""
        
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        return {
            'documents': results['documents'][0] if results['documents'] else [],
            'metadatas': results['metadatas'][0] if results['metadatas'] else [],
            'distances': results['distances'][0] if results['distances'] else []
        }
    
    def add_document(self, document, doc_id, metadata):
        """Add single document to knowledge base"""
        
        self.collection.add(
            documents=[document],
            ids=[doc_id],
            metadatas=[metadata]
        )
        print(f"✓ Added document: {doc_id}")


# Test
if __name__ == "__main__":
    kb = RAGKnowledgeBase()
    
    # Test retrieval
    results = kb.retrieve("What is Trade-Based Money Laundering?")
    
    print("\n📚 Retrieved documents:")
    for i, (doc, meta) in enumerate(zip(results['documents'], results['metadatas'])):
        print(f"\n{i+1}. Source: {meta['source']}")
        print(f"   {doc[:200]}...")
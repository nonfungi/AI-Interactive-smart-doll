# app/memory.py
import uuid
import datetime
from qdrant_client import QdrantClient, models
from langchain_openai import OpenAIEmbeddings

# Import the settings GETTER function, not the object itself
from .config import get_settings

class MemoryManager:
    # The client and embedding model are initialized here,
    # but only when an instance of MemoryManager is created.
    def __init__(self):
        settings = get_settings()
        print("Initializing Qdrant client...")
        self.client = QdrantClient(
            url=settings.qdrant_url, 
            api_key=settings.qdrant_api_key
        )
        self.embedding_model = OpenAIEmbeddings(openai_api_key=settings.openai_api_key)
        self.collection_name = "toy_conversations_v2"
        self.ensure_collection_exists()
        print("Qdrant client initialized successfully.")

    def ensure_collection_exists(self):
        # This logic remains the same
        collections_response = self.client.get_collections()
        existing_collections = [c.name for c in collections_response.collections]
        
        if self.collection_name not in existing_collections:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE)
            )
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="child_id",
                field_schema=models.PayloadSchemaType.KEYWORD,
                wait=True
            )
            print(f"Collection '{self.collection_name}' and payload index created.")

    async def search_memory(self, child_id: str, query_text: str) -> str:
        # This logic remains the same
        query_vector = self.embedding_model.embed_query(query_text)
        search_results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=models.Filter(
                must=[models.FieldCondition(key="child_id", match=models.MatchValue(value=child_id))]
            ),
            limit=3
        )
        memories = "\n".join([
            f"Child previously said: '{hit.payload['user_text']}' and AI responded: '{hit.payload['ai_text']}'"
            for hit in search_results
        ])
        return memories

    async def save_to_memory(self, child_id: str, user_text: str, ai_text: str):
        # This logic remains the same
        vector = self.embedding_model.embed_query(user_text)
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "child_id": child_id,
                        "user_text": user_text,
                        "ai_text": ai_text,
                        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
                    }
                )
            ]
        )

# We define a global variable for our manager, but initialize it as None.
# It will be populated during the application startup lifespan event.
memory_manager: MemoryManager | None = None

def initialize_memory_manager():
    """
    This function will be called ONLY during app startup within the lifespan event.
    """
    global memory_manager
    if memory_manager is None:
        memory_manager = MemoryManager()


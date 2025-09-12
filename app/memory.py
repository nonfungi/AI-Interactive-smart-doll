# app/memory.py
import uuid
import datetime
from qdrant_client import QdrantClient, models
from langchain_openai import OpenAIEmbeddings

# Import the settings function instead of the settings object
from .config import get_settings

# This will act as a global placeholder for our memory manager instance.
# It is initialized as None and will be populated during the app's startup.
memory_manager = None

def initialize_memory_manager():
    """
    Initializes the MemoryManager instance using the loaded settings.
    This function is called during the application startup lifespan event,
    ensuring that settings are fully loaded before a connection is attempted.
    """
    global memory_manager
    if memory_manager is None:
        print("Initializing MemoryManager and Qdrant client...")
        memory_manager = MemoryManager()
        print("MemoryManager initialized successfully.")

class MemoryManager:
    def __init__(self):
        # Get the fully loaded settings object
        settings = get_settings()
        
        # Initialize clients using the loaded settings
        self.client = QdrantClient(
            url=settings.qdrant_url, 
            api_key=settings.qdrant_api_key
        )
        self.embedding_model = OpenAIEmbeddings(openai_api_key=settings.openai_api_key)
        self.collection_name = "toy_conversations_v3" # Renamed to ensure a fresh start
        self.ensure_collection_exists()

    def ensure_collection_exists(self):
        """Checks if the Qdrant collection exists, and creates it if not."""
        try:
            collections_response = self.client.get_collections()
            existing_collections = [c.name for c in collections_response.collections]
            
            if self.collection_name not in existing_collections:
                print(f"Collection '{self.collection_name}' not found. Creating...")
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
        except Exception as e:
            print(f"Error checking or creating Qdrant collection: {e}")
            raise

    async def search_memory(self, child_id: str, query_text: str) -> str:
        """Searches for relevant memories for a specific child."""
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
            f"Child previously said: '{hit.payload.get('user_text', '')}' and AI responded: '{hit.payload.get('ai_text', '')}'"
            for hit in search_results
        ])
        return memories

    async def save_to_memory(self, child_id: str, user_text: str, ai_text: str):
        """Saves a new conversation turn to the child's memory."""
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
            ],
            wait=True
        )


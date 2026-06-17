from elasticsearch import Elasticsearch
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.core.config import settings
from app.db.models import MetadataCatalog
from app.db.session import SessionLocal
from app.services.local_embedding import LocalHashEmbedding
from app.services.metadata_document import from_model

COLLECTION_NAME = "metadata_catalog"
ELASTIC_INDEX_NAME = "metadata_catalog"
VECTOR_SIZE = 128


class MetadataIndexer:
    def __init__(self) -> None:
        self.embedding = LocalHashEmbedding(dimension=VECTOR_SIZE)
        self.qdrant = QdrantClient(url=settings.qdrant_url)
        self.elasticsearch = Elasticsearch(settings.elasticsearch_url)

    def rebuild(self) -> dict[str, int]:
        documents = self._load_documents()
        self._rebuild_qdrant(documents)
        self._rebuild_elasticsearch(documents)
        return {"indexed": len(documents)}

    def _load_documents(self):
        with SessionLocal() as session:
            rows = session.query(MetadataCatalog).order_by(MetadataCatalog.id).all()
            return [from_model(row) for row in rows]

    def _rebuild_qdrant(self, documents) -> None:
        self.qdrant.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        points = [
            PointStruct(
                id=document.id,
                vector=self.embedding.embed(document.text),
                payload=document.payload(),
            )
            for document in documents
        ]
        if points:
            self.qdrant.upsert(collection_name=COLLECTION_NAME, points=points)

    def _rebuild_elasticsearch(self, documents) -> None:
        if self.elasticsearch.indices.exists(index=ELASTIC_INDEX_NAME):
            self.elasticsearch.indices.delete(index=ELASTIC_INDEX_NAME)

        self.elasticsearch.indices.create(
            index=ELASTIC_INDEX_NAME,
            mappings={
                "properties": {
                    "object_type": {"type": "keyword"},
                    "object_name": {"type": "keyword"},
                    "parent_name": {"type": "keyword"},
                    "business_name": {"type": "text"},
                    "description": {"type": "text"},
                    "synonyms": {"type": "text"},
                    "example_values": {"type": "text"},
                    "text": {"type": "text"},
                }
            },
        )

        for document in documents:
            self.elasticsearch.index(
                index=ELASTIC_INDEX_NAME,
                id=document.id,
                document=document.payload(),
                refresh=False,
            )
        self.elasticsearch.indices.refresh(index=ELASTIC_INDEX_NAME)


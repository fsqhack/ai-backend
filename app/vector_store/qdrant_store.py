import uuid
from typing import Callable, Union, List, Dict, Any
import numpy as np
from qdrant_client import QdrantClient, models


class VectorEmbeddingStore:
    """
    Wrapper for Qdrant vector DB supporting dense (OpenAI) and sparse (SPLADE) embeddings.
    """

    def __init__(
        self,
        collection_name: str,
        embedder: Union[Callable[[str], Union[np.ndarray, Dict[int, float]]], str],
        host: str = "http://localhost:6333",
        api_key: str = None,
        distance_metric: str = "Cosine",
        retrieval_pipeline: List[Union[Callable, List[Any]]] = None,
        is_sparse: bool = False,
    ):
        self.collection_name = collection_name

        if isinstance(embedder, str):
            if embedder.lower() == "openai":
                from .models.openai_emb import OPENAI_EMBEDDER
                self.embedder = OPENAI_EMBEDDER
                # print("Using OpenAI embedder for dense embeddings.")
            elif embedder.lower() == "splade":
                from .models.splade_emb import SPLADE_EMBEDDER
                self.embedder = SPLADE_EMBEDDER
                # print("Using SPLADE embedder for sparse embeddings.")
            else:
                raise ValueError("Embedder must be 'openai' or 'splade' or a callable function.")
        elif callable(embedder):
            # print("Using custom embedder function.")
            self.embedder = embedder
        else:
            raise TypeError("Embedder must be a callable function or a string identifier.")
        
        self.is_sparse = is_sparse
        self.retrieval_pipeline = retrieval_pipeline or []
        self.client = QdrantClient(url=host, api_key=api_key)

        if not self.client.collection_exists(collection_name):
            sample_vector = self.embedder("sample")
            if isinstance(sample_vector, np.ndarray):
                # Dense vector store
                dim = sample_vector.shape[0]
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(size=dim, distance=models.Distance[distance_metric.upper()])
                )
            else:
                # Sparse vector store
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config={},  # Required even if unused
                    sparse_vectors_config={
                        "text": models.SparseVectorParams()
                    }
                )

    def _format_point(self, item: Dict[str, Any]) -> models.PointStruct:
        vector = self.embedder(item['text'])
        raw_id = item["id"]

        # Normalize ID
        if isinstance(raw_id, str):
            try:
                point_id = str(uuid.UUID(raw_id))
            except ValueError:
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, raw_id))
        elif isinstance(raw_id, int):
            point_id = raw_id
        else:
            raise ValueError("Point ID must be str or int")

        if isinstance(vector, dict):  # Sparse vector
            indices, values = zip(*vector.items()) if vector else ([], [])
            return models.PointStruct(
                id=point_id,
                vector={"text": models.SparseVector(indices=list(indices), values=list(values))},
                payload={"text": item["text"], "metadata": item.get("metadata", {})}
            )
        else:  # Dense vector
            return models.PointStruct(
                id=point_id,
                vector=vector.tolist() if isinstance(vector, np.ndarray) else vector,
                payload={"text": item["text"], "metadata": item.get("metadata", {})}
            )

    def insert(self, item: Dict[str, Any]):
        self.client.upsert(
            collection_name=self.collection_name,
            points=[self._format_point(item)]
        )

    def inserts(self, items: List[Dict[str, Any]]):
        points = [self._format_point(item) for item in items]
        self.client.upsert(collection_name=self.collection_name, points=points)

    def retrieve(self, query: str, top_k: int = None, retrieval_pipeline=None) -> List[Dict[str, Any]]:
        embedded_query = self.embedder(query)
        if top_k is None:
            # Total number of items in the collection
            top_k = self.client.count(
                collection_name=self.collection_name,
                exact=True
            ).count

        if isinstance(embedded_query, dict):
            indices, values = zip(*embedded_query.items()) if embedded_query else ([], [])
            result = self.client.query_points(
                collection_name=self.collection_name,
                query=models.SparseVector(indices=list(indices), values=list(values)),
                using="text",
                limit=top_k,
                with_payload=True
            ).points
        else:
            result = self.client.query_points(
                collection_name=self.collection_name,
                query=embedded_query.tolist() if isinstance(embedded_query, np.ndarray) else embedded_query,
                limit=top_k,
                with_payload=True
            ).points

        items = [{"id": r.id, "score": r.score, **(r.payload or {})} for r in result]

        for step in self.retrieval_pipeline if retrieval_pipeline is None else retrieval_pipeline:
            if callable(step):
                items = list(filter(step, items))
            elif isinstance(step, list) and step[0] == "search":
                items = items[:step[1]]

        return items

    def delete(self, condition: Callable[[Dict], bool]):
        all_points, _ = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=None,
            limit=10000
        )

        to_delete_ids = [
            point.id for point in all_points
            if condition({"id": point.id, **(point.payload or {})})
        ]

        if to_delete_ids:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(points=to_delete_ids)
            )

    def update(self, condition: Callable[[Dict], bool], update_func: Callable[[Dict], Dict]):
        all_points, _ = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=None,
            limit=10000
        )

        updated_points = []
        for point in all_points:
            full_data = {"id": point.id, **(point.payload or {})}
            if condition(full_data):
                new_data = update_func(full_data)
                updated_points.append(self._format_point(new_data))

        if updated_points:
            self.client.upsert(collection_name=self.collection_name, points=updated_points)

    def delete_collection(self):
        if self.client.collection_exists(self.collection_name):
            self.client.delete_collection(collection_name=self.collection_name)

    def reset_collection(self):
        self.delete_collection()
        sample_vector = self.embedder("sample")

        if isinstance(sample_vector, np.ndarray):
            dim = sample_vector.shape[0]
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE)
            )
        else:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={},
                sparse_vectors_config={
                    "text": models.SparseVectorParams()
                }
            )
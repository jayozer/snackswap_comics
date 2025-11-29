"""
Qdrant vector database service for SnackSwap Comics.
Manages connections to Qdrant and operations on collections.
"""

import logging
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from app.core.config import Settings

logger = logging.getLogger(__name__)


class QdrantService:
    """Service for interacting with Qdrant vector database."""

    # Collection names
    SNACKS_COLLECTION = "snacks_v1"
    FACTS_COLLECTION = "facts_v1"
    SWAPS_COLLECTION = "swaps_v1"
    STYLES_COLLECTION = "styles_v1"

    def __init__(self, settings: Settings):
        """Initialize Qdrant client."""
        self.settings = settings
        self.client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            timeout=30,
        )
        logger.info(f"Initialized Qdrant client at {settings.qdrant_url}")

    async def ensure_collections(self) -> None:
        """Ensure all required collections exist with proper indexes."""
        collections = [
            (self.SNACKS_COLLECTION, 768),  # Gemini embedding size
            (self.FACTS_COLLECTION, 768),
            (self.SWAPS_COLLECTION, 768),
            (self.STYLES_COLLECTION, 768),
        ]

        for collection_name, vector_size in collections:
            try:
                # Check if collection exists
                self.client.get_collection(collection_name)
                logger.info(f"Collection {collection_name} already exists")
            except (UnexpectedResponse, Exception):
                # Create collection if it doesn't exist
                logger.info(f"Creating collection {collection_name}")
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=vector_size,
                        distance=models.Distance.COSINE,
                    ),
                )

        # Ensure payload indexes exist for filtered fields (required by Qdrant Cloud)
        await self._ensure_payload_indexes()

    async def _ensure_payload_indexes(self) -> None:
        """
        Create payload indexes for fields used in filters.

        Qdrant Cloud requires explicit indexes for filtered queries.
        This creates indexes idempotently (skips if already exists).
        """
        # Define indexes needed for each collection
        indexes_config = {
            self.FACTS_COLLECTION: [
                ("clinic_approved", models.PayloadSchemaType.BOOL),
                ("age_band", models.PayloadSchemaType.KEYWORD),
            ],
            self.STYLES_COLLECTION: [
                ("is_default", models.PayloadSchemaType.BOOL),
            ],
            self.SWAPS_COLLECTION: [
                ("taste_cluster", models.PayloadSchemaType.KEYWORD),
                ("allergy_tags", models.PayloadSchemaType.KEYWORD),
            ],
            self.SNACKS_COLLECTION: [
                ("category", models.PayloadSchemaType.KEYWORD),
            ],
        }

        for collection_name, indexes in indexes_config.items():
            for field_name, field_type in indexes:
                try:
                    self.client.create_payload_index(
                        collection_name=collection_name,
                        field_name=field_name,
                        field_schema=field_type,
                    )
                    logger.info(f"Created index {field_name} on {collection_name}")
                except UnexpectedResponse as e:
                    # Index might already exist - that's fine
                    if "already exists" in str(e).lower():
                        logger.debug(f"Index {field_name} already exists on {collection_name}")
                    else:
                        logger.warning(f"Failed to create index {field_name} on {collection_name}: {e}")
                except Exception as e:
                    logger.warning(f"Failed to create index {field_name} on {collection_name}: {e}")

    def search_snacks(
        self,
        query_vector: list[float],
        limit: int = 8,
        filters: dict[str, Any] | None = None,
    ) -> list[models.ScoredPoint]:
        """
        Search for similar snacks in the snacks_v1 collection.

        Args:
            query_vector: Query embedding vector
            limit: Maximum number of results
            filters: Optional Qdrant filters

        Returns:
            List of scored points (snacks)
        """
        query_filter = None
        if filters:
            query_filter = self._build_filter(filters)

        results = self.client.search(
            collection_name=self.SNACKS_COLLECTION,
            query_vector=query_vector,
            limit=limit,
            query_filter=query_filter,
            with_payload=True,
        )

        return results

    def search_facts(
        self,
        query_vector: list[float],
        age_band: str,
        limit: int = 8,
        clinic_approved_only: bool = True,
    ) -> list[models.ScoredPoint]:
        """
        Search for relevant facts in the facts_v1 collection.

        Args:
            query_vector: Query embedding vector
            age_band: Target age band (3-5, 6-8, 9-12, all)
            limit: Maximum number of results
            clinic_approved_only: Only return clinic-approved facts

        Returns:
            List of scored points (facts)
        """
        filters = {}
        if clinic_approved_only:
            filters["clinic_approved"] = True

        # Age band filter (matches specific band or "all")
        query_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="clinic_approved",
                    match=models.MatchValue(value=True),
                ),
                models.Filter(
                    should=[
                        models.FieldCondition(
                            key="age_band",
                            match=models.MatchValue(value=age_band),
                        ),
                        models.FieldCondition(
                            key="age_band",
                            match=models.MatchValue(value="all"),
                        ),
                    ]
                ),
            ]
        )

        results = self.client.search(
            collection_name=self.FACTS_COLLECTION,
            query_vector=query_vector,
            limit=limit,
            query_filter=query_filter,
            with_payload=True,
        )

        return results

    def search_swaps(
        self,
        query_vector: list[float],
        taste_cluster: str | None = None,
        allergies: list[str] | None = None,
        age_band: str | None = None,
        limit: int = 8,
    ) -> list[models.ScoredPoint]:
        """
        Search for suitable swap alternatives in the swaps_v1 collection.

        Args:
            query_vector: Query embedding vector
            taste_cluster: Preferred taste cluster
            allergies: Allergens to exclude
            age_band: Age band for suitability check
            limit: Maximum number of results

        Returns:
            List of scored points (swaps)
        """
        must_conditions = []

        # Taste cluster filter
        if taste_cluster:
            must_conditions.append(
                models.FieldCondition(
                    key="taste_cluster",
                    match=models.MatchValue(value=taste_cluster),
                )
            )

        # Allergen exclusion
        if allergies:
            for allergen in allergies:
                must_conditions.append(
                    models.Filter(
                        must_not=[
                            models.FieldCondition(
                                key="allergy_tags",
                                match=models.MatchValue(value=allergen),
                            )
                        ]
                    )
                )

        query_filter = None
        if must_conditions:
            query_filter = models.Filter(must=must_conditions)

        results = self.client.search(
            collection_name=self.SWAPS_COLLECTION,
            query_vector=query_vector,
            limit=limit,
            query_filter=query_filter,
            with_payload=True,
        )

        return results

    def get_style(self, style_id: str) -> models.Record | None:
        """Get a specific style by ID."""
        try:
            results = self.client.retrieve(
                collection_name=self.STYLES_COLLECTION,
                ids=[style_id],
                with_payload=True,
            )
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Error retrieving style {style_id}: {e}")
            return None

    def get_default_style(self) -> models.Record | None:
        """Get the default style."""
        results = self.client.scroll(
            collection_name=self.STYLES_COLLECTION,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="is_default",
                        match=models.MatchValue(value=True),
                    )
                ]
            ),
            limit=1,
            with_payload=True,
        )

        records, _ = results
        return records[0] if records else None

    def _build_filter(self, filters: dict[str, Any]) -> models.Filter:
        """Build a Qdrant filter from a dictionary."""
        conditions = []
        for key, value in filters.items():
            conditions.append(
                models.FieldCondition(
                    key=key,
                    match=models.MatchValue(value=value),
                )
            )

        return models.Filter(must=conditions)

    def upsert_points(
        self,
        collection_name: str,
        points: list[models.PointStruct],
    ) -> None:
        """
        Upsert points into a collection.

        Args:
            collection_name: Name of the collection
            points: List of point structs to upsert
        """
        self.client.upsert(
            collection_name=collection_name,
            points=points,
        )
        logger.info(f"Upserted {len(points)} points to {collection_name}")

"""Scoring and retrieval endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, Depends

from app.core.config import get_settings, Settings
from app.models import ScoreRetrieveRequest, ScoreRetrieveResponse, ScoredItem, ComicMode
from app.services.gemini_service import GeminiService
from app.services.qdrant_service import QdrantService
from app.services.scoring_service import ScoringService
from app.services.query_builder import QueryBuilder

logger = logging.getLogger(__name__)

router = APIRouter()

# Threshold for mode determination
CELEBRATE_THRESHOLD = 30.0  # Risk < 30 = CELEBRATE, Risk >= 30 = EDUCATE


def get_gemini_service(settings: Annotated[Settings, Depends(get_settings)]) -> GeminiService:
    """Dependency for Gemini service."""
    return GeminiService(settings)


def get_qdrant_service(settings: Annotated[Settings, Depends(get_settings)]) -> QdrantService:
    """Dependency for Qdrant service."""
    return QdrantService(settings)


def get_scoring_service() -> ScoringService:
    """Dependency for scoring service."""
    return ScoringService()


def determine_mode(scored_items: list[ScoredItem], matched_snacks: list[dict]) -> ComicMode:
    """
    Determine comic mode based on risk scores and snack properties.

    Args:
        scored_items: List of scored items with risk scores
        matched_snacks: List of matched snack payloads

    Returns:
        ComicMode (CELEBRATE, EDUCATE, or UNKNOWN)
    """
    if not scored_items:
        return ComicMode.UNKNOWN

    # Check if any snack is explicitly healthy
    for snack in matched_snacks:
        if snack.get("is_healthy", False):
            return ComicMode.CELEBRATE

    # Calculate average risk score
    avg_risk = sum(item.dental_risk_score for item in scored_items) / len(scored_items)

    if avg_risk < CELEBRATE_THRESHOLD:
        return ComicMode.CELEBRATE
    else:
        return ComicMode.EDUCATE


@router.post("/retrieve", response_model=ScoreRetrieveResponse)
async def score_retrieve(
    request: ScoreRetrieveRequest,
    gemini_service: GeminiService = Depends(get_gemini_service),
    qdrant_service: QdrantService = Depends(get_qdrant_service),
    scoring_service: ScoringService = Depends(get_scoring_service),
) -> ScoreRetrieveResponse:
    """
    Score detected items and retrieve relevant facts and swaps.

    Steps:
    1. For each detected item, search Qdrant for matching snacks
    2. Calculate dental risk scores
    3. Determine comic mode (CELEBRATE/EDUCATE/UNKNOWN)
    4. Retrieve mode-appropriate facts with risk_tags filtering
    5. Find taste-aligned swaps (only for EDUCATE mode)

    Args:
        request: Score retrieval request with items, age, allergies
        gemini_service: Gemini service for embeddings
        qdrant_service: Qdrant service for vector search
        scoring_service: Scoring service for risk calculation

    Returns:
        Scored items with facts, swaps, mode, and average risk score
    """
    try:
        age_band = scoring_service.get_age_band(request.age)
        scored_items = []
        matched_snacks = []
        all_facts = []
        all_swaps = []
        all_risk_tags = set()

        # Process each detected item
        for item in request.items:
            # Generate query embedding using QueryBuilder
            query_text = QueryBuilder.build_snack_query(
                detected_name=item.name,
                brand_guess=item.brand_guess,
                category=item.category,
            )
            query_embedding = await gemini_service.generate_query_embedding(query_text)

            # Search for matching snacks
            snack_results = await qdrant_service.search_snacks(query_embedding, limit=3)

            if not snack_results:
                logger.warning(f"No matching snacks found for: {item.name}")
                continue

            # Match item to best snack
            matched_snack = scoring_service.match_snack_to_payload(item, snack_results)

            if not matched_snack:
                continue

            matched_snacks.append(matched_snack)

            # Calculate dental risk
            risk_score = scoring_service.calculate_dental_risk(matched_snack)

            # Extract risk tags for cross-collection filtering
            risk_tags = scoring_service.extract_risk_tags(matched_snack)
            all_risk_tags.update(risk_tags)

            scored_items.append(
                ScoredItem(
                    snack_id=matched_snack["snack_id"],
                    name=matched_snack["name"],
                    category=matched_snack["category"],
                    dental_risk_score=risk_score,
                    confidence=matched_snack["match_confidence"],
                )
            )

        # Determine mode based on scores and snack properties
        mode = determine_mode(scored_items, matched_snacks)

        # Calculate average risk score
        avg_risk = 0.0
        if scored_items:
            avg_risk = sum(item.dental_risk_score for item in scored_items) / len(scored_items)

        logger.info(f"Mode determined: {mode.value}, avg_risk: {avg_risk:.1f}")

        # Get facts based on mode
        if mode == ComicMode.CELEBRATE:
            # For celebrate mode, get celebration facts
            for matched_snack in matched_snacks:
                fact_query = QueryBuilder.build_celebrate_query(
                    snack_category=matched_snack["category"],
                    health_benefits=matched_snack.get("health_benefits", []),
                )
                fact_embedding = await gemini_service.generate_query_embedding(fact_query)

                fact_results = await qdrant_service.search_facts(
                    fact_embedding,
                    age_band=age_band,
                    limit=4,
                    fact_type="celebrate",  # Only celebration facts
                )

                for fact in fact_results:
                    fact_data = dict(fact.payload)
                    fact_data["score"] = fact.score
                    all_facts.append(fact_data)

        elif mode == ComicMode.EDUCATE:
            # For educate mode, get targeted educational facts
            for matched_snack in matched_snacks:
                snack_traits = scoring_service.extract_risk_tags(matched_snack)

                fact_query = QueryBuilder.build_fact_query(
                    snack_category=matched_snack["category"],
                    snack_traits=snack_traits,
                )
                fact_embedding = await gemini_service.generate_query_embedding(fact_query)

                # Use risk_tags for cross-collection filtering
                fact_results = await qdrant_service.search_facts(
                    fact_embedding,
                    age_band=age_band,
                    limit=4,
                    fact_type="educate",
                    risk_tags=snack_traits if snack_traits else None,
                )

                for fact in fact_results:
                    fact_data = dict(fact.payload)
                    fact_data["score"] = fact.score
                    all_facts.append(fact_data)

                # Find swaps (only for EDUCATE mode)
                taste_cluster = matched_snack.get("taste_cluster", "neutral")
                swap_query = f"{taste_cluster}, healthy alternative, {matched_snack['category']}"
                swap_embedding = await gemini_service.generate_query_embedding(swap_query)

                swap_results = await qdrant_service.search_swaps(
                    swap_embedding,
                    taste_cluster=taste_cluster,
                    allergies=request.allergies,
                    age_band=age_band,
                    limit=8,
                )

                # Convert to dicts and rank
                swap_candidates = [dict(swap.payload) for swap in swap_results]
                ranked_swaps = scoring_service.rank_swaps(
                    matched_snack,
                    swap_candidates,
                    age_band,
                    request.allergies,
                )

                all_swaps.extend(ranked_swaps[:3])  # Top 3 per item

        else:
            # UNKNOWN mode - get generic educational facts
            generic_query = "dental health, brushing, healthy teeth"
            fact_embedding = await gemini_service.generate_query_embedding(generic_query)

            fact_results = await qdrant_service.search_facts(
                fact_embedding,
                age_band=age_band,
                limit=4,
            )

            for fact in fact_results:
                fact_data = dict(fact.payload)
                fact_data["score"] = fact.score
                all_facts.append(fact_data)

        # Deduplicate facts and swaps by ID
        unique_facts = {f["fact_id"]: f for f in all_facts}.values()
        unique_swaps = {s["swap_id"]: s for s in all_swaps}.values()

        logger.info(
            f"Retrieved {len(scored_items)} items, "
            f"{len(unique_facts)} facts, "
            f"{len(unique_swaps)} swaps, "
            f"mode={mode.value}"
        )

        return ScoreRetrieveResponse(
            scored_items=scored_items,
            facts=list(unique_facts),
            swaps=list(unique_swaps),
            mode=mode,
            average_risk_score=round(avg_risk, 2),
        )

    except Exception as e:
        logger.error(f"Error in score_retrieve: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve data: {str(e)}")

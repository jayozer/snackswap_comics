"""
Seed data for SnackSwap Comics.
Populates Qdrant collections with sample snacks, facts, swaps, and styles.
"""

import asyncio
import sys
import uuid
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

import google.generativeai as genai
from qdrant_client.http import models

from app.core.config import get_settings
from app.services.qdrant_service import QdrantService


async def generate_embedding(text: str, api_key: str) -> list[float]:
    """Generate embedding for text."""
    genai.configure(api_key=api_key)
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=text,
        task_type="retrieval_document",
    )
    return result["embedding"]


async def seed_snacks(qdrant_service: QdrantService, api_key: str):
    """Seed sample snacks."""
    print("Seeding snacks...")

    snacks = [
        {
            "snack_id": "chips_classic",
            "name": "Classic Potato Chips",
            "brand": "Generic",
            "category": "chips",
            "flavor_notes": ["salty", "crunchy", "savory"],
            "sugar_g_per_100g": 1.5,
            "added_sugar_g": 0.5,
            "acidity_tag": "low",
            "stickiness": 0.1,
            "residue": 0.3,
            "crunch_hardness": 0.6,
            "water_content": 0.02,
            "typical_portion_g": 30,
            "age_flags": {},
            "allergy_tags": [],
            "taste_cluster": "savory-crunch",
            "images": [],
        },
        {
            "snack_id": "candy_gummy",
            "name": "Gummy Bears",
            "brand": "Generic",
            "category": "candy",
            "flavor_notes": ["sweet", "fruity", "chewy"],
            "sugar_g_per_100g": 46.0,
            "added_sugar_g": 46.0,
            "acidity_tag": "medium",
            "stickiness": 0.8,
            "residue": 0.7,
            "crunch_hardness": 0.0,
            "water_content": 0.15,
            "typical_portion_g": 40,
            "age_flags": {},
            "allergy_tags": ["gelatin"],
            "taste_cluster": "sweet-chewy",
            "images": [],
        },
        {
            "snack_id": "cookie_chocolate",
            "name": "Chocolate Chip Cookies",
            "brand": "Generic",
            "category": "cookie",
            "flavor_notes": ["sweet", "chocolatey", "buttery"],
            "sugar_g_per_100g": 35.0,
            "added_sugar_g": 30.0,
            "acidity_tag": "low",
            "stickiness": 0.4,
            "residue": 0.5,
            "crunch_hardness": 0.3,
            "water_content": 0.05,
            "typical_portion_g": 50,
            "age_flags": {},
            "allergy_tags": ["gluten", "dairy"],
            "taste_cluster": "sweet-baked",
            "images": [],
        },
        {
            "snack_id": "soda_cola",
            "name": "Cola Soda",
            "brand": "Generic",
            "category": "beverage",
            "flavor_notes": ["sweet", "fizzy", "caramel"],
            "sugar_g_per_100g": 10.6,
            "added_sugar_g": 10.6,
            "acidity_tag": "high",
            "stickiness": 0.2,
            "residue": 0.4,
            "crunch_hardness": 0.0,
            "water_content": 0.89,
            "typical_portion_g": 355,
            "age_flags": {},
            "allergy_tags": [],
            "taste_cluster": "sweet-fizzy",
            "images": [],
        },
    ]

    points = []
    for snack in snacks:
        # Generate embedding
        embedding_text = (
            f"brand={snack['brand']}, type={snack['category']}, "
            f"name={snack['name']}, flavors={', '.join(snack['flavor_notes'])}"
        )
        embedding = await generate_embedding(embedding_text, api_key)

        points.append(
            models.PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_DNS, snack["snack_id"])),
                vector=embedding,
                payload=snack,
            )
        )

    qdrant_service.upsert_points(QdrantService.SNACKS_COLLECTION, points)
    print(f"Seeded {len(points)} snacks")


async def seed_facts(qdrant_service: QdrantService, api_key: str):
    """Seed sample facts."""
    print("Seeding facts...")

    facts = [
        {
            "fact_id": "F001",
            "text": "Sugar feeds bacteria in your mouth that make acid, which can hurt your tooth enamel.",
            "topic": ["sugar", "bacteria"],
            "age_band": "6-8",
            "source_key": "ClinicKB#SugarBacteria",
            "source_url": "https://example.com/dental-facts",
            "reviewed_by": "Dr. Smith",
            "clinic_approved": True,
        },
        {
            "fact_id": "F002",
            "text": "Sticky foods like gummy candies stay on your teeth longer, giving bacteria more time to make acid.",
            "topic": ["stickiness", "sugar"],
            "age_band": "6-8",
            "source_key": "ClinicKB#StickyFoods",
            "source_url": "https://example.com/dental-facts",
            "reviewed_by": "Dr. Smith",
            "clinic_approved": True,
        },
        {
            "fact_id": "F003",
            "text": "Brushing your teeth after eating sweets helps wash away the sugar before it can cause problems.",
            "topic": ["timing", "brushing"],
            "age_band": "all",
            "source_key": "ClinicKB#Timing",
            "source_url": "https://example.com/dental-facts",
            "reviewed_by": "Dr. Smith",
            "clinic_approved": True,
        },
        {
            "fact_id": "F004",
            "text": "Acidic drinks can soften your tooth enamel, making it easier to get cavities.",
            "topic": ["acidity", "enamel"],
            "age_band": "9-12",
            "source_key": "ClinicKB#Acidity",
            "source_url": "https://example.com/dental-facts",
            "reviewed_by": "Dr. Smith",
            "clinic_approved": True,
        },
        {
            "fact_id": "F005",
            "text": "Eating snacks with less sugar and drinking water helps keep your teeth strong and healthy!",
            "topic": ["sugar", "water"],
            "age_band": "3-5",
            "source_key": "ClinicKB#HealthyChoices",
            "source_url": "https://example.com/dental-facts",
            "reviewed_by": "Dr. Smith",
            "clinic_approved": True,
        },
    ]

    points = []
    for fact in facts:
        embedding = await generate_embedding(fact["text"], api_key)

        points.append(
            models.PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_DNS, fact["fact_id"])),
                vector=embedding,
                payload=fact,
            )
        )

    qdrant_service.upsert_points(QdrantService.FACTS_COLLECTION, points)
    print(f"Seeded {len(points)} facts")


async def seed_swaps(qdrant_service: QdrantService, api_key: str):
    """Seed sample swaps."""
    print("Seeding swaps...")

    swaps = [
        {
            "swap_id": "swap_popcorn",
            "name": "Air-popped popcorn with light salt",
            "category": "snack",
            "flavor_notes": ["savory", "crunchy", "light"],
            "sugar_g_per_100g": 0.0,
            "added_sugar_g": 0.0,
            "acidity_tag": "low",
            "stickiness": 0.0,
            "residue": 0.1,
            "water_content": 0.04,
            "allergy_tags": [],
            "taste_cluster": "savory-crunch",
            "prep_time": "<5min",
            "suitability": {"3-5": True, "6-8": True, "9-12": True},
            "example_brands": ["Orville", "SkinnyPop"],
            "popularity_score": 0.8,
        },
        {
            "swap_id": "swap_yogurt_berries",
            "name": "Plain yogurt with fresh berries",
            "category": "dairy",
            "flavor_notes": ["creamy", "tangy", "sweet-tart"],
            "sugar_g_per_100g": 5.0,
            "added_sugar_g": 0.0,
            "acidity_tag": "medium",
            "stickiness": 0.2,
            "residue": 0.2,
            "water_content": 0.85,
            "allergy_tags": ["dairy"],
            "taste_cluster": "sweet-creamy",
            "prep_time": "0",
            "suitability": {"3-5": True, "6-8": True, "9-12": True},
            "example_brands": ["Chobani", "Fage"],
            "popularity_score": 0.9,
        },
        {
            "swap_id": "swap_cheese_crackers",
            "name": "Whole grain crackers with cheese slices",
            "category": "snack",
            "flavor_notes": ["savory", "cheesy", "wholesome"],
            "sugar_g_per_100g": 2.0,
            "added_sugar_g": 0.5,
            "acidity_tag": "low",
            "stickiness": 0.1,
            "residue": 0.3,
            "water_content": 0.05,
            "allergy_tags": ["gluten", "dairy"],
            "taste_cluster": "savory-crunch",
            "prep_time": "0",
            "suitability": {"3-5": True, "6-8": True, "9-12": True},
            "example_brands": ["Triscuit", "Wheat Thins"],
            "popularity_score": 0.85,
        },
        {
            "swap_id": "swap_water_fruit",
            "name": "Water with sliced fruit",
            "category": "beverage",
            "flavor_notes": ["fresh", "light", "fruity"],
            "sugar_g_per_100g": 1.0,
            "added_sugar_g": 0.0,
            "acidity_tag": "low",
            "stickiness": 0.0,
            "residue": 0.0,
            "water_content": 0.99,
            "allergy_tags": [],
            "taste_cluster": "fresh-light",
            "prep_time": "<5min",
            "suitability": {"3-5": True, "6-8": True, "9-12": True},
            "example_brands": [],
            "popularity_score": 0.7,
        },
    ]

    points = []
    for swap in swaps:
        embedding_text = f"{swap['name']}, {', '.join(swap['flavor_notes'])}, {swap['taste_cluster']}"
        embedding = await generate_embedding(embedding_text, api_key)

        points.append(
            models.PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_DNS, swap["swap_id"])),
                vector=embedding,
                payload=swap,
            )
        )

    qdrant_service.upsert_points(QdrantService.SWAPS_COLLECTION, points)
    print(f"Seeded {len(points)} swaps")


async def seed_styles(qdrant_service: QdrantService, api_key: str):
    """Seed sample styles."""
    print("Seeding styles...")

    styles = [
        {
            "style_id": "default",
            "name": "SnackSwap Default",
            "palette": {
                "primary": "#4A90E2",
                "secondary": "#50C878",
                "background": "#FFFFFF",
                "text": "#333333",
                "accent": "#FFB347",
            },
            "fonts": {
                "title": "Comic Sans MS",
                "dialogue": "Arial",
                "caption": "Helvetica",
            },
            "bubble_style": "rounded",
            "frame_style": "clean",
            "logo_uri": None,
            "mascot_uri": None,
            "watermark_uri": None,
            "panel_layout": "2x2",
            "min_font_size_pt": 15,
            "safe_margin_px": 64,
            "created_by": "system",
            "is_default": True,
        }
    ]

    points = []
    for style in styles:
        embedding_text = f"{style['name']}, {style['bubble_style']}, {style['frame_style']}"
        embedding = await generate_embedding(embedding_text, api_key)

        points.append(
            models.PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_DNS, style["style_id"])),
                vector=embedding,
                payload=style,
            )
        )

    qdrant_service.upsert_points(QdrantService.STYLES_COLLECTION, points)
    print(f"Seeded {len(points)} styles")


async def main():
    """Main seeding function."""
    print("Starting SnackSwap Comics data seeding...\n")

    settings = get_settings()
    qdrant_service = QdrantService(settings)

    # Ensure collections exist
    await qdrant_service.ensure_collections()

    # Seed data
    await seed_snacks(qdrant_service, settings.gemini_api_key)
    await seed_facts(qdrant_service, settings.gemini_api_key)
    await seed_swaps(qdrant_service, settings.gemini_api_key)
    await seed_styles(qdrant_service, settings.gemini_api_key)

    print("\nSeeding complete!")


if __name__ == "__main__":
    asyncio.run(main())

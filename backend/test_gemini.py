#!/usr/bin/env python3
"""
Quick test to verify Gemini API is working correctly.
Tests both google-generativeai and google-genai packages.
"""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("❌ ERROR: GEMINI_API_KEY not found in .env file")
    sys.exit(1)

print(f"✓ API Key found: {GEMINI_API_KEY[:10]}...")
print()

# Test 1: google-generativeai (for vision and text)
print("=" * 60)
print("TEST 1: google-generativeai package (vision/text)")
print("=" * 60)

try:
    import google.generativeai as genai

    genai.configure(api_key=GEMINI_API_KEY)

    # Test text generation
    model = genai.GenerativeModel("gemini-2.0-flash-exp")
    response = model.generate_content("Say 'Hello from Gemini!' in exactly those words.")

    print(f"✓ Text generation works!")
    print(f"  Response: {response.text[:100]}")
    print()

    # Test embedding
    result = genai.embed_content(
        model="models/text-embedding-004",
        content="test embedding",
        task_type="retrieval_query",
    )

    embedding_length = len(result["embedding"])
    print(f"✓ Embedding generation works!")
    print(f"  Embedding dimension: {embedding_length}")
    print()

except Exception as e:
    print(f"❌ google-generativeai test FAILED: {e}")
    sys.exit(1)

# Test 2: google-genai (for Nano-Banana image generation)
print("=" * 60)
print("TEST 2: google-genai package (Nano-Banana image gen)")
print("=" * 60)

try:
    from google import genai as genai_new
    from google.genai import types

    client = genai_new.Client(api_key=GEMINI_API_KEY)

    # Test simple text generation with new SDK
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="Say 'Hello from new SDK!' in exactly those words."),
            ],
        ),
    ]

    response_received = False
    for chunk in client.models.generate_content_stream(
        model="gemini-2.0-flash-exp",
        contents=contents,
    ):
        if (
            chunk.candidates
            and chunk.candidates[0].content
            and chunk.candidates[0].content.parts
        ):
            part = chunk.candidates[0].content.parts[0]
            if part.text:
                print(f"✓ New SDK text generation works!")
                print(f"  Response: {part.text[:100]}")
                response_received = True
                break

    if not response_received:
        raise Exception("No response received from new SDK")

    print()
    print("✓ Nano-Banana SDK ready (image generation not tested - requires longer prompt)")
    print()

except Exception as e:
    print(f"❌ google-genai test FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Success!
print("=" * 60)
print("🎉 ALL TESTS PASSED!")
print("=" * 60)
print()
print("Both Gemini packages are working correctly:")
print("  ✓ google-generativeai (vision, text, embeddings)")
print("  ✓ google-genai (Nano-Banana image generation)")
print()
print("Your API key is valid and the models are accessible.")

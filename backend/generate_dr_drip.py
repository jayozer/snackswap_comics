
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from rembg import remove
from PIL import Image
import io

# Add backend to path to import app modules
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import Settings
from app.services.nanobana_service import NanoBananaService

async def main():
    load_dotenv()
    
    settings = Settings()
    if not settings.gemini_api_key:
        print("Error: GEMINI_API_KEY not found")
        return

    service = NanoBananaService(settings)
    
    # 1. REVERTED TO PREVIOUS STYLE (User preferred this)
    # But adding fixes for Hands, Cutoff, and continuity.
    base_description = (
        "A hype-beast molar tooth character named 'Dr. Drip'. "
        "IMPORTANT: The TOP PART of the tooth is SOLID SHINY GOLD (A Gold Dental Crown / Gold Cap). "
        "It looks like a Gold Tooth. "
        "He wears cool black sunglasses and fresh high-top sneakers. "
        "Style: Modern 2D vector art, clean lines, vibrant colors, edgy sticker art style. "
        "White body, GOLD TOP (Dental Crown), black shades. "
        "NO TEXT. NO WORDS. SINGLE CHARACTER ONLY. "
        "framing: FULL BODY SHOT, ZOOM OUT slightly to ensure feet and crown are fully visible. Wide margins."
    )
    
    variations = [
        {
            "name": "dr_drip_hero",
            "expression": "confident, cool, smirking, standing with swag",
            "detail": "Standing confidently. Gold tooth cap is shiny. Arms crossed or at sides."
        },
        {
            "name": "dr_drip_scanning",
            "expression": "intense focus, looking over sunglasses",
            "detail": "Action: Moving glasses down with ONE HAND to peek over them. The other hand is down. STRICTLY TWO HANDS TOTAL. No extra floating hands."
        },
        {
            "name": "dr_drip_success",
            "expression": "celebrating, triumphant, holding up a 'W' sign or thumbs up",
            "detail": "Huge success. Energetic pose. Jump or cheer. ZOOM OUT to keep hands and feet in frame. Gold top shining."
        }
    ]
    
    output_dir = Path("../frontend/public/images")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for var in variations:
        filename = f"{var['name']}.png"
        raw_path = output_dir / f"{var['name']}_raw.png"
        final_path = output_dir / filename
        
        full_desc = f"{base_description} ACTION: {var['detail']} EXPRESSION: {var['expression']}"
        
        print(f"Generating {filename}...")
        
        try:
            # Generate Image (Raw)
            await service.generate_character_image(
                character_name="Dr. Drip",
                character_description=full_desc,
                expression=var["expression"],
                output_path=raw_path,
                image_size="1024x1024" 
            )
            print(f"  ✓ Generated raw image")

            # Remove Background
            print(f"  Processing background removal...")
            with open(raw_path, 'rb') as i:
                input_data = i.read()
                subject = remove(input_data)
                
                # Verify image is not empty
                if not subject:
                     print(f"  ❌ Error: Background removal failed (empty result)")
                     continue
                
                # Save final transparent image
                with open(final_path, 'wb') as o:
                    o.write(subject)
            
            print(f"  ✓ Saved transparent image to {final_path}")
            
            # Clean up raw file
            # raw_path.unlink() 

        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")

if __name__ == "__main__":
    asyncio.run(main())

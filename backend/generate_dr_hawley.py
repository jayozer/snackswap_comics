
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
    
    # Dr. Hawley character description based on image_25.png reference
    base_description = (
        "An anthropomorphic molar tooth character named 'Dr. Hawley'. "
        "Off-white/pale cyan body with smooth rounded shape. "
        "Large round eyes with small black pupils, simple black eyebrows, wide open smiling mouth. "
        "Black retro sunglasses pushed up onto forehead. "
        "Wears an oversized dark forest green pullover hoodie with front kangaroo pocket and drawstrings. "
        "Chunky beige slip-on slides (Yeezy style) on feet. "
        "Style: Clean 2D digital illustration in modern cartoon style. Bold uniform black outlines. "
        "Flat coloring with minimal hard-edged cel-shading. "
        "NO TEXT. NO WORDS. SINGLE CHARACTER ONLY. "
        "framing: FULL BODY SHOT, ZOOM OUT slightly to ensure feet and hoodie are fully visible. Wide margins. White background."
    )
    
    variations = [
        {
            "name": "dr_hawley_hero",
            "expression": "confident, cool, smirking, standing with swag",
            "detail": "Standing confidently. Clean white shine. Arms crossed or at sides. Hoodie looks fresh."
        },
        {
            "name": "dr_hawley_scanning",
            "expression": "intense focus, pulling shades down from forehead",
            "detail": "Action: Pulling shades down from forehead with ONE HAND to peek. The other hand is down. STRICTLY TWO HANDS TOTAL. No extra floating hands."
        },
        {
            "name": "dr_hawley_success",
            "expression": "celebrating, triumphant, holding up a 'W' sign or thumbs up",
            "detail": "Huge success. Energetic pose. Jump or cheer. ZOOM OUT to keep hands and feet in frame. Hoodie and slides visible."
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
                character_name="Dr. Hawley",
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

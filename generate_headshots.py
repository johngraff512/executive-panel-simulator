#!/usr/bin/env python3
"""
Generate AI headshots for executive panel members using DALL-E 3
Run this script once to generate all executive headshots
"""

import os
import requests
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
api_key = os.environ.get('OPENAI_API_KEY')
if not api_key:
    print("❌ Error: OPENAI_API_KEY not found in environment")
    exit(1)

client = openai.OpenAI(api_key=api_key)

# Executive profiles for headshot generation
EXECUTIVES = {
    'sarah_chen': {
        'name': 'Sarah Chen',
        'role': 'CEO',
        'prompt': 'Professional corporate headshot of an Asian female executive in her 40s, wearing a dark business suit, confident smile, modern office background, high quality, natural lighting, professional photography style'
    },
    'michael_rodriguez': {
        'name': 'Michael Rodriguez',
        'role': 'CFO',
        'prompt': 'Professional corporate headshot of a Hispanic male executive in his 40s, wearing glasses and a dark suit, analytical expression, modern office background, high quality, natural lighting, professional photography style'
    },
    'lisa_kincaid': {
        'name': 'Dr. Lisa Kincaid',
        'role': 'CTO',
        'prompt': 'Professional corporate headshot of a female technology executive in her 40s, wearing smart business attire, intelligent and focused expression, modern tech office background, high quality, natural lighting, professional photography style'
    },
    'james_thompson': {
        'name': 'James Thompson',
        'role': 'CMO',
        'prompt': 'Professional corporate headshot of a male marketing executive in his 40s, wearing a modern business suit, creative and energetic expression, contemporary office background, high quality, natural lighting, professional photography style'
    },
    'rebecca_johnson': {
        'name': 'Rebecca Johnson',
        'role': 'COO',
        'prompt': 'Professional corporate headshot of a female operations executive in her 40s, wearing professional business attire, efficient and composed expression, modern office background, high quality, natural lighting, professional photography style'
    }
}

def generate_headshot(exec_id, exec_info):
    """Generate a single headshot using DALL-E 3"""
    try:
        print(f"\n🎨 Generating headshot for {exec_info['name']} ({exec_info['role']})...")
        print(f"   Prompt: {exec_info['prompt'][:80]}...")

        # Generate image using DALL-E 3
        response = client.images.generate(
            model="dall-e-3",
            prompt=exec_info['prompt'],
            size="1024x1024",  # Square format for headshots
            quality="standard",  # "hd" for higher quality but 2x cost
            n=1
        )

        # Get image URL
        image_url = response.data[0].url
        print(f"   ✅ Image generated: {image_url}")

        # Download image
        print(f"   📥 Downloading image...")
        image_response = requests.get(image_url)
        image_response.raise_for_status()

        # Save image
        output_path = f"static/images/executives/{exec_id}.png"
        with open(output_path, 'wb') as f:
            f.write(image_response.content)

        print(f"   💾 Saved to: {output_path}")
        print(f"   ✅ {exec_info['name']} headshot complete!")

        return True

    except Exception as e:
        print(f"   ❌ Error generating {exec_info['name']}: {e}")
        return False

def main():
    """Generate all executive headshots"""
    print("="*60)
    print("🎭 Executive Headshot Generator")
    print("="*60)
    print(f"\nGenerating {len(EXECUTIVES)} headshots using DALL-E 3...")

    success_count = 0
    failed_count = 0

    for exec_id, exec_info in EXECUTIVES.items():
        if generate_headshot(exec_id, exec_info):
            success_count += 1
        else:
            failed_count += 1

    print("\n" + "="*60)
    print("📊 Generation Summary")
    print("="*60)
    print(f"✅ Successful: {success_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"📁 Images saved to: static/images/executives/")
    print("\nHeadshots ready for use in the simulator!")

if __name__ == '__main__':
    main()

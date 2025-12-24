#!/usr/bin/env python3
"""
Create placeholder headshots for executive panel members
These are simple colored avatars with initials that can be replaced with AI-generated images later
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Executive profiles
EXECUTIVES = {
    'sarah_chen': {
        'name': 'Sarah Chen',
        'role': 'CEO',
        'initials': 'SC',
        'color': '#BF5700'  # UT Orange
    },
    'michael_rodriguez': {
        'name': 'Michael Rodriguez',
        'role': 'CFO',
        'initials': 'MR',
        'color': '#005F86'  # Blue
    },
    'lisa_kincaid': {
        'name': 'Dr. Lisa Kincaid',
        'role': 'CTO',
        'initials': 'LK',
        'color': '#6A5ACD'  # Slate Blue
    },
    'james_thompson': {
        'name': 'James Thompson',
        'role': 'CMO',
        'initials': 'JT',
        'color': '#2E8B57'  # Sea Green
    },
    'rebecca_johnson': {
        'name': 'Rebecca Johnson',
        'role': 'COO',
        'initials': 'RJ',
        'color': '#8B4513'  # Saddle Brown
    }
}

def create_placeholder_headshot(exec_id, exec_info):
    """Create a simple placeholder headshot with initials"""
    try:
        # Create a 400x400 image
        size = 400
        img = Image.new('RGB', (size, size), color=exec_info['color'])
        draw = ImageDraw.Draw(img)

        # Try to use a nice font, fall back to default if not available
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 150)
        except:
            font = ImageFont.load_default()

        # Get text bounding box for centering
        initials = exec_info['initials']
        bbox = draw.textbbox((0, 0), initials, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Calculate position to center text
        x = (size - text_width) / 2 - bbox[0]
        y = (size - text_height) / 2 - bbox[1]

        # Draw white text
        draw.text((x, y), initials, fill='white', font=font)

        # Add a subtle circle border
        draw.ellipse([10, 10, size-10, size-10], outline='white', width=5)

        # Save image
        output_path = f"static/images/executives/{exec_id}.png"
        img.save(output_path)

        print(f"✅ Created placeholder for {exec_info['name']}: {output_path}")
        return True

    except Exception as e:
        print(f"❌ Error creating placeholder for {exec_info['name']}: {e}")
        return False

def main():
    """Create all placeholder headshots"""
    print("="*60)
    print("🎭 Creating Placeholder Executive Headshots")
    print("="*60)
    print(f"\nCreating {len(EXECUTIVES)} placeholder headshots...")
    print("(These can be replaced with AI-generated images using DALL-E 3)\n")

    # Ensure directory exists
    os.makedirs("static/images/executives", exist_ok=True)

    success_count = 0
    for exec_id, exec_info in EXECUTIVES.items():
        if create_placeholder_headshot(exec_id, exec_info):
            success_count += 1

    print(f"\n✅ Created {success_count}/{len(EXECUTIVES)} placeholder headshots")
    print(f"📁 Images saved to: static/images/executives/")
    print("\nTo generate AI headshots with DALL-E 3:")
    print("  1. Ensure OPENAI_API_KEY is set in your environment")
    print("  2. Run: python generate_headshots.py")

if __name__ == '__main__':
    main()

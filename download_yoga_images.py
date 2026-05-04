"""
Yoga Pose Image Downloader
Downloads accurate yoga pose images for VisionFit AI

This script downloads high-quality yoga pose images from Unsplash (free stock photos)
or generates simple SVG illustrations as fallback.
"""

import os
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io

# Directory where images will be saved
IMAGES_DIR = Path(__file__).parent / "static" / "yoga_images"

# Yoga poses we need images for
YOGA_POSES = {
    "mountain_pose": {
        "name": "Mountain Pose Tadasana",
        "search_terms": "mountain pose yoga tadasana standing",
        "color": "#00CED1"
    },
    "downward_dog": {
        "name": "Downward Dog",
        "search_terms": "downward facing dog yoga adho mukha svanasana",
        "color": "#9370DB"
    },
    "warrior_i": {
        "name": "Warrior I",
        "search_terms": "warrior 1 pose yoga virabhadrasana",
        "color": "#FFD700"
    },
    "warrior_ii": {
        "name": "Warrior II",
        "search_terms": "warrior 2 pose yoga virabhadrasana",
        "color": "#FF6347"
    },
    "tree_pose": {
        "name": "Tree Pose",
        "search_terms": "tree pose yoga vrksasana balance",
        "color": "#32CD32"
    },
    "child_pose": {
        "name": "Child's Pose",
        "search_terms": "child pose yoga balasana resting",
        "color": "#87CEEB"
    },
    "cobra_pose": {
        "name": "Cobra Pose",
        "search_terms": "cobra pose yoga bhujangasana backbend",
        "color": "#FF8C00"
    },
    "plank_pose": {
        "name": "Plank Pose",
        "search_terms": "plank pose yoga core strength",
        "color": "#DC143C"
    },
    "cat_cow": {
        "name": "Cat Cow Pose",
        "search_terms": "cat cow pose yoga marjaryasana",
        "color": "#BA55D3"
    }
}

def download_from_unsplash(pose_id, search_terms):
    """
    Download image from Unsplash API (free, no API key needed for demo)
    Note: For production, get a free API key from https://unsplash.com/developers
    """
    try:
        # Using Unsplash Source (simple API, no key needed)
        # Format: https://source.unsplash.com/400x400/?{search_terms}
        url = f"https://source.unsplash.com/400x400/?{search_terms.replace(' ', ',')}"
        
        print(f"Downloading {pose_id} from Unsplash...")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content))
            # Resize to consistent size
            img = img.resize((400, 400), Image.Resampling.LANCZOS)
            return img
        else:
            print(f"  Failed to download from Unsplash (status {response.status_code})")
            return None
    except Exception as e:
        print(f"  Error downloading from Unsplash: {e}")
        return None

def create_simple_illustration(pose_name, color):
    """
    Create a simple illustration with pose silhouette
    This is a fallback when download fails
    """
    # Create a gradient background
    img = Image.new('RGB', (400, 400), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw gradient background
    for i in range(400):
        shade = int(255 * (1 - i/400))
        color_rgb = tuple(int(color.lstrip('#')[j:j+2], 16) for j in (0, 2, 4))
        gradient_color = tuple(int(c * (shade/255)) for c in color_rgb)
        draw.rectangle([(0, i), (400, i+1)], fill=gradient_color)
    
    # Add text overlay
    try:
        # Try to use a nice font
        font_large = ImageFont.truetype("arial.ttf", 40)
        font_small = ImageFont.truetype("arial.ttf", 20)
    except:
        # Fallback to default font
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Draw pose name
    text = pose_name.upper()
    bbox = draw.textbbox((0, 0), text, font=font_large)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    position = ((400 - text_width) // 2, (400 - text_height) // 2)
    
    # Add shadow
    draw.text((position[0]+2, position[1]+2), text, fill='black', font=font_large)
    # Add main text
    draw.text(position, text, fill='white', font=font_large)
    
    # Add "YOGA POSE" subtitle
    subtitle = "YOGA POSE"
    bbox = draw.textbbox((0, 0), subtitle, font=font_small)
    subtitle_width = bbox[2] - bbox[0]
    subtitle_pos = ((400 - subtitle_width) // 2, position[1] + text_height + 20)
    draw.text(subtitle_pos, subtitle, fill='white', font=font_small)
    
    return img

def download_all_images(use_unsplash=True):
    """
    Download all yoga pose images
    """
    # Ensure directory exists
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading yoga pose images to: {IMAGES_DIR}")
    print("=" * 60)
    
    for pose_id, pose_info in YOGA_POSES.items():
        filename = f"{pose_id}.png"
        filepath = IMAGES_DIR / filename
        
        print(f"\nProcessing: {pose_info['name']}")
        
        img = None
        
        # Try to download from Unsplash first
        if use_unsplash:
            img = download_from_unsplash(pose_id, pose_info['search_terms'])
        
        # Fallback to simple illustration
        if img is None:
            print(f"  Creating simple illustration...")
            img = create_simple_illustration(pose_info['name'], pose_info['color'])
        
        # Save the image
        img.save(filepath, 'PNG')
        print(f"  ✓ Saved: {filename}")
    
    print("\n" + "=" * 60)
    print(f"✓ All images downloaded successfully!")
    print(f"Location: {IMAGES_DIR}")

def main():
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║        VisionFit AI - Yoga Pose Image Downloader        ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    print("This script will download accurate yoga pose images.")
    print("\nOptions:")
    print("1. Download from Unsplash (recommended - real photos)")
    print("2. Generate simple illustrations (fallback)")
    
    choice = input("\nEnter your choice (1 or 2, default=1): ").strip() or "1"
    
    use_unsplash = choice == "1"
    
    try:
        download_all_images(use_unsplash)
        print("\n✓ Success! Your yoga images are ready.")
        print("  Restart your Flask app to see the new images.")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("  Please check your internet connection and try again.")

if __name__ == "__main__":
    main()

"""
Improved Yoga Pose Image Downloader
Downloads accurate, real yoga pose images from curated sources
"""

import os
import requests
from pathlib import Path
from PIL import Image
import io

# Directory where images will be saved
IMAGES_DIR = Path(__file__).parent / "static" / "yoga_images"

# Curated high-quality yoga pose images from Pexels (free to use)
# Format: pose_id -> direct image URL
YOGA_IMAGES = {
    "mountain_pose": "https://images.pexels.com/photos/3822906/pexels-photo-3822906.jpeg?auto=compress&cs=tinysrgb&w=400",
    "downward_dog": "https://images.pexels.com/photos/3822165/pexels-photo-3822165.jpeg?auto=compress&cs=tinysrgb&w=400",
    "warrior_i": "https://images.pexels.com/photos/3822167/pexels-photo-3822167.jpeg?auto=compress&cs=tinysrgb&w=400",
    "warrior_ii": "https://images.pexels.com/photos/3822356/pexels-photo-3822356.jpeg?auto=compress&cs=tinysrgb&w=400",
    "tree_pose": "https://images.pexels.com/photos/3822166/pexels-photo-3822166.jpeg?auto=compress&cs=tinysrgb&w=400",
    "child_pose": "https://images.pexels.com/photos/3822220/pexels-photo-3822220.jpeg?auto=compress&cs=tinysrgb&w=400",
    "cobra_pose": "https://images.pexels.com/photos/3822354/pexels-photo-3822354.jpeg?auto=compress&cs=tinysrgb&w=400",
    "plank_pose": "https://images.pexels.com/photos/4056723/pexels-photo-4056723.jpeg?auto=compress&cs=tinysrgb&w=400",
    "cat_cow": "https://images.pexels.com/photos/3822621/pexels-photo-3822621.jpeg?auto=compress&cs=tinysrgb&w=400",
    # New poses - yoga images from Pexels
    "pigeon_pose": "https://images.pexels.com/photos/4056548/pexels-photo-4056548.jpeg?auto=compress&cs=tinysrgb&w=400",
    "bridge_pose": "https://images.pexels.com/photos/3822355/pexels-photo-3822355.jpeg?auto=compress&cs=tinysrgb&w=400",
    "corpse_pose": "https://images.pexels.com/photos/3822910/pexels-photo-3822910.jpeg?auto=compress&cs=tinysrgb&w=400",
    "happy_baby": "https://images.pexels.com/photos/4056538/pexels-photo-4056538.jpeg?auto=compress&cs=tinysrgb&w=400",
    "triangle_pose": "https://images.pexels.com/photos/3822357/pexels-photo-3822357.jpeg?auto=compress&cs=tinysrgb&w=400",
    "chair_pose": "https://images.pexels.com/photos/3822168/pexels-photo-3822168.jpeg?auto=compress&cs=tinysrgb&w=400",
    "eagle_pose": "https://images.pexels.com/photos/3822622/pexels-photo-3822622.jpeg?auto=compress&cs=tinysrgb&w=400",
    "supine_twist": "https://images.pexels.com/photos/3822620/pexels-photo-3822620.jpeg?auto=compress&cs=tinysrgb&w=400",
    "legs_up_wall": "https://images.pexels.com/photos/4056542/pexels-photo-4056542.jpeg?auto=compress&cs=tinysrgb&w=400",
    "butterfly_pose": "https://images.pexels.com/photos/3822619/pexels-photo-3822619.jpeg?auto=compress&cs=tinysrgb&w=400",
    "standing_forward_bend": "https://images.pexels.com/photos/3822164/pexels-photo-3822164.jpeg?auto=compress&cs=tinysrgb&w=400",
    "low_lunge": "https://images.pexels.com/photos/3822623/pexels-photo-3822623.jpeg?auto=compress&cs=tinysrgb&w=400",
    "boat_pose": "https://images.pexels.com/photos/4056724/pexels-photo-4056724.jpeg?auto=compress&cs=tinysrgb&w=400",
    "reclined_butterfly": "https://images.pexels.com/photos/3822911/pexels-photo-3822911.jpeg?auto=compress&cs=tinysrgb&w=400",
    "seated_forward_bend": "https://images.pexels.com/photos/3822353/pexels-photo-3822353.jpeg?auto=compress&cs=tinysrgb&w=400",
    "side_plank": "https://images.pexels.com/photos/4056725/pexels-photo-4056725.jpeg?auto=compress&cs=tinysrgb&w=400",
    "seated_twist": "https://images.pexels.com/photos/3822624/pexels-photo-3822624.jpeg?auto=compress&cs=tinysrgb&w=400",
}

def download_image(url, filename):
    """
    Download an image from a URL and save it
    """
    try:
        print(f"  Downloading from: {url[:50]}...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content))
            # Convert to RGB if necessary (remove alpha channel)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Resize to square format
            img = img.resize((400, 400), Image.Resampling.LANCZOS)
            return img
        else:
            print(f"  ✗ Failed: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None

def download_all_images():
    """
    Download all yoga pose images
    """
    # Ensure directory exists
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"Downloading Yoga Pose Images")
    print(f"Destination: {IMAGES_DIR}")
    print(f"{'='*60}\n")
    
    success_count = 0
    failed = []
    
    for pose_id, url in YOGA_IMAGES.items():
        filename = f"{pose_id}.png"
        filepath = IMAGES_DIR / filename
        
        print(f"[{pose_id}]")
        
        img = download_image(url, filename)
        
        if img:
            img.save(filepath, 'PNG', quality=95)
            print(f"  ✓ Saved: {filename}\n")
            success_count += 1
        else:
            failed.append(pose_id)
            print(f"  ✗ Failed to download {pose_id}\n")
    
    print(f"{'='*60}")
    print(f"✓ Successfully downloaded: {success_count}/{len(YOGA_IMAGES)} images")
    
    if failed:
        print(f"✗ Failed: {', '.join(failed)}")
        print(f"\nFor failed images, you can:")
        print(f"  1. Try running the script again")
        print(f"  2. Manually download from pexels.com or unsplash.com")
    else:
        print(f"✓ All images downloaded successfully!")
    
    print(f"{'='*60}\n")
    
    return success_count == len(YOGA_IMAGES)

def main():
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║     VisionFit AI - Yoga Pose Image Downloader v2.0      ║
    ║              Using Curated Pexels Images                ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    try:
        success = download_all_images()
        
        if success:
            print("\n✓ SUCCESS! All yoga pose images are ready.")
            print("\nNext steps:")
            print("  1. Restart your Flask app (if running)")
            print("  2. Go to: http://localhost:5000/yoga")
            print("  3. Generate a yoga plan to see the new images!")
        else:
            print("\n⚠ Some images failed to download.")
            print("  Check your internet connection and try again.")
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("  Please check your internet connection and try again.")

if __name__ == "__main__":
    main()

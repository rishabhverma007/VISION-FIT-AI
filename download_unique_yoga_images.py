"""
Unique Yoga Pose Image Downloader - Version 3
Downloads UNIQUE, accurate yoga pose images with no duplicates
Uses multiple sources and specific pose queries
"""

import os
import requests
from pathlib import Path
from PIL import Image
import io
import hashlib

# Directory where images will be saved
IMAGES_DIR = Path(__file__).parent / "static" / "yoga_images"

# Carefully curated UNIQUE yoga pose images from multiple free sources
# Each URL is specifically selected to show the EXACT pose with no duplicates
YOGA_IMAGES_UNIQUE = {
    "mountain_pose": {
        "url": "https://images.pexels.com/photos/3822906/pexels-photo-3822906.jpeg?auto=compress&cs=tinysrgb&w=600",
        "description": "Standing tall, feet together, arms at sides"
    },
    "downward_dog": {
        "url": "https://images.pexels.com/photos/3822165/pexels-photo-3822165.jpeg?auto=compress&cs=tinysrgb&w=600",
        "description": "Inverted V-shape, hands and feet on ground"
    },
    "warrior_i": {
        "url": "https://images.pexels.com/photos/3822167/pexels-photo-3822167.jpeg?auto=compress&cs=tinysrgb&w=600",
        "description": "Lunge with arms raised overhead"
    },
    "warrior_ii": {
        "url": "https://images.pexels.com/photos/3822356/pexels-photo-3822356.jpeg?auto=compress&cs=tinysrgb&w=600",
        "description": "Wide stance, arms extended to sides"
    },
    "tree_pose": {
        "url": "https://images.pexels.com/photos/3822166/pexels-photo-3822166.jpeg?auto=compress&cs=tinysrgb&w=600",
        "description": "Standing on one leg, foot on thigh"
    },
    "child_pose": {
        "url": "https://images.pexels.com/photos/3822220/pexels-photo-3822220.jpeg?auto=compress&cs=tinysrgb&w=600",
        "description": "Kneeling, forehead to ground, resting"
    },
    "cobra_pose": {
        "url": "https://images.pexels.com/photos/3822354/pexels-photo-3822354.jpeg?auto=compress&cs=tinysrgb&w=600",
        "description": "Lying prone, chest lifted, backbend"
    },
    "plank_pose": {
        "url": "https://images.pexels.com/photos/4056723/pexels-photo-4056723.jpeg?auto=compress&cs=tinysrgb&w=600",
        "description": "Pushup position, body straight"
    },
    "cat_cow": {
        "url": "https://images.pexels.com/photos/3822621/pexels-photo-3822621.jpeg?auto=compress&cs=tinysrgb&w=600",
        "description": "On hands and knees, back arched"
    }
}

def get_image_hash(img):
    """Calculate hash of image to detect duplicates"""
    return hashlib.md5(img.tobytes()).hexdigest()

def download_image(url, filename, description):
    """
    Download an image from a URL and save it
    """
    try:
        print(f"  Downloading: {description}")
        print(f"  URL: {url[:60]}...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=20)
        
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content))
            
            # Convert to RGB if necessary
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
    Download all unique yoga pose images and verify no duplicates
    """
    # Ensure directory exists
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*70}")
    print(f"Downloading UNIQUE Yoga Pose Images (No Duplicates)")
    print(f"Destination: {IMAGES_DIR}")
    print(f"{'='*70}\n")
    
    downloaded_images = {}
    image_hashes = {}
    success_count = 0
    failed = []
    duplicates = []
    
    for pose_id, pose_data in YOGA_IMAGES_UNIQUE.items():
        filename = f"{pose_id}.png"
        filepath = IMAGES_DIR / filename
        
        print(f"[{pose_id.upper().replace('_', ' ')}]")
        
        img = download_image(pose_data['url'], filename, pose_data['description'])
        
        if img:
            # Check for duplicates
            img_hash = get_image_hash(img)
            
            if img_hash in image_hashes:
                print(f"  ⚠ WARNING: Duplicate detected! Same as {image_hashes[img_hash]}")
                duplicates.append((pose_id, image_hashes[img_hash]))
            else:
                image_hashes[img_hash] = pose_id
            
            # Save the image
            img.save(filepath, 'PNG', quality=95)
            downloaded_images[pose_id] = img
            print(f"  ✓ Saved: {filename}")
            print(f"  Size: {filepath.stat().st_size / 1024:.1f} KB\n")
            success_count += 1
        else:
            failed.append(pose_id)
            print(f"  ✗ Failed to download {pose_id}\n")
    
    print(f"{'='*70}")
    print(f"✓ Successfully downloaded: {success_count}/{len(YOGA_IMAGES_UNIQUE)} images")
    
    if duplicates:
        print(f"\n⚠ DUPLICATES FOUND:")
        for dup1, dup2 in duplicates:
            print(f"  - {dup1} is same as {dup2}")
        print(f"\n  You may need to manually replace these with different images.")
    else:
        print(f"✓ No duplicates detected - all images are unique!")
    
    if failed:
        print(f"\n✗ Failed: {', '.join(failed)}")
        print(f"\nFor failed images, you can:")
        print(f"  1. Try running the script again")
        print(f"  2. Manually download from pexels.com or unsplash.com")
    
    print(f"{'='*70}\n")
    
    return success_count == len(YOGA_IMAGES_UNIQUE) and len(duplicates) == 0

def main():
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║     VisionFit AI - Unique Yoga Pose Image Downloader v3.0       ║
    ║          Ensuring Each Pose Has a Unique, Accurate Image        ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        success = download_all_images()
        
        if success:
            print("\n✓ SUCCESS! All yoga pose images are unique and ready.")
            print("\nNext steps:")
            print("  1. Your Flask app should auto-reload (if running in debug mode)")
            print("  2. Or restart: Ctrl+C then run .\\run_visionfit.bat")
            print("  3. Go to: http://localhost:5000/yoga")
            print("  4. Generate a yoga plan to verify all images are different!")
        else:
            print("\n⚠ Some issues detected.")
            print("  Please review the output above and fix any duplicates or failures.")
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("  Please check your internet connection and try again.")

if __name__ == "__main__":
    main()

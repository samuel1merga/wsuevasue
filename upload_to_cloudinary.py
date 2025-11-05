import os
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Cloudinary configuration
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME', 'diabmp2ch'),
    api_key=os.getenv('CLOUDINARY_API_KEY', '822588618995714'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET', 'tNi0vwgDa17yPw1NQNDWz6dmaFc')
)

# Local media folder
media_dir = "media/"

if not os.path.exists(media_dir):
    print("⚠️ No 'media/' folder found. Nothing to upload.")
else:
    for root, dirs, files in os.walk(media_dir):
        for file in files:
            file_path = os.path.join(root, file)
            result = cloudinary.uploader.upload(file_path)
            print(f"✅ Uploaded {file_path} as {result['public_id']}")

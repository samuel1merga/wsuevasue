import os
import cloudinary
import cloudinary.uploader
from django.conf import settings
import django

# Initialize Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wsuevasue.settings")
django.setup()

# Configure Cloudinary
cloudinary.config(
    cloud_name=settings.CLOUDINARY_STORAGE['CLOUD_NAME'],
    api_key=settings.CLOUDINARY_STORAGE['API_KEY'],
    api_secret=settings.CLOUDINARY_STORAGE['API_SECRET']
)

# Define your local media directory
MEDIA_ROOT = os.path.join(settings.BASE_DIR, 'media')

def upload_directory_to_cloudinary(directory_path, cloudinary_folder="media"):
    """
    Recursively upload files from a local folder to Cloudinary.
    """
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            local_file_path = os.path.join(root, file)
            # Create relative folder structure for Cloudinary
            relative_path = os.path.relpath(local_file_path, directory_path)
            public_id = os.path.join(cloudinary_folder, os.path.splitext(relative_path)[0]).replace("\\", "/")

            print(f"Uploading: {local_file_path} -> {public_id}")

            try:
                cloudinary.uploader.upload(
                    local_file_path,
                    public_id=public_id,
                    folder=cloudinary_folder,
                    overwrite=False,
                    resource_type="auto"
                )
            except Exception as e:
                print(f"❌ Failed to upload {file}: {e}")

    print("✅ Upload complete!")

if __name__ == "__main__":
    if not os.path.exists(MEDIA_ROOT):
        print("⚠️ No 'media/' folder found. Nothing to upload.")
    else:
        print("🚀 Starting upload to Cloudinary...")
        upload_directory_to_cloudinary(MEDIA_ROOT)

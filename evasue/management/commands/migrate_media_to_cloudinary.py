# evasue/management/commands/migrate_media_to_cloudinary.py
from django.core.management.base import BaseCommand
from evasue.models import Team, User
import cloudinary.uploader
import requests
from io import BytesIO
from django.core.files.base import ContentFile
from urllib.parse import urljoin
from django.conf import settings

class Command(BaseCommand):
    help = "Migrate existing Team and User images from Render ephemeral storage to Cloudinary"

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting migration to Cloudinary...")

        # --- Teams ---
        for team in Team.objects.all():
            if team.image and not team.image.startswith('http'):
                self.stdout.write(f"Processing Team '{team.name}' image...")
                try:
                    # Try fetching the file from Render storage (temporary)
                    file_url = urljoin(settings.MEDIA_URL, team.image)
                    response = requests.get(file_url)
                    if response.status_code == 200:
                        # Upload to Cloudinary
                        cloud_resp = cloudinary.uploader.upload(
                            BytesIO(response.content),
                            folder="team_backgrounds",
                            public_id=team.name.replace(" ", "_"),
                            overwrite=True
                        )
                        team.image = cloud_resp['secure_url']
                        team.save()
                        self.stdout.write(self.style.SUCCESS(f"✅ Team '{team.name}' image uploaded"))
                    else:
                        self.stdout.write(self.style.WARNING(f"⚠️ Team '{team.name}' image not found at {file_url}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Error uploading Team '{team.name}': {e}"))

        # --- Users ---
        for user in User.objects.all():
            if user.profile_image and not user.profile_image.startswith('http'):
                self.stdout.write(f"Processing User '{user.username}' profile image...")
                try:
                    file_url = urljoin(settings.MEDIA_URL, user.profile_image)
                    response = requests.get(file_url)
                    if response.status_code == 200:
                        cloud_resp = cloudinary.uploader.upload(
                            BytesIO(response.content),
                            folder="profiles",
                            public_id=user.username,
                            overwrite=True
                        )
                        user.profile_image = cloud_resp['secure_url']
                        user.save()
                        self.stdout.write(self.style.SUCCESS(f"✅ User '{user.username}' profile image uploaded"))
                    else:
                        self.stdout.write(self.style.WARNING(f"⚠️ User '{user.username}' image not found at {file_url}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Error uploading User '{user.username}': {e}"))

        self.stdout.write(self.style.SUCCESS("Migration complete!"))

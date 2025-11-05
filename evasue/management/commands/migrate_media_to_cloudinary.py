# evasue/management/commands/migrate_media_to_cloudinary.py
from django.core.management.base import BaseCommand
from evasue.models import Team, User
import cloudinary.uploader
import os

class Command(BaseCommand):
    help = "Upload existing Team and User images to Cloudinary safely"

    def handle(self, *args, **kwargs):
        # --- Teams ---
        teams = Team.objects.all()
        for team in teams:
            if team.image:
                # Check if it's already a Cloudinary URL
                if not team.image.url.startswith('http'):
                    # Check if the file exists on Render
                    local_path = team.image.path if os.path.exists(team.image.path) else None
                    if local_path:
                        self.stdout.write(f"Uploading Team '{team.name}' image to Cloudinary...")
                        try:
                            response = cloudinary.uploader.upload(local_path, folder="team_backgrounds")
                            team.image = response['secure_url']
                            team.save()
                            self.stdout.write(self.style.SUCCESS(f"✅ Team '{team.name}' image uploaded"))
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"❌ Error uploading Team '{team.name}': {e}"))
                    else:
                        self.stdout.write(self.style.WARNING(f"⚠️ Team '{team.name}' image not found locally, skipping"))
        
        # --- Users ---
        users = User.objects.all()
        for user in users:
            if user.profile_image:
                if not user.profile_image.url.startswith('http'):
                    local_path = user.profile_image.path if os.path.exists(user.profile_image.path) else None
                    if local_path:
                        self.stdout.write(f"Uploading User '{user.username}' profile image to Cloudinary...")
                        try:
                            response = cloudinary.uploader.upload(local_path, folder="profiles")
                            user.profile_image = response['secure_url']
                            user.save()
                            self.stdout.write(self.style.SUCCESS(f"✅ User '{user.username}' profile image uploaded"))
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"❌ Error uploading User '{user.username}': {e}"))
                    else:
                        self.stdout.write(self.style.WARNING(f"⚠️ User '{user.username}' profile image not found locally, skipping"))

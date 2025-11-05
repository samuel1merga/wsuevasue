# evasue/management/commands/migrate_media_to_cloudinary.py
from django.core.management.base import BaseCommand
from evasue.models import Team, User
import cloudinary.uploader

class Command(BaseCommand):
    help = "Re-upload existing Team and User images to Cloudinary"

    def handle(self, *args, **kwargs):
        # --- Teams ---
        teams = Team.objects.all()
        for team in teams:
            if team.image and not str(team.image).startswith('http'):
                self.stdout.write(f"Uploading Team '{team.name}' image to Cloudinary...")
                try:
                    response = cloudinary.uploader.upload(team.image.path, folder="team_backgrounds")
                    team.image = response['secure_url']
                    team.save()
                    self.stdout.write(self.style.SUCCESS(f"✅ Team '{team.name}' image uploaded"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Error uploading Team '{team.name}': {e}"))

        # --- Users ---
        users = User.objects.all()
        for user in users:
            if user.profile_image and not str(user.profile_image).startswith('http'):
                self.stdout.write(f"Uploading User '{user.username}' profile image to Cloudinary...")
                try:
                    response = cloudinary.uploader.upload(user.profile_image.path, folder="profiles")
                    user.profile_image = response['secure_url']
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f"✅ User '{user.username}' profile image uploaded"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Error uploading User '{user.username}': {e}"))

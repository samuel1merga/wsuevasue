import os
from django.core.management.base import BaseCommand
from cloudinary.uploader import upload
from evasue.models import User, Team
from django.conf import settings

class Command(BaseCommand):
    help = "Upload existing media files to Cloudinary"

    def handle(self, *args, **kwargs):
        # Upload User profile images
        for user in User.objects.all():
            if user.profile_image and not user.profile_image.url.startswith('http'):
                local_path = settings.MEDIA_ROOT / user.profile_image.name
                if os.path.exists(local_path):
                    result = upload(str(local_path), folder='profiles')
                    user.profile_image = result['secure_url']
                    user.save()
                    self.stdout.write(f"Uploaded {user.username}'s profile image.")

        # Upload Team images
        for team in Team.objects.all():
            if team.image and not team.image.url.startswith('http'):
                local_path = settings.MEDIA_ROOT / team.image.name
                if os.path.exists(local_path):
                    result = upload(str(local_path), folder='team_backgrounds')
                    team.image = result['secure_url']
                    team.save()
                    self.stdout.write(f"Uploaded {team.name}'s team image.")
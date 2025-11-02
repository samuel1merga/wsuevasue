from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('leader', 'Leader'),
        ('member', 'Member'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)
    full_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    batch = models.CharField(max_length=2)
    def __str__(self):
        return f"{self.username} ({self.role})"


class Team(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    members = models.ManyToManyField(User, related_name='teams')
    image = models.ImageField(upload_to='team_backgrounds/', null=True, blank=True)

    leaders = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='leading_teams',
        limit_choices_to={'role': 'leader'},
        blank=True
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Membership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    active = models.BooleanField(default=False)  # Default to inactive until approved

    class Meta:
        unique_together = ('user', 'team')

    def __str__(self):
        return f"{self.user.username} in {self.team.name} ({'Active' if self.active else 'Inactive'})"


class Message(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message by {self.author.username} on {self.team.name}"


class JoinRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    requested_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)  # Set True by leader/admin when approved
    processed = models.BooleanField(default=False)  # True when leader/admin acted on the request

    class Meta:
        unique_together = ('user', 'team')

    @property
    def status(self):
        if self.approved:
            return "Approved"
        if self.processed:
            return "Rejected"
        return "Pending"

    def __str__(self):
        return f"JoinRequest: {self.user.username} for {self.team.name} ({self.status})"

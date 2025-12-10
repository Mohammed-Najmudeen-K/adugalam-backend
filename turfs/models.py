# turfs/models.py
from django.db import models

SPORT_CHOICES = [
    ("football", "Football"),
    ("cricket", "Cricket"),
    ("badminton", "Badminton"),
    ("multi", "Multi-sport"),
]

class Turf(models.Model):
    # owner is a Player (admin) — use string reference to avoid circular imports
    owner = models.ForeignKey("users.Player", on_delete=models.SET_NULL, null=True, blank=True, related_name="owned_turfs")

    name = models.CharField(max_length=200)
    location = models.CharField(max_length=300)
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    sport_type = models.CharField(max_length=20, choices=SPORT_CHOICES, default="multi")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class TurfImage(models.Model):
    turf = models.ForeignKey(Turf, on_delete=models.CASCADE, related_name="turf_images")
    image = models.ImageField(upload_to="turf_images/")

    def __str__(self):
        return f"Image for {self.turf.name}"




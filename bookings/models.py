from django.db import models
from django.utils import timezone
from users.models import Player
from turfs.models import Turf


# ----------------------------------------------------
# SLOT MODEL
# ----------------------------------------------------
class Slot(models.Model):
    turf = models.ForeignKey(Turf, on_delete=models.CASCADE, related_name="slots")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_booked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.turf.name} | {self.start_time} - {self.end_time}"


# ----------------------------------------------------
# BOOKING MODEL
# ----------------------------------------------------
class Booking(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    slot = models.ForeignKey(Slot, on_delete=models.CASCADE)
    booked_at = models.DateTimeField(default=timezone.now)
    is_cancelled = models.BooleanField(default=False)
    payment_status = models.CharField(max_length=20, default="pending")
    advance_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)


    def __str__(self):
        return f"Booking #{self.id} by {self.player.phone}"

# users/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

# -----------------------------------
# CUSTOM USER MANAGER
# -----------------------------------
class PlayerManager(BaseUserManager):
    def create_user(self, phone, password=None):
        if not phone:
            raise ValueError("Phone number required")
        user = self.model(phone=phone)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password):
        user = self.create_user(phone, password)
        user.is_admin = True
        user.save(using=self._db)
        return user


# -----------------------------------
# PLAYER MODEL
# -----------------------------------
class Player(AbstractBaseUser):
    name = models.CharField(max_length=200, blank=True, null=True)
    phone = models.CharField(max_length=20, unique=True)
    email = models.CharField(max_length=200, blank=True, null=True)
    profile_photo = models.ImageField(upload_to="players/", blank=True, null=True)
    wallet = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    city = models.CharField(max_length=100, blank=True, null=True)


    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


    USERNAME_FIELD = "phone"
    objects = PlayerManager()

    def __str__(self):
        return self.phone


# -----------------------------------
# OTP MODEL
# -----------------------------------
class OTP(models.Model):
    phone = models.CharField(max_length=20)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)


# -----------------------------------
# WALLET TRANSACTIONS
# -----------------------------------
class WalletTransaction(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=10)  # add / subtract
    created_at = models.DateTimeField(auto_now_add=True)


# -----------------------------------
# FAVOURITES
# -----------------------------------
class Favourite(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    # refer to Turf by string to avoid ordering issues
    turf = models.ForeignKey("turfs.Turf", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


# -----------------------------------
# REVIEWS
# -----------------------------------
class Review(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    turf = models.ForeignKey("turfs.Turf", on_delete=models.CASCADE)
    rating = models.IntegerField(default=5)
    title = models.CharField(max_length=250, blank=True, null=True)   # views expect title
    body = models.TextField(blank=True, null=True)                    # views expect body
    comment = models.TextField(blank=True, null=True)                 # optional legacy
    created_at = models.DateTimeField(auto_now_add=True)


# -----------------------------------
# NOTIFICATIONS
# -----------------------------------
class Notification(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    body = models.TextField()   # changed to 'body' because views use n.body
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)


# -----------------------------------
# CART (and items)
# -----------------------------------
class Cart(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class CartItem(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    turf = models.ForeignKey("turfs.Turf", on_delete=models.CASCADE)
    slot = models.ForeignKey("bookings.Slot", on_delete=models.CASCADE)  # FIXED
    qty = models.IntegerField(default=1)
    date = models.DateField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)


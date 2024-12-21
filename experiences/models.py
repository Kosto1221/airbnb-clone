from django.db import models
from common.models import CommonModel
from datetime import date


class Experience(CommonModel):

    """Experience Model Definiiton"""

    country = models.CharField(
        max_length=50,
        default="한국",
    )
    city = models.CharField(
        max_length=80,
        default="서울",
    )
    name = models.CharField(
        max_length=250,
    )
    host = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="experiences",
    )
    price = models.PositiveIntegerField()
    address = models.CharField(
        max_length=250,
    )
    event_date = models.DateField(default=date.today)
    start = models.TimeField()
    end = models.TimeField()
    is_public = models.BooleanField(
        default=True,
        help_text="Allow multiple bookings"
    )
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField()
    perks = models.ManyToManyField(
        "experiences.Perk",
        related_name="experiences",
    )
    category = models.ForeignKey("categories.Category", blank=True, null=True, on_delete=models.SET_NULL, related_name="experiences",)

    def __str__(self) -> str:
        return self.name
    
    def total_perks(self):
        return self.perks.count()
    
    def rating(self):
        count = self.reviews.count()
        if count == 0:
            return 0
        else: 
            total_rating = 0
            for review in self.reviews.all().values("rating"):
                total_rating += review["rating"]
            return round(total_rating / count, 2)
        
    def booking_rate(self):
        if self.max_participants != None:
            head_count = 0
            for booking in self.bookings.all().values("guests"):
                head_count += booking["guests"]
            return f"{head_count} out of {self.max_participants} booked"
        else:
            return "No attendee cap"

class Perk(CommonModel):

    """What is included on an Experience"""

    name = models.CharField(
        max_length=100,
    )
    details = models.CharField(
        max_length=250,
        blank=True,
        default="",
    )
    explanation = models.TextField(
        blank=True,
        default="",
    )

    def __str__(self) -> str:
        return self.name
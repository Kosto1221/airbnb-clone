from django.contrib import admin
from .models import Review

# Register your models here.
class WordFilter(admin.SimpleListFilter):

    title = "Filter by words!"

    parameter_name = "word"

    def lookups(self, request, model_admin):
        return [
            ("good", "Good"),
            ("great", "Great"),
            ("awesome", "Awesome"),
        ]
    
    def queryset(self, request, reviews):
        word = self.value()
        if word:
            return reviews.filter(payload__contains=word)
        else:
            return reviews
        
class ReputationFilter(admin.SimpleListFilter):

    title = "Filter by reputation!"

    parameter_name = "reputation"

    def lookups(self, request, model_admin):
        return [
            ("good", "Good"),
            ("bad", "Bad"),
        ]
    
    def queryset(self, request, reviews):
        reputation = self.value()
        if reputation == "good": 
            return reviews.filter(rating__gte=3)
        elif reputation == "bad":
            return reviews.filter(rating__lt=3)
        else:
            return reviews
    
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    
    list_display = (
        "__str__",
        "payload",
    )

    list_filter = (
        WordFilter,
        ReputationFilter,
        "rating",
        "user__is_host",
        "room__category",
        "room__pet_friendly",
    )
    
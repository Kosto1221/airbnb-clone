from rest_framework.serializers import ModelSerializer
from .models import Perk, Experience
from rest_framework import serializers
from wishlists.models import Wishlist
from medias.serializers import PhotoSerializer, VideoSerializer
from users.serializers import TinyUserSerializer
from categories.serializers import CategorySerializer


class PerkSerializer(ModelSerializer):
    class Meta:
        model = Perk
        fields = "__all__"
    
class ExperienceDetailSerializer(ModelSerializer):

    host = TinyUserSerializer(read_only=True)
    category = CategorySerializer(
        read_only=True,
    )
    rating = serializers.SerializerMethodField()
    is_host = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    photos = PhotoSerializer(many=True, read_only=True)
    videos = VideoSerializer(read_only=True)
    booking_rate = serializers.SerializerMethodField()

    class Meta:
        model = Experience
        fields = "__all__"

    def get_rating(self, experience):
        print(self.context)
        return experience.rating()
    
    def get_booking_rate(self, experience):
        return experience.booking_rate()
    
    def get_is_host(self, experience):
        request = self.context['request']
        return experience.host == request.user

    def get_is_liked(self, experience):
        request = self.context['request']
        return Wishlist.objects.filter(user=request.user, experiences__pk=experience.pk).exists()

class ExperienceListSerializer(ModelSerializer):

    rating = serializers.SerializerMethodField()
    is_host = serializers.SerializerMethodField()
    photos = PhotoSerializer(many=True, read_only=True)
    videos = VideoSerializer(read_only=True)

    class Meta:
        model = Experience
        fields = (
            "pk",
            "name",
            "country",
            "city",
            "price",
            "rating",
            "is_host",
            "photos",
            "videos"
        )

    def get_rating(self, experience):
        return experience.rating()

    def get_is_host(self, experience):
        request = self.context['request']
        return experience.host == request.user
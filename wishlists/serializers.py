from rest_framework.serializers import ModelSerializer
from rooms.serializers import RoomListSerializer
from experiences.serializers import ExperienceListSerializer
from .models import Wishlist


class WishlistSerializer(ModelSerializer):

    rooms = RoomListSerializer(
        many=True,
        read_only=True,
    )

    experiences = ExperienceListSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Wishlist
        fields = (
            "pk",
            "name",
            "rooms",
            "experiences"
        )
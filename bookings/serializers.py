from rest_framework import serializers
from .models import Booking
from django.utils import timezone
from django.db.models import Sum
from users.serializers import TinyUserSerializer

class CreateRoomBookingSerializer(serializers.ModelSerializer):

    check_in = serializers.DateField()
    check_out = serializers.DateField()

    class Meta:
        model = Booking
        fields = (
            "check_in",
            "check_out",
            "guests",
        )

    def validate_check_in(self, value):
        now = timezone.localtime(timezone.now()).date()
        if now > value:
            raise serializers.ValidationError("Can't book in the past!")
        return value
    
    def validate_check_out(self, value):
        now = timezone.localtime(timezone.now()).date()
        if now > value:
            raise serializers.ValidationError("Can't book in the past!")
        return value
    
    def validate(self, data):
        if data["check_out"] <= data["check_in"]:
            raise serializers.ValidationError("Check in should be smaller than check out.") 
        if Booking.objects.filter(
            check_in__lte=data["check_out"],
            check_out__gte=data["check_in"]
        ).exists():
            raise serializers.ValidationError("Those (or some) of those dates are already taken.")
        return data

class CreateExperienceBookingSerializer(serializers.ModelSerializer):

    experience_time = serializers.DateTimeField()

    class Meta:
        model = Booking
        fields = (
            "experience_time",
            "guests",
        )
    
    def validate(self, data):
        experience = self.context.get("experience")
        experience_time = data.get("experience_time")
        if experience_time:
            if timezone.is_naive(experience_time):
                experience_time = timezone.make_aware(experience_time)
                data["experience_time"] = experience_time

            start_datetime = timezone.make_aware(
                timezone.datetime.combine(experience.event_date, experience.start)
            )
            end_datetime = timezone.make_aware(
                timezone.datetime.combine(experience.event_date, experience.end)
            )

            if not (start_datetime <= experience_time <= end_datetime):
                raise serializers.ValidationError(
                    f"Experience time must be between {experience.start} and {experience.end}."
                )
        guest_count = data.get("guests")   
        if experience.max_participants is not None:
            current_guest_count = Booking.objects.filter(
                experience=experience
            ).aggregate(total=Sum('guests'))['total'] or 0
            if current_guest_count + guest_count > experience.max_participants:
                raise serializers.ValidationError(
                    f"Booking exceeds the maximum participants limit ({experience.max_participants})."
                )    
        return data


class PublicBookingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Booking
        fields = (
            "pk",
            "check_in",
            "check_out",
            "experience_time",
            "guests",
        )

class ExperienceBookingDetailSerializer(serializers.ModelSerializer):

    user = TinyUserSerializer(read_only=True)

    class Meta:
        model = Booking
        exclude = ("room", "check_in", "check_out", "kind", "experience")
from django.conf import settings
from rest_framework.views import APIView
from .models import Perk, Experience
from .serializers import PerkSerializer
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework.status import HTTP_204_NO_CONTENT
from django.conf import settings
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.exceptions import NotFound, ParseError, PermissionDenied
from categories.models import Category
from django.db import transaction
from . import serializers
from django.utils import timezone
from bookings.models import Booking
from bookings.serializers import PublicBookingSerializer, CreateExperienceBookingSerializer, ExperienceBookingDetailSerializer
# Create your views here.

class Perks(APIView):

    def get(self, request):
        all_perks = Perk.objects.all()
        serializer = PerkSerializer(all_perks, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PerkSerializer(data=request.data)
        if serializer.is_valid():
            perk = serializer.save()  # Save the instance
            return Response(PerkSerializer(perk).data) 
        else:
            return Response(serializer.errors)

class PerkDetail(APIView):

    def get_object(self, pk):
        try:
            return Perk.objects.get(pk=pk)
        except Perk.DoesNotExist:
            raise  NotFound

    def get(self, request, pk):
        perk = self.get_object(pk)
        serializer = PerkSerializer(perk)
        return Response(serializer.data)

    def put(self, request, pk):
        perk = self.get_object(pk)
        serializer = PerkSerializer(perk, data=request.data, partial=True)
        if serializer.is_valid():
            updated_perk = serializer.save()
            return Response(PerkSerializer(updated_perk).data)
        else:
            return Response(serializer.errors)

    def delete(self, request, pk):
        perk = self.get_object(pk)
        perk.delete()
        return Response(status=HTTP_204_NO_CONTENT)
    
class Experiences(APIView):

    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get(self, request):
        try:
            page = request.query_params.get('page', 1)
            page = int(page)
        except ValueError:
            page = 1
        page_size = settings.PAGE_SIZE
        start = (page -1) * page_size
        end = start + page_size
        all_experiences = Experience.objects.all()
        serializer =serializers.ExperienceListSerializer(all_experiences[start:end], many=True, context={"request": request},)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = serializers.ExperienceDetailSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            category_pk = request.data.get("category")
            if not category_pk:
                raise ParseError("Category is required")
            try:
                category = Category.objects.get(pk=category_pk)
                if category.kind == Category.CategoryKindChoices.ROOMS: 
                    raise ParseError("The category kind should be 'experiences'")
            except Category.DoesNotExist:
                raise ParseError("Category not found")
            try:
                with transaction.atomic():
                    experience = serializer.save(
                        owner = request.user,
                        category=category,
                    )
                    perks = request.data.get("perks")
                    for perk_pk in perks:
                        perk = Perk.objects.get(pk=perk_pk)
                        experience.perks.add(perk)
                    serializer = serializers.ExperienceDetailSerializer(experience, context={"request": request})
                    return Response(serializer.data)
            except Exception:
                raise ParseError("Experience not found")
        else:
            return Response(serializer.errors)


class ExperienceDetail(APIView):

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self, pk):
        try:
            return Experience.objects.get(pk=pk)
        except Experience.DoesNotExist:
            raise NotFound
        
    def get(self, request, pk):
        experience = self.get_object(pk)
        serializer = serializers.ExperienceDetailSerializer(experience, context={"request": request},)
        return Response(serializer.data)

    def put(self, request, pk):
        experience = self.get_object(pk)
        if experience.host != request.user:
            raise PermissionDenied
        serializer = serializers.ExperienceDetailSerializer(
            experience,
            data=request.data,
            partial=True,
        )
        if serializer.is_valid():
            category_pk = request.data.get("category")
            perks = request.data.get("perks")
            with transaction.atomic():
                if category_pk:
                    category = Category.objects.get(pk=category_pk)
                    if category.kind == Category.CategoryKindChoices.ROOMS:
                         raise ParseError("The category kind should be 'experiences'")
                    experience.category = category
                if perks:
                    try:
                        for perk_pk in perks:
                            perk = Perk.objects.get(pk=perk_pk)
                            experience.perks.add(perk)
                    except Perk.DoesNotExist:
                        raise ParseError("Perk not found")
                experience = serializer.save()
            return Response(serializers.ExperienceDetailSerializer(experience, context={"request": request}).data)
        return Response(serializer.errors)
        
    def delete(self, request, pk):
        experience = self.get_object(pk)
        if experience.host != request.user:
            raise PermissionDenied
        experience.delete()
        return Response(status=HTTP_204_NO_CONTENT)

class ExperiencePerks(APIView):

    def get_object(self, pk):
        try:
            return Experience.objects.get(pk=pk)
        except Experience.DoesNotExist:
            raise NotFound
        
    def get(self, request, pk):
        try:
            page = request.query_params.get("page",1)
            page = int(page)
        except ValueError:
            page = 1
        page_size = settings.PAGE_SIZE
        start = (page -1) * page_size
        end = start + page_size
        experience = self.get_object(pk)
        serializer = serializers.PerkSerializer(
            experience.perks.all()[start:end],
            many=True
        )
        return Response(serializer.data)
    
    # page
    
class ExperienceBookings(APIView):

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self, pk):
        try:
            return Experience.objects.get(pk=pk)
        except:
            raise NotFound

    def get(self, request, pk):
        try:
            page = request.query_params.get('page', 1)
            page = int(page)
        except ValueError:
            page = 1
        page_size = settings.PAGE_SIZE
        start = (page -1) * page_size
        end = start + page_size
        experience = self.get_object(pk)
        now = timezone.localtime(timezone.now())
        bookings = Booking.objects.filter(experience=experience, kind=Booking.BookingKindChoices.EXPERIENCE, experience_time__gt=now,)
        serializer = PublicBookingSerializer(bookings[start:end], many=True)
        return Response(serializer.data)
    
    def post(self, request, pk):
        experience = self.get_object(pk)
        serializer = CreateExperienceBookingSerializer(data=request.data, context={"experience": experience})
        if serializer.is_valid():
            booking = serializer.save(experience=experience, user=request.user, kind=Booking.BookingKindChoices.EXPERIENCE,)
            serializer = PublicBookingSerializer(booking)
            return Response(serializer.data)
        else:
            return Response(serializer.errors)
        
class ExperienceBookingDetail(APIView):

    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Experience.objects.get(pk=pk)
        except:
            raise NotFound
        
    def get(self, request, pk, booking_pk):
        experience = self.get_object(pk)
        booking = Booking.objects.get(experience=experience, pk=booking_pk)
        serializer = ExperienceBookingDetailSerializer(booking)
        return Response(serializer.data)
    
    def put(self, request, pk, booking_pk):
        experience = self.get_object(pk)
        booking = Booking.objects.get(experience=experience, pk=booking_pk)
        if booking.user != request.user:
            raise PermissionDenied
        serializer = ExperienceBookingDetailSerializer(
            booking,
            data=request.data,
            partial=True,
        )
        if serializer.is_valid():
            booking = serializer.save()
            serializer = ExperienceBookingDetailSerializer(booking)
            return Response(serializer.data)
        return Response(serializer.errors)

    def delete(self, request, pk, booking_pk):
        experience = self.get_object(pk)
        booking = Booking.objects.get(experience=experience, pk=booking_pk)
        if booking.user != request.user:
            raise PermissionDenied
        booking.delete()
        return Response(status=HTTP_204_NO_CONTENT)


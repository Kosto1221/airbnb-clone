import jwt
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from . import serializers
from rest_framework.exceptions import ParseError, NotFound
from .models import User
import requests

# Create your views here.
class Me(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = serializers.PrivateUserSerializer(user).data
        return Response(serializer)
    
    def put(self, request):
        user = request.user
        serializer = serializers.PrivateUserSerializer(
            user,
            data=request.data,
            partial=True,
        )
        if serializer.is_valid():
            user = serializer.save()
            serializer = serializers.PrivateUserSerializer(user)
            return Response(serializer.data)
        else:
            return Response(serializer.errors)

class Users(APIView):
    def post(self, request):
        password = request.data.get("password")
        if not password:
            raise ParseError
        serializer = serializers.PrivateUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.set_password(password)
            user.save()
            serializer = serializers.PrivateUserSerializer(user)
            return Response(serializer.data)
        else:
            return Response(serializer.errors)
        
class PublicUser(APIView):

    def get(self, request, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise NotFound
        serializer = serializers.PrivateUserSerializer(user)
        return Response(serializer.data)
    
    # bigger public userserializer how many reviews how many houses i have see the countty i travelled to reviews about me(user)
    # get /users/@username/reviews challenge 2.2

class ChangePassword(APIView):

    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        if not old_password or not new_password:
            raise ParseError
        if user.check_password(old_password):
            user.set_password(new_password)
            user.save()
            return Response(status=status.HTTP_200_OK)
        else:
            raise ParseError
        
class LogIn(APIView):

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        if not username or not password:
            raise ParseError
        user = authenticate(request, username=username, password=password,)
        if user:
            login(request, user)
            return Response({"ok": "Welcome!"})
        else:
            return Response({"error": "wrong password"}, status=401)
        
class LogOut(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"ok":"bye!"})
    

class JWTLogIn(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        if not username or not password:
            raise ParseError
        user = authenticate(
            request,
            username=username,
            password=password,
        )
        if user:
            token = jwt.encode(
                {"pk": user.pk},
                settings.SECRET_KEY,
                algorithm="HS256",
            )
            return Response({"token": token})
        else:
            return Response({"error": "wrong password"})
        
class GithubLogIn(APIView):
    
    def post(self, request):
        try:
            code = request.data.get('code')
            access_token = requests.post(f"https://github.com/login/oauth/access_token?code={code}&client_id=Ov23lipfR84wF56lANzd&client_secret={settings.GH_SECRET}", headers={"Accept": "application/json"})
            access_token = access_token.json().get('access_token')
            user_data = requests.get("https://api.github.com/user", headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"})
            user_data = user_data.json()
            user_emails = requests.get("https://api.github.com/user/emails", headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"})
            user_emails = user_emails.json()
            try:
                user = User.objects.get(email=user_emails[0]['email'])
                login(request, user)
                return Response(status=status.HTTP_200_OK)
            except User.DoesNotExist:
                user = User.objects.create(
                    username=user_data.get('login')+"_"+str(user_data.get('id')),
                    email=user_emails[0]['email'],
                    name=user_data.get('name') if user_data.get('name') else 'No Name',
                    avatar=user_data.get('avatar_url')
                )
                user.set_unusable_password()
                user.save()
                login(request, user)
                return Response(status=status.HTTP_200_OK)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
class KakaoLogIn(APIView):

    def post(self, request):
        try:
            code = request.data.get('code')
            access_token = requests.post(
                "https://kauth.kakao.com/oauth/token",
                headers= {"Content-Type": "application/x-www-form-urlencoded"},
                data={"grant_type": "authorization_code", "client_id":"92428ebf5d488b4ad1c7f13f9dc71c5c", "redirect_uri":"http://localhost:5173/social/kakao", "code": code}
            )
            access_token = access_token.json().get("access_token")
            user_data = requests.get(
                "https://kapi.kakao.com/v2/user/me",
                headers={"Authorization":f"Bearer {access_token}", "Content-type":"application/x-www-form-urlencoded;charset=utf-8"}
            )
            user_data = user_data.json()
            kakao_account = user_data.get("kakao_account")
            profile = kakao_account.get("profile")
            try:
                user = User.objects.get(email=kakao_account.get('email'))
                login(request, user)
                return Response(status=status.HTTP_200_OK)
            except User.DoesNotExist:
                user = User.objects.create(
                    email=kakao_account.get('email'),
                    username=profile.get('nickname'),
                    name=profile.get('nickname'),
                    avatar=profile.get('profile_image_url')
                )
                user.set_unusable_password()
                user.save()
                login(request, user)
                return Response(status=status.HTTP_200_OK)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)


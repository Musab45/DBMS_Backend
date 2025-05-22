from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from .models import Profile, Post, Comment, Message
from .serializers import (
    UserSerializer, ProfileSerializer, PostSerializer,
    CommentSerializer, MessageSerializer, RegisterSerializer
)
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.db.models import Q, Max

# Create your views here.

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=['get'])
    def profile(self, request, pk=None):
        user = self.get_object()
        profile = get_object_or_404(Profile, user=user)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def posts(self, request, pk=None):
        user = self.get_object()
        posts = Post.objects.filter(author=user).order_by('-created_at')
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def liked_posts(self, request, pk=None):
        user = self.get_object()
        posts = Post.objects.filter(likes=user).order_by('-created_at')
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)

class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=['post'])
    def follow(self, request, pk=None):
        profile = self.get_object()
        user_profile = request.user.profile
        
        if profile == user_profile:
            return Response(
                {"error": "You cannot follow yourself"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if profile in user_profile.following.all():
            user_profile.following.remove(profile)
            return Response({"status": "unfollowed"})
        else:
            user_profile.following.add(profile)
            return Response({"status": "followed"})

    @action(detail=True, methods=['get'])
    def followers(self, request, pk=None):
        profile = self.get_object()
        followers = profile.followers.all()
        serializer = ProfileSerializer(followers, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def following(self, request, pk=None):
        profile = self.get_object()
        following = profile.user.following.all()
        serializer = ProfileSerializer(following, many=True)
        return Response(serializer.data)

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        post = self.get_object()
        if request.user in post.likes.all():
            post.likes.remove(request.user)
            return Response({"status": "unliked"})
        else:
            post.likes.add(request.user)
            return Response({"status": "liked"})

    @action(detail=True, methods=['post'])
    def repost(self, request, pk=None):
        post = self.get_object()
        if request.user in post.reposts.all():
            post.reposts.remove(request.user)
            return Response({"status": "unreposted"})
        else:
            post.reposts.add(request.user)
            return Response({"status": "reposted"})

    @action(detail=False, methods=['get'])
    def feed(self, request):
        # Get the profiles that the current user follows
        following_profiles = request.user.profile.following.all()
        
        # If user follows no one, return empty list immediately
        if not following_profiles.exists():
            return Response([])
            
        # Get the users associated with those profiles
        following_users = User.objects.filter(profile__in=following_profiles)
        
        # Get posts from those users
        posts = Post.objects.filter(author__in=following_users).order_by('-created_at')
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def explore(self, request):
        # Get the profiles that the current user follows
        following_profiles = request.user.profile.following.all()
        
        # If user follows no one, show all posts in explore
        if not following_profiles.exists():
            posts = Post.objects.all().order_by('-created_at')
        else:
            # Get the users associated with those profiles
            following_users = User.objects.filter(profile__in=following_profiles)
            # Get posts from users that are not in the following list
            posts = Post.objects.exclude(author__in=following_users).order_by('-created_at')
            
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        comment = self.get_object()
        if request.user in comment.likes.all():
            comment.likes.remove(request.user)
            return Response({"status": "unliked"})
        else:
            comment.likes.add(request.user)
            return Response({"status": "liked"})

    @action(detail=True, methods=['post'])
    def reply(self, request, pk=None):
        parent_comment = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(
            author=request.user,
            post=parent_comment.post,
            parent=parent_comment
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

    @action(detail=False, methods=['get'])
    def conversations(self, request):
        user = request.user
        # Get all users this user has messaged with
        messages = Message.objects.filter(Q(sender=user) | Q(receiver=user))
        # Find the latest message for each conversation
        convo_map = {}
        for msg in messages:
            other_user = msg.receiver if msg.sender == user else msg.sender
            if other_user.id not in convo_map or msg.created_at > convo_map[other_user.id].created_at:
                convo_map[other_user.id] = msg
        # Build response
        result = []
        for other_user_id, last_msg in convo_map.items():
            other_user = last_msg.receiver if last_msg.sender == user else last_msg.sender
            result.append({
                'user': UserSerializer(other_user).data,
                'last_message': MessageSerializer(last_msg).data
            })
        return Response(result)

    @action(detail=False, methods=['get'], url_path='with/(?P<user_id>[^/.]+)')
    def with_user(self, request, user_id=None):
        user = request.user
        try:
            other_user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=404)
        messages = Message.objects.filter(
            (Q(sender=user) & Q(receiver=other_user)) |
            (Q(sender=other_user) & Q(receiver=user))
        ).order_by('created_at')
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = Message.objects.filter(receiver=request.user, is_read=False).count()
        return Response({"unread_count": count})

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        message = self.get_object()
        if message.receiver == request.user:
            message.is_read = True
            message.save()
            return Response({"status": "marked as read"})
        return Response(
            {"error": "You can only mark messages sent to you as read"},
            status=status.HTTP_403_FORBIDDEN
        )

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

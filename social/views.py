from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from .models import Profile, Post, Comment, Message, Follow
from .serializers import (
    UserSerializer, ProfileSerializer, PostSerializer,
    CommentSerializer, MessageSerializer, RegisterSerializer
)
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.db.models import Q, Max
from rest_framework.pagination import PageNumberPagination
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

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
    
    # Add filtering and search backends
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    
    # Configure search fields
    search_fields = ['username', 'first_name', 'last_name', 'email']
    
    # Configure filterable fields
    filterset_fields = ['is_active', 'is_staff']
    
    # Configure ordering fields
    ordering_fields = ['username', 'date_joined', 'last_login']
    ordering = ['-date_joined']  # Default ordering

    def get_queryset(self):
        """
        Override get_queryset to add custom filtering logic
        """
        queryset = User.objects.all()
        
        # Custom search parameter handling
        search_query = self.request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                Q(username__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query)
            )
        
        # Additional custom filters
        username = self.request.query_params.get('username', None)
        if username:
            queryset = queryset.filter(username__icontains=username)
            
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset

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

    @action(detail=True, methods=['get'])
    def reposted_posts(self, request, pk=None):
        user = self.get_object()
        posts = Post.objects.filter(reposts=user).order_by('-created_at')
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)

class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=['get'])
    def followers(self, request, pk=None):
        try:
            profile = self.get_object()
            # Get users who are following this profile's user
            followers = User.objects.filter(following_relationships__following=profile.user)
            # Get the profiles of these users
            follower_profiles = Profile.objects.filter(user__in=followers)
            
            serializer = ProfileSerializer(follower_profiles, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def following(self, request, pk=None):
        profile = self.get_object()
        # Get users that this profile's user is following
        following_users = User.objects.filter(follower_relationships__follower=profile.user)
        # Now get the profiles of these users
        following_profiles = Profile.objects.filter(user__in=following_users)
        serializer = ProfileSerializer(following_profiles, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def follow(self, request, pk=None):
        profile_to_follow = self.get_object()
        user_following = request.user

        # Prevent following yourself
        if user_following == profile_to_follow.user:
            return Response({"detail": "You cannot follow yourself."}, status=status.HTTP_400_BAD_REQUEST)

        follow_instance, created = Follow.objects.get_or_create(
            follower=user_following,
            following=profile_to_follow.user
        )

        if created:
            return Response({"status": "followed"}, status=status.HTTP_200_OK)
        else:
            # If it already exists, it means the user was already following, so unfollow
            follow_instance.delete()
            return Response({"status": "unfollowed"}, status=status.HTTP_200_OK)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['get'])
    def like(self, request, pk=None):
        try:
            post = self.get_object()
            is_liked = post.likes.filter(id=request.user.id).exists()
            return Response({
                'status': 'liked' if is_liked else 'unliked'
            })
        except Post.DoesNotExist:
            return Response(
                {'detail': 'Post not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        try:
            post = self.get_object()
            if request.user in post.likes.all():
                post.likes.remove(request.user)
                return Response({'status': 'unliked'})
            else:
                post.likes.add(request.user)
                return Response({'status': 'liked'})
        except Post.DoesNotExist:
            return Response(
                {'detail': 'Post not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

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
        try:
            # Get users that the current user follows
            following_users = User.objects.filter(
                follower_relationships__follower=request.user
            )
            
            # Get posts from users that the current user follows
            posts = Post.objects.filter(
                author__in=following_users
            ).order_by('-created_at')
            
            # Apply pagination
            page = self.paginate_queryset(posts)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(posts, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def explore(self, request):
        try:
            # Get users that the current user follows
            following_users = User.objects.filter(
                follower_relationships__follower=request.user
            )
            
            # Get posts from users that the current user doesn't follow
            # Exclude the current user's posts as well
            posts = Post.objects.exclude(
                author__in=following_users
            ).exclude(
                author=request.user
            ).order_by('-created_at')
            
            # Apply pagination
            page = self.paginate_queryset(posts)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(posts, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
    pagination_class = StandardResultsSetPagination

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

    def update(self, request, *args, **kwargs):
        message = self.get_object()
        # Only allow sender to edit their own messages
        if message.sender != request.user:
            return Response(
                {"error": "You can only edit your own messages"},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        message = self.get_object()
        # Only allow sender to edit their own messages
        if message.sender != request.user:
            return Response(
                {"error": "You can only edit your own messages"},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        message = self.get_object()
        # Only allow sender to delete their own messages
        if message.sender != request.user:
            return Response(
                {"error": "You can only delete your own messages"},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

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
        ).order_by('-created_at')  # Descending order for newest first
        
        # Apply pagination
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
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

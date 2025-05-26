from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import Profile, Post, Comment, Message, Follow
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'email', 'first_name', 'last_name')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user

class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ('id', 'username', 'bio', 'profile_picture', 'followers_count', 'following_count', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_followers_count(self, obj):
        return obj.followers_count or 0

    def get_following_count(self, obj):
        return obj.following_count or 0

    def to_representation(self, instance):
        """
        Ensure all fields are present and properly typed
        """
        data = super().to_representation(instance)
        # Ensure required fields have default values
        data['id'] = instance.id
        data['followers_count'] = self.get_followers_count(instance)
        data['following_count'] = self.get_following_count(instance)
        data['bio'] = data.get('bio') or ''
        return data

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'profile')
        read_only_fields = ('id',)

class CommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='author.username', read_only=True)
    likes_count = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ('id', 'post', 'username', 'content', 'created_at', 'updated_at', 'likes_count', 'replies')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_replies(self, obj):
        replies = Comment.objects.filter(parent=obj)
        return CommentSerializer(replies, many=True).data

class PostSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)
    author_user_id = serializers.ReadOnlyField(source='author.id')
    author_profile_id = serializers.ReadOnlyField(source='author.profile.id')
    likes_count = serializers.SerializerMethodField()
    reposts_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ('id', 'author_username', 'author_user_id', 'author_profile_id', 'content', 'image', 
                 'created_at', 'updated_at', 'likes_count', 'reposts_count', 'comments_count', 
                 'comments', 'is_liked')
        read_only_fields = ('id', 'author_username', 'author_user_id', 'author_profile_id', 
                          'created_at', 'updated_at', 'is_liked')

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_reposts_count(self, obj):
        return obj.reposts.count()

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(id=request.user.id).exists()
        return False

    def get_comments(self, obj):
        # Only get top-level comments (comments without parents)
        comments = Comment.objects.filter(post=obj, parent=None)
        return CommentSerializer(comments, many=True).data

    def to_representation(self, instance):
        """
        Ensure all author-related fields are present and non-null
        """
        data = super().to_representation(instance)
        # Ensure author fields are present
        if not data.get('author_username'):
            data['author_username'] = instance.author.username
        if not data.get('author_user_id'):
            data['author_user_id'] = instance.author.id
        if not data.get('author_profile_id'):
            data['author_profile_id'] = instance.author.profile.id
        return data

class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    receiver_username = serializers.CharField(source='receiver.username', read_only=True)

    class Meta:
        model = Message
        fields = ('id', 'sender', 'sender_username', 'receiver', 'receiver_username', 
                 'content', 'created_at', 'is_read')
        read_only_fields = ('id', 'created_at')

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        # Use the updated UserSerializer which includes the ProfileSerializer
        data['user'] = UserSerializer(self.user).data
        return data 
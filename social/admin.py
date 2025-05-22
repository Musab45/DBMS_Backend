from django.contrib import admin
from .models import Profile, Post, Comment, Message

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'created_at', 'updated_at')
    search_fields = ('user__username', 'bio')
    list_filter = ('created_at', 'updated_at')

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('author', 'content', 'created_at', 'updated_at', 'likes_count', 'reposts_count')
    search_fields = ('author__username', 'content')
    list_filter = ('created_at', 'updated_at')
    
    def likes_count(self, obj):
        return obj.likes.count()
    likes_count.short_description = 'Likes'
    
    def reposts_count(self, obj):
        return obj.reposts.count()
    reposts_count.short_description = 'Reposts'

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'content', 'created_at', 'updated_at', 'likes_count')
    search_fields = ('author__username', 'content', 'post__content')
    list_filter = ('created_at', 'updated_at')
    
    def likes_count(self, obj):
        return obj.likes.count()
    likes_count.short_description = 'Likes'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'content', 'created_at', 'is_read')
    search_fields = ('sender__username', 'receiver__username', 'content')
    list_filter = ('created_at', 'is_read')

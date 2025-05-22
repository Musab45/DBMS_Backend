# Frontend Implementation Guide: Feed and Explore Pages

## API Endpoints

### Feed Endpoint
```
GET /api/posts/feed/
Headers: 
  - Authorization: Bearer <access_token>
```
- Shows posts from users that the current user follows
- Returns empty list if user doesn't follow anyone
- Posts are ordered by creation date (newest first)

### Explore Endpoint
```
GET /api/posts/explore/
Headers:
  - Authorization: Bearer <access_token>
```
- Shows posts from users that the current user doesn't follow
- Returns empty list if there are no posts from non-followed users
- Posts are ordered by creation date (newest first)

## Post Object Structure
```json
{
    "id": 123,
    "author_username": "testuser1",
    "author_user_id": 1,
    "author_profile_id": 1,
    "content": "This is a sample post.",
    "image": "image_url",
    "created_at": "2024-03-14T12:00:00Z",
    "updated_at": "2024-03-14T12:00:00Z",
    "likes_count": 5,
    "reposts_count": 1,
    "comments_count": 2,
    "comments": [...]
}
```

## Implementation Steps

### 1. Post Model
```dart
class Post {
  final int id;
  final String authorUsername;
  final int authorUserId;
  final int authorProfileId;
  final String content;
  final String? image;
  final DateTime createdAt;
  final DateTime updatedAt;
  final int likesCount;
  final int repostsCount;
  final int commentsCount;
  final List<Comment> comments;

  Post({
    required this.id,
    required this.authorUsername,
    required this.authorUserId,
    required this.authorProfileId,
    required this.content,
    this.image,
    required this.createdAt,
    required this.updatedAt,
    required this.likesCount,
    required this.repostsCount,
    required this.commentsCount,
    required this.comments,
  });

  factory Post.fromJson(Map<String, dynamic> json) {
    return Post(
      id: json['id'],
      authorUsername: json['author_username'],
      authorUserId: json['author_user_id'],
      authorProfileId: json['author_profile_id'],
      content: json['content'],
      image: json['image'],
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
      likesCount: json['likes_count'],
      repostsCount: json['reposts_count'],
      commentsCount: json['comments_count'],
      comments: (json['comments'] as List)
          .map((comment) => Comment.fromJson(comment))
          .toList(),
    );
  }
}
```

### 2. Feed Implementation

```dart
class FeedPage extends StatefulWidget {
  @override
  _FeedPageState createState() => _FeedPageState();
}

class _FeedPageState extends State<FeedPage> {
  List<Post> posts = [];
  bool isLoading = true;
  bool hasError = false;

  @override
  void initState() {
    super.initState();
    _loadFeed();
  }

  Future<void> _loadFeed() async {
    try {
      setState(() {
        isLoading = true;
        hasError = false;
      });

      final response = await http.get(
        Uri.parse('${Constants.apiUrl}/posts/feed/'),
        headers: {
          'Authorization': 'Bearer ${AuthManager.accessToken}',
        },
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        setState(() {
          posts = data.map((json) => Post.fromJson(json)).toList();
          isLoading = false;
        });
      } else {
        setState(() {
          hasError = true;
          isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        hasError = true;
        isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (isLoading) {
      return Center(child: CircularProgressIndicator());
    }

    if (hasError) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text('Error loading feed'),
            ElevatedButton(
              onPressed: _loadFeed,
              child: Text('Retry'),
            ),
          ],
        ),
      );
    }

    if (posts.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text('No posts in your feed'),
            Text('Follow some users to see their posts here'),
            ElevatedButton(
              onPressed: () {
                // Navigate to explore page
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => ExplorePage()),
                );
              },
              child: Text('Explore Posts'),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadFeed,
      child: ListView.builder(
        itemCount: posts.length,
        itemBuilder: (context, index) {
          final post = posts[index];
          return PostCard(
            post: post,
            isMyPost: post.authorUserId == AuthManager.currentUserId,
            onLike: () => _handleLike(post),
            onComment: () => _handleComment(post),
            onRepost: () => _handleRepost(post),
            onFollow: () => _handleFollow(post),
          );
        },
      ),
    );
  }
}
```

### 3. Explore Implementation

```dart
class ExplorePage extends StatefulWidget {
  @override
  _ExplorePageState createState() => _ExplorePageState();
}

class _ExplorePageState extends State<ExplorePage> {
  List<Post> posts = [];
  bool isLoading = true;
  bool hasError = false;

  @override
  void initState() {
    super.initState();
    _loadExplore();
  }

  Future<void> _loadExplore() async {
    try {
      setState(() {
        isLoading = true;
        hasError = false;
      });

      final response = await http.get(
        Uri.parse('${Constants.apiUrl}/posts/explore/'),
        headers: {
          'Authorization': 'Bearer ${AuthManager.accessToken}',
        },
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        setState(() {
          posts = data.map((json) => Post.fromJson(json)).toList();
          isLoading = false;
        });
      } else {
        setState(() {
          hasError = true;
          isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        hasError = true;
        isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (isLoading) {
      return Center(child: CircularProgressIndicator());
    }

    if (hasError) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text('Error loading explore'),
            ElevatedButton(
              onPressed: _loadExplore,
              child: Text('Retry'),
            ),
          ],
        ),
      );
    }

    if (posts.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text('No posts to explore'),
            Text('Check back later for new posts'),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadExplore,
      child: ListView.builder(
        itemCount: posts.length,
        itemBuilder: (context, index) {
          final post = posts[index];
          return PostCard(
            post: post,
            isMyPost: post.authorUserId == AuthManager.currentUserId,
            onLike: () => _handleLike(post),
            onComment: () => _handleComment(post),
            onRepost: () => _handleRepost(post),
            onFollow: () => _handleFollow(post),
          );
        },
      ),
    );
  }
}
```

### 4. PostCard Widget
```dart
class PostCard extends StatelessWidget {
  final Post post;
  final bool isMyPost;
  final VoidCallback onLike;
  final VoidCallback onComment;
  final VoidCallback onRepost;
  final VoidCallback onFollow;

  const PostCard({
    Key? key,
    required this.post,
    required this.isMyPost,
    required this.onLike,
    required this.onComment,
    required this.onRepost,
    required this.onFollow,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.all(8.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ListTile(
            leading: CircleAvatar(
              child: Text(post.authorUsername[0].toUpperCase()),
            ),
            title: Text(post.authorUsername),
            subtitle: Text(timeAgo(post.createdAt)),
            trailing: !isMyPost
                ? TextButton(
                    onPressed: onFollow,
                    child: Text('Follow'),
                  )
                : null,
          ),
          if (post.image != null)
            Image.network(
              post.image!,
              width: double.infinity,
              fit: BoxFit.cover,
            ),
          Padding(
            padding: EdgeInsets.all(8.0),
            child: Text(post.content),
          ),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              IconButton(
                icon: Icon(Icons.favorite),
                onPressed: onLike,
              ),
              Text('${post.likesCount}'),
              IconButton(
                icon: Icon(Icons.comment),
                onPressed: onComment,
              ),
              Text('${post.commentsCount}'),
              IconButton(
                icon: Icon(Icons.repeat),
                onPressed: onRepost,
              ),
              Text('${post.repostsCount}'),
            ],
          ),
        ],
      ),
    );
  }
}
```

## Important Notes

1. **Error Handling**
   - Always handle network errors and invalid responses
   - Show appropriate error messages to users
   - Provide retry functionality

2. **Loading States**
   - Show loading indicators while fetching data
   - Implement pull-to-refresh for both feed and explore

3. **Empty States**
   - Feed: Show message suggesting to follow users or explore posts
   - Explore: Show message when no posts are available

4. **Post Ownership**
   - Use `author_user_id` to determine if the current user is the post author
   - Show/hide appropriate actions based on ownership

5. **Follow Functionality**
   - Use `author_profile_id` for follow/unfollow actions
   - Update UI immediately after follow/unfollow
   - Consider moving followed users' posts from explore to feed

6. **Performance**
   - Implement pagination if needed
   - Cache posts locally
   - Optimize image loading

7. **Authentication**
   - Always include the access token in requests
   - Handle token expiration
   - Redirect to login if unauthorized

## Testing Checklist

- [ ] Feed loads posts from followed users
- [ ] Explore shows posts from non-followed users
- [ ] Pull-to-refresh works on both pages
- [ ] Error states are handled properly
- [ ] Empty states show appropriate messages
- [ ] Post actions (like, comment, repost) work
- [ ] Follow/unfollow functionality works
- [ ] Post ownership is correctly identified
- [ ] Images load properly
- [ ] Authentication is maintained
- [ ] UI is responsive and smooth 
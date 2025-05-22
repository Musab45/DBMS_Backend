# Social Media App Frontend Implementation Guide

## Table of Contents
1. [Authentication](#authentication)
2. [Posts & Feed](#posts--feed)
3. [User Interactions](#user-interactions)
4. [Messaging](#messaging)
5. [Profile Management](#profile-management)

## Authentication

### Login Screen
```dart
class LoginScreen extends StatefulWidget {
  @override
  _LoginScreenState createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  Future<void> _login() async {
    if (_formKey.currentState!.validate()) {
      try {
        final response = await http.post(
          Uri.parse('$baseUrl/api/auth/login/'),
          body: {
            'email': _emailController.text,
            'password': _passwordController.text,
          },
        );

        if (response.statusCode == 200) {
          final data = json.decode(response.body);
          // Store tokens
          await storage.write(key: 'access_token', value: data['access']);
          await storage.write(key: 'refresh_token', value: data['refresh']);
          // Navigate to home
          Navigator.pushReplacementNamed(context, '/home');
        } else {
          // Show error
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Login failed')),
          );
        }
      } catch (e) {
        // Handle error
      }
    }
  }
}
```

### Sign Up Screen
```dart
class SignUpScreen extends StatefulWidget {
  @override
  _SignUpScreenState createState() => _SignUpScreenState();
}

class _SignUpScreenState extends State<SignUpScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _usernameController = TextEditingController();

  Future<void> _signUp() async {
    if (_formKey.currentState!.validate()) {
      try {
        final response = await http.post(
          Uri.parse('$baseUrl/api/auth/register/'),
          body: {
            'email': _emailController.text,
            'password': _passwordController.text,
            'username': _usernameController.text,
          },
        );

        if (response.statusCode == 201) {
          // Navigate to login
          Navigator.pushReplacementNamed(context, '/login');
        } else {
          // Show error
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Registration failed')),
          );
        }
      } catch (e) {
        // Handle error
      }
    }
  }
}
```

## Posts & Feed

### Feed Screen
```dart
class FeedScreen extends StatefulWidget {
  @override
  _FeedScreenState createState() => _FeedScreenState();
}

class _FeedScreenState extends State<FeedScreen> {
  List<Post> _posts = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadFeed();
  }

  Future<void> _loadFeed() async {
    try {
      final token = await storage.read(key: 'access_token');
      final response = await http.get(
        Uri.parse('$baseUrl/api/posts/feed/'),
        headers: {'Authorization': 'Bearer $token'},
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        setState(() {
          _posts = data.map((json) => Post.fromJson(json)).toList();
          _isLoading = false;
        });
      } else if (response.statusCode == 404) {
        // Feed is empty, load explore
        _loadExplore();
      }
    } catch (e) {
      // Handle error
    }
  }

  Future<void> _loadExplore() async {
    try {
      final token = await storage.read(key: 'access_token');
      final response = await http.get(
        Uri.parse('$baseUrl/api/posts/explore/'),
        headers: {'Authorization': 'Bearer $token'},
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        setState(() {
          _posts = data.map((json) => Post.fromJson(json)).toList();
          _isLoading = false;
        });
      }
    } catch (e) {
      // Handle error
    }
  }
}
```

### Create Post
```dart
class CreatePostScreen extends StatefulWidget {
  @override
  _CreatePostScreenState createState() => _CreatePostScreenState();
}

class _CreatePostScreenState extends State<CreatePostScreen> {
  final _contentController = TextEditingController();
  File? _image;

  Future<void> _createPost() async {
    try {
      final token = await storage.read(key: 'access_token');
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/api/posts/'),
      );

      request.headers['Authorization'] = 'Bearer $token';
      request.fields['content'] = _contentController.text;

      if (_image != null) {
        request.files.add(
          await http.MultipartFile.fromPath('image', _image!.path),
        );
      }

      final response = await request.send();
      if (response.statusCode == 201) {
        Navigator.pop(context);
      }
    } catch (e) {
      // Handle error
    }
  }
}
```

## User Interactions

### Like/Unlike Post
```dart
Future<void> _toggleLike(String postId) async {
  try {
    final token = await storage.read(key: 'access_token');
    final response = await http.post(
      Uri.parse('$baseUrl/api/posts/$postId/like/'),
      headers: {'Authorization': 'Bearer $token'},
    );

    if (response.statusCode == 200) {
      // Update UI
      setState(() {
        // Update like status
      });
    }
  } catch (e) {
    // Handle error
  }
}
```

### Follow/Unfollow User
```dart
Future<void> _toggleFollow(String profileId) async {
  try {
    final token = await storage.read(key: 'access_token');
    final response = await http.post(
      Uri.parse('$baseUrl/api/profiles/$profileId/follow/'),
      headers: {'Authorization': 'Bearer $token'},
    );

    if (response.statusCode == 200) {
      // Update UI
      setState(() {
        // Update follow status
      });
    }
  } catch (e) {
    // Handle error
  }
}
```

## Messaging

### Chat List
```dart
class ChatListScreen extends StatefulWidget {
  @override
  _ChatListScreenState createState() => _ChatListScreenState();
}

class _ChatListScreenState extends State<ChatListScreen> {
  List<Chat> _chats = [];

  Future<void> _loadChats() async {
    try {
      final token = await storage.read(key: 'access_token');
      final response = await http.get(
        Uri.parse('$baseUrl/api/messages/chats/'),
        headers: {'Authorization': 'Bearer $token'},
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        setState(() {
          _chats = data.map((json) => Chat.fromJson(json)).toList();
        });
      }
    } catch (e) {
      // Handle error
    }
  }
}
```

### Chat Screen
```dart
class ChatScreen extends StatefulWidget {
  final String recipientId;
  
  @override
  _ChatScreenState createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _messageController = TextEditingController();
  List<Message> _messages = [];

  Future<void> _sendMessage() async {
    if (_messageController.text.isNotEmpty) {
      try {
        final token = await storage.read(key: 'access_token');
        final response = await http.post(
          Uri.parse('$baseUrl/api/messages/'),
          headers: {
            'Authorization': 'Bearer $token',
            'Content-Type': 'application/json',
          },
          body: json.encode({
            'recipient': widget.recipientId,
            'content': _messageController.text,
          }),
        );

        if (response.statusCode == 201) {
          _messageController.clear();
          _loadMessages();
        }
      } catch (e) {
        // Handle error
      }
    }
  }
}
```

## Profile Management

### Edit Profile
```dart
class EditProfileScreen extends StatefulWidget {
  @override
  _EditProfileScreenState createState() => _EditProfileScreenState();
}

class _EditProfileScreenState extends State<EditProfileScreen> {
  final _bioController = TextEditingController();
  File? _avatar;

  Future<void> _updateProfile() async {
    try {
      final token = await storage.read(key: 'access_token');
      var request = http.MultipartRequest(
        'PATCH',
        Uri.parse('$baseUrl/api/profiles/me/'),
      );

      request.headers['Authorization'] = 'Bearer $token';
      request.fields['bio'] = _bioController.text;

      if (_avatar != null) {
        request.files.add(
          await http.MultipartFile.fromPath('avatar', _avatar!.path),
        );
      }

      final response = await request.send();
      if (response.statusCode == 200) {
        Navigator.pop(context);
      }
    } catch (e) {
      // Handle error
    }
  }
}
```

## Best Practices

1. **Token Management**
   - Store tokens securely using `flutter_secure_storage`
   - Implement token refresh logic
   - Handle token expiration

2. **Error Handling**
   - Implement proper error handling for all API calls
   - Show user-friendly error messages
   - Handle network errors gracefully

3. **State Management**
   - Use Provider or Bloc for state management
   - Keep UI in sync with backend data
   - Implement proper loading states

4. **Image Handling**
   - Compress images before upload
   - Implement proper image caching
   - Handle image loading errors

5. **Real-time Updates**
   - Implement WebSocket for real-time messaging
   - Use polling for feed updates
   - Handle offline mode

6. **Security**
   - Never store sensitive data in shared preferences
   - Implement proper input validation
   - Handle user sessions securely

7. **Performance**
   - Implement pagination for lists
   - Use proper image loading techniques
   - Optimize network calls

8. **Testing**
   - Write unit tests for API calls
   - Implement UI tests
   - Test error scenarios

## Common Issues and Solutions

1. **Token Expiration**
   ```dart
   Future<void> _refreshToken() async {
     try {
       final refreshToken = await storage.read(key: 'refresh_token');
       final response = await http.post(
         Uri.parse('$baseUrl/api/auth/token/refresh/'),
         body: {'refresh': refreshToken},
       );

       if (response.statusCode == 200) {
         final data = json.decode(response.body);
         await storage.write(key: 'access_token', value: data['access']);
       } else {
         // Handle refresh failure
         await _logout();
       }
     } catch (e) {
       // Handle error
     }
   }
   ```

2. **Image Upload**
   ```dart
   Future<String?> _uploadImage(File image) async {
     try {
       final compressedImage = await FlutterImageCompress.compressAndGetFile(
         image.path,
         image.path.replaceAll('.jpg', '_compressed.jpg'),
         quality: 70,
       );

       if (compressedImage != null) {
         // Upload compressed image
         return compressedImage.path;
       }
     } catch (e) {
       // Handle error
     }
     return null;
   }
   ```

3. **Offline Support**
   ```dart
   Future<void> _syncData() async {
     try {
       final isOnline = await InternetConnectionChecker().hasConnection;
       if (isOnline) {
         // Sync offline changes
         await _syncPosts();
         await _syncMessages();
       }
     } catch (e) {
       // Handle error
     }
   }
   ```

## Dependencies

Add these to your `pubspec.yaml`:

```yaml
dependencies:
  http: ^1.1.0
  flutter_secure_storage: ^8.0.0
  image_picker: ^1.0.4
  flutter_image_compress: ^2.0.0
  provider: ^6.0.5
  cached_network_image: ^3.2.3
  web_socket_channel: ^2.4.0
  internet_connection_checker: ^1.0.0
```

## Getting Started

1. Clone the repository
2. Install dependencies: `flutter pub get`
3. Configure environment variables
4. Run the app: `flutter run`

## Testing

1. Unit Tests:
```dart
void main() {
  group('API Tests', () {
    test('Login success', () async {
      // Test login
    });

    test('Feed loading', () async {
      // Test feed
    });
  });
}
```

2. Widget Tests:
```dart
void main() {
  testWidgets('Login screen', (WidgetTester tester) async {
    // Test login screen
  });
}
```

## Deployment

1. Android:
   - Update `android/app/build.gradle`
   - Generate signed APK
   - Test on multiple devices

2. iOS:
   - Update `ios/Runner.xcworkspace`
   - Configure certificates
   - Test on simulator and devices

## Support

For any issues or questions:
1. Check the API documentation
2. Review error logs
3. Contact support team 
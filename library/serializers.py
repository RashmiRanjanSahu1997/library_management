from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Author, Genre, Book, BorrowRequest, BookReview

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'role')

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ('id', 'name', 'bio')

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ('id', 'name')

class BookListSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    genres = GenreSerializer(many=True, read_only=True)

    class Meta:
        model = Book
        fields = ('id', 'title', 'author', 'genres', 'ISBN', 'available_copies', 'total_copies')

class BookCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ('id', 'title', 'author', 'genres', 'ISBN', 'available_copies', 'total_copies')

class BorrowRequestSerializer(serializers.ModelSerializer):
    book = BookListSerializer(read_only=True)
    book_id = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all(), source='book', write_only=True)

    class Meta:
        model = BorrowRequest
        fields = ('id', 'book', 'book_id', 'status', 'requested_at', 'approved_at', 'returned_at')
        read_only_fields = ('status', 'requested_at', 'approved_at', 'returned_at')

class BookReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = BookReview
        fields = ('id', 'user', 'book', 'rating', 'comment', 'created_at')
        read_only_fields = ('user', 'created_at')
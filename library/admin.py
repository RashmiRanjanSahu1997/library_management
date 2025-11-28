from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Author, Genre, Book, BorrowRequest, BookReview

User = get_user_model()

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_staff')

admin.site.register(Author)
admin.site.register(Genre)
admin.site.register(Book)
admin.site.register(BorrowRequest)
admin.site.register(BookReview)
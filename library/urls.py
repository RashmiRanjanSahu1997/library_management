from rest_framework import routers
from django.urls import path, include
from .views import RegisterView, AuthorViewSet, GenreViewSet, BookViewSet, BorrowRequestViewSet

router = routers.DefaultRouter()
router.register(r'authors', AuthorViewSet, basename='author')
router.register(r'genres', GenreViewSet, basename='genre')
router.register(r'books', BookViewSet, basename='book')
router.register(r'borrow', BorrowRequestViewSet, basename='borrow')

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('', include(router.urls)),
]
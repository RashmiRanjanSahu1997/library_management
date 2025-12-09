from rest_framework import viewsets, generics, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from .models import Author, Genre, Book, BorrowRequest, BookReview
from .serializers import (
    RegisterSerializer, AuthorSerializer, GenreSerializer, BookListSerializer,
    BookCreateUpdateSerializer, BorrowRequestSerializer, BookReviewSerializer
)
from .permissions import IsLibrarian, IsOwnerOrReadOnly
from django.contrib.auth import get_user_model
from rest_framework.throttling import SimpleRateThrottle
from django.core.mail import send_mail
from django.conf import settings
User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['name']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsLibrarian]
        else:
            permission_classes = [IsAuthenticated]
        return [p() for p in permission_classes]

class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsLibrarian]
        else:
            permission_classes = [IsAuthenticated]
        return [p() for p in permission_classes]

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.prefetch_related('genres', 'author').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['author', 'genres', 'title']
    search_fields = ['title', 'author__name', 'ISBN']
    ordering_fields = ['title', 'available_copies']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return BookCreateUpdateSerializer
        return BookListSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsLibrarian]
        else:
            permission_classes = [IsAuthenticated]
        return [p() for p in permission_classes]

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def reviews(self, request, pk=None):
        book = self.get_object()
        reviews = book.reviews.all()
        serializer = BookReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def add_review(self, request, pk=None):
        book = self.get_object()
        serializer = BookReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, book=book)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class BorrowRequestViewSet(viewsets.ModelViewSet):
    serializer_class = BorrowRequestSerializer
    

    class BorrowRequestRateThrottle(SimpleRateThrottle):
        scope = 'borrow'
        rate = '5/day'

        def get_cache_key(self, request, view):
            if not request.user or not request.user.is_authenticated:
                return None
            return self.cache_format % {
                'scope': self.scope,
                'ident': request.user.pk
            }

    throttle_classes = [BorrowRequestRateThrottle]

    def get_queryset(self):
        user = self.request.user
        if user.is_librarian:
            return BorrowRequest.objects.select_related('book', 'user')
        return BorrowRequest.objects.select_related('book').filter(user=user)

    def create(self, request, *args, **kwargs):
        # throttle is applied automatically by DRF
        if request.user.role != User.STUDENT:
            return Response({'detail': 'Only students can create borrow requests'}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        br = serializer.save(user=request.user)
        return Response(self.get_serializer(br).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch'], permission_classes=(IsAuthenticated, IsLibrarian))
    def approve(self, request, pk=None):
        br = get_object_or_404(BorrowRequest, pk=pk)
        try:
            br.approve()
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        try:
            if br.user.email:
                subject = f"Your borrow request for '{br.book.title}' has been approved"
                message = (
                    f"Hello {br.user.email},"
                    f"Your request to borrow the book '{br.book.title}' has been approved."
                    f"Approved at: {br.approved_at}"
                    "Please collect the book from the library."
                    "Regards,Library Team"
                )

                send_mail(subject, message, getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@example.com'), [br.user.email])
        except Exception:
            pass

        return Response(self.get_serializer(br).data)

    @action(detail=True, methods=['patch'], permission_classes=(IsAuthenticated, IsLibrarian))
    def reject(self, request, pk=None):
        br = get_object_or_404(BorrowRequest, pk=pk)
        try:
            br.reject()
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        try:
            if br.user.email:
                subject = f"Your borrow request for '{br.book.title}' has been rejected"
                message = (
                    f"Hello {br.user.email},"
                    f"We are sorry to inform you that your request to borrow the book '{br.book.title}' was rejected."
                    f"If you have questions, please contact the library."
                    "Regards,Library Team"
                )
                send_mail(subject, message, getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@example.com'), [br.user.email])
        except Exception:
            pass

        return Response(self.get_serializer(br).data)

    @action(detail=True, methods=['patch'], permission_classes=(IsAuthenticated,))
    def return_book(self, request, pk=None):
        br = get_object_or_404(BorrowRequest, pk=pk)
        if request.user != br.user and not request.user.is_librarian():
            return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)
        try:
            br.mark_returned()
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(br).data)




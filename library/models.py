from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.exceptions import ValidationError

class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # no username required
    STUDENT = 'STUDENT'
    LIBRARIAN = 'LIBRARIAN'
    ROLE_CHOICES = ((STUDENT, 'Student'), (LIBRARIAN, 'Librarian'))
    # email = models.EmailField(unique=True)
    # USERNAME_FIELD = 'email'

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=STUDENT)

    def is_librarian(self):
        return self.role == self.LIBRARIAN

class Author(models.Model):
    name = models.CharField(max_length=255)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Book(models.Model):
    title = models.CharField(max_length=500)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='books')
    genres = models.ManyToManyField(Genre, related_name='books', blank=True)
    ISBN = models.CharField(max_length=20, blank=True, null=True)
    available_copies = models.PositiveIntegerField(default=1)
    total_copies = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.title

class BorrowRequest(models.Model):
    PENDING = 'PENDING'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    RETURNED = 'RETURNED'
    STATUS_CHOICES = ((PENDING, 'Pending'), (APPROVED, 'Approved'), (REJECTED, 'Rejected'), (RETURNED, 'Returned'))

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='borrow_requests')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='borrow_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    returned_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-requested_at']

    def approve(self):
        if self.status != self.PENDING:
            raise ValidationError("Only pending requests can be approved.")

        if self.book.available_copies <= 0:
            raise ValidationError("No copies available to approve this request.")

        self.status = self.APPROVED
        self.approved_at = timezone.now()
        self.save()

    def reject(self):
        if self.status != self.PENDING:
            raise ValidationError("Only pending requests can be rejected.")

        self.status = self.REJECTED
        self.save()

    def mark_returned(self):
        if self.status != self.APPROVED:
            raise ValidationError("Only approved requests can be returned.")

        self.status = self.RETURNED
        self.returned_at = timezone.now()
        self.save()

class BookReview(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'book')
        ordering = ['-created_at']
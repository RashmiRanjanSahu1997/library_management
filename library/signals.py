from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import BorrowRequest, Book
from django.utils import timezone

@receiver(post_save, sender=BorrowRequest)
def handle_borrow_request_save(sender, instance, created, **kwargs):
    if not created:
        if instance.status == BorrowRequest.APPROVED and instance.approved_at is None:
            instance.approved_at = timezone.now()
            instance.book.available_copies = max(0, instance.book.available_copies - 1)
            instance.book.save()
        elif instance.status == BorrowRequest.RETURNED and instance.returned_at is None:
            instance.returned_at = timezone.now()
            instance.book.available_copies = min(instance.book.total_copies, instance.book.available_copies + 1)
            instance.book.save()
"""
Yutuqlar: Expense yozilganda tekshiruv (dashboard'dan ajratilgan).
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from expenses.models import Expense
from .services import _grant_new_achievements

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Expense)
def on_expense_saved(sender, instance, created, **kwargs):
    """
    Har safar xarajat saqlanganda (yangi yoki tahrir) yutuqlarni tekshiramiz.
    first_expense, seven_day_streak va boshqalar shu paytda berilishi mumkin.
    """
    try:
        _grant_new_achievements(instance.user)
    except Exception as e:
        logger.exception("achievement check after expense save user_id=%s: %s", instance.user_id, e)

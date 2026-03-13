"""
Yutuqlar: Expense yozilganda tekshiruv (dashboard'dan ajratilgan).
"""
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from expenses.models import Expense
from .services import _grant_new_achievements, clear_insights_cache_for_user

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

    try:
        clear_insights_cache_for_user(instance.user, year=instance.date.year, month=instance.date.month)
    except Exception as e:
        logger.exception("insights cache clear after expense save user_id=%s: %s", instance.user_id, e)


@receiver(post_delete, sender=Expense)
def on_expense_deleted(sender, instance, **kwargs):
    """
    Xarajat o'chirilganda tegishli oy uchun insights cache'ini ham tozalaymiz.
    """
    try:
        clear_insights_cache_for_user(instance.user, year=instance.date.year, month=instance.date.month)
    except Exception as e:
        logger.exception("insights cache clear after expense delete user_id=%s: %s", instance.user_id, e)

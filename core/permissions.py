"""
Object-level authorization: barcha user-scoped resurslar uchun bir xil pattern.
Foydalanish: get_user_object_or_404(Expense, request.user, pk) yoki user_owns(obj, request.user).
"""
import logging
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied

logger = logging.getLogger(__name__)


def user_owns(obj, user) -> bool:
    """
    Obekt foydalanuvchiga tegishli ekanligini tekshiradi.
    Modelda user ForeignKey bo'lishi kerak (user=... yoki obj.user).
    """
    if not user or not user.is_authenticated:
        return False
    owner = getattr(obj, "user", None)
    return owner is not None and owner.pk == user.pk


def get_user_object_or_404(model, user, pk, field_name="user"):
    """
    Foydalanuvchiga tegishli obektni pk bo'yicha oladi.
    Topilmasa 404, boshqa user ga tegishli bo'lsa 404 (xavfsizlik: boshqaning ma'lumotini ko'rsatmaymiz).
    """
    if not user or not user.is_authenticated:
        raise PermissionDenied("Kirish talab qilinadi.")
    lookup = {"pk": pk, field_name: user}
    obj = get_object_or_404(model, **lookup)
    return obj

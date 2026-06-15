from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError('Telefon raqami majburiy')
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(phone, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    phone = models.CharField(max_length=20, unique=True, verbose_name='Telefon')
    full_name = models.CharField(max_length=100, blank=True, verbose_name='Ism familiya')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'Foydalanuvchi'
        verbose_name_plural = 'Foydalanuvchilar'

    def __str__(self):
        return self.phone


class TelegramBotUser(models.Model):
    chat_id = models.BigIntegerField(unique=True, verbose_name='Telegram chat ID')
    full_name = models.CharField(max_length=150, blank=True, verbose_name='Ism familiya')
    username = models.CharField(max_length=100, blank=True, verbose_name='Username')
    is_active = models.BooleanField(default=True, verbose_name='Faol')
    added_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='added_telegram_bot_users',
        verbose_name='Qo\'shgan admin',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Qo\'shilgan vaqt')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Yangilangan vaqt')

    class Meta:
        verbose_name = 'Telegram bot foydalanuvchisi'
        verbose_name_plural = 'Telegram bot foydalanuvchilari'
        ordering = ('-created_at',)

    def __str__(self):
        name = self.full_name or self.username or str(self.chat_id)
        return f'{name} ({self.chat_id})'

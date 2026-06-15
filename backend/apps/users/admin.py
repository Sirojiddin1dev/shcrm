from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import TelegramBotUser, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('phone', 'full_name', 'is_staff', 'is_active', 'created_at')
    list_filter = ('is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Shaxsiy malumot', {'fields': ('full_name',)}),
        ('Ruxsatlar', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('phone', 'password1', 'password2', 'full_name')}),
    )
    search_fields = ('phone', 'full_name')
    ordering = ('-created_at',)


@admin.register(TelegramBotUser)
class TelegramBotUserAdmin(admin.ModelAdmin):
    list_display = ('chat_id', 'full_name', 'username', 'is_active', 'added_by', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('chat_id', 'full_name', 'username')
    readonly_fields = ('created_at', 'updated_at')
    fields = ('chat_id', 'full_name', 'username', 'is_active', 'added_by', 'created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        if not obj.added_by_id and request.user.is_authenticated:
            obj.added_by = request.user
        super().save_model(request, obj, form, change)

from django.contrib import admin, messages
from django.conf import settings
from django.utils.html import format_html
from .models import Customer
from .services import send_debt_reminder


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'phone', 'debt_uzs', 'debt_usd', 'total_spent_uzs', 'total_spent_usd',
        'status', 'is_linked_display', 'is_telegram_verified_display', 'created_at',
    )
    list_filter = ('status', 'notifications_enabled', 'telegram_verified_at')
    search_fields = ('name', 'phone', 'telegram_chat_id')
    readonly_fields = ('link_token', 'bot_deep_link_display', 'last_debt_reminder_at',
                       'telegram_verified_at', 'total_spent_uzs', 'total_spent_usd',
                       'created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('name', 'phone', 'address', 'note')}),
        ('Moliya', {'fields': ('debt_uzs', 'debt_usd', 'total_spent_uzs', 'total_spent_usd', 'status')}),
        ('Telegram bot', {
            'fields': ('telegram_chat_id', 'notifications_enabled',
                       'telegram_verified_at', 'link_token', 'bot_deep_link_display',
                       'last_debt_reminder_at'),
        }),
        ('Tizim', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    ordering = ('-created_at',)
    actions = ['send_debt_reminders_action']

    def is_linked_display(self, obj):
        return '✅' if obj.is_linked else '—'
    is_linked_display.short_description = 'Bot'

    def is_telegram_verified_display(self, obj):
        return '✅' if obj.is_telegram_verified else '—'
    is_telegram_verified_display.short_description = 'Tasdiq'

    def bot_deep_link_display(self, obj):
        username = getattr(settings, 'TELEGRAM_BOT_USERNAME', '') or 'your_bot'
        link = obj.bot_deep_link(username)
        return format_html('<a href="{}" target="_blank">{}</a>', link, link)
    bot_deep_link_display.short_description = 'Botga ulanish linki'

    @admin.action(description="Tanlangan mijozlarga qarz eslatma yuborish")
    def send_debt_reminders_action(self, request, queryset):
        sent = 0
        for customer in queryset:
            if customer.is_linked and (customer.debt_uzs > 0 or customer.debt_usd > 0):
                if send_debt_reminder(customer):
                    sent += 1
        self.message_user(request, f"{sent} ta mijozga eslatma yuborildi", messages.SUCCESS)

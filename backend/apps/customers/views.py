from decimal import Decimal
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse
from .models import Customer
from .serializers import (
    CustomerSerializer, CustomerListSerializer,
    LinkByPhoneSerializer, LinkByTokenSerializer, PaymentSerializer,
)
from .services import (
    find_customer_by_phone, send_debt_reminder, send_payment_received,
)


@extend_schema(tags=['customers'])
@extend_schema_view(
    list=extend_schema(
        summary='Mijozlar ro\'yxati',
        description='Filter: `?status=vip|active|debtor|inactive`, Qidirish: `?search=Ali`',
    ),
    create=extend_schema(summary='Yangi mijoz qo\'shish'),
    retrieve=extend_schema(summary='Mijoz ma\'lumoti'),
    update=extend_schema(summary='Mijoz tahrirlash'),
    partial_update=extend_schema(summary='Mijoz qisman tahrirlash'),
    destroy=extend_schema(summary='Mijoz o\'chirish'),
)
class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['name', 'phone']
    ordering_fields = ['name', 'total_spent', 'debt', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return CustomerListSerializer
        return CustomerSerializer

    @extend_schema(summary='Qarzdor mijozlar')
    @action(detail=False, methods=['get'])
    def debtors(self, request):
        from django.db.models import Q
        customers = self.get_queryset().filter(
            Q(debt_uzs__gt=0) | Q(debt_usd__gt=0)
        ).order_by('-debt_uzs', '-debt_usd')
        serializer = CustomerListSerializer(customers, many=True)
        return Response(serializer.data)

    @extend_schema(summary='VIP mijozlar')
    @action(detail=False, methods=['get'])
    def vip(self, request):
        customers = self.get_queryset().filter(status='vip')
        serializer = CustomerListSerializer(customers, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary='Botga ulanish linkini olish',
        description=(
            'Mijoz uchun Telegram deep link qaytaradi. Bu linkni mijozga yuboring '
            '(SMS, WhatsApp, qog\'oz chekda QR kod va h.k.).\n\n'
            'Mijoz linkni bossa, bot uni avtomatik bog\'lab oladi.'
        ),
    )
    @action(detail=True, methods=['get'], url_path='bot-link')
    def bot_link(self, request, pk=None):
        customer = self.get_object()
        bot_username = getattr(settings, 'TELEGRAM_BOT_USERNAME', '') or 'your_bot'
        return Response({
            'token': customer.link_token,
            'deep_link': customer.bot_deep_link(bot_username),
            'is_linked': customer.is_linked,
            'is_telegram_verified': customer.is_telegram_verified,
            'telegram_verified_at': customer.telegram_verified_at,
            'telegram_chat_id': customer.telegram_chat_id or None,
        })

    @extend_schema(
        summary='Botdan ajratish',
        description='Mijozning Telegram aloqasini uzish (telegram_chat_id ni tozalash).',
    )
    @action(detail=True, methods=['post'], url_path='unlink')
    def unlink(self, request, pk=None):
        customer = self.get_object()
        customer.telegram_chat_id = ''
        customer.telegram_verified_at = None
        customer.save(update_fields=['telegram_chat_id', 'telegram_verified_at'])
        return Response({'detail': 'Aloqa uzildi'})

    @extend_schema(
        summary='Qo\'lda qarz eslatma yuborish',
        responses={
            200: OpenApiResponse(description='Yuborildi'),
            400: OpenApiResponse(description='Aloqa yo\'q yoki qarz yo\'q'),
        },
    )
    @action(detail=True, methods=['post'], url_path='send-debt-reminder')
    def send_debt_reminder_action(self, request, pk=None):
        customer = self.get_object()
        if not customer.is_linked:
            return Response({'detail': 'Mijoz botga ulanmagan'}, status=status.HTTP_400_BAD_REQUEST)
        if customer.debt_uzs <= 0 and customer.debt_usd <= 0:
            return Response({'detail': 'Mijozning qarzi yo\'q'}, status=status.HTTP_400_BAD_REQUEST)
        sent = send_debt_reminder(customer)
        if sent:
            return Response({'detail': 'Eslatma yuborildi'})
        return Response({'detail': 'Yuborib bo\'lmadi'}, status=status.HTTP_502_BAD_GATEWAY)

    @extend_schema(
        summary='Qarzdan to\'lov qabul qilish',
        description=(
            'Mijozning qarzini kamaytiradi va unga Telegram orqali tasdiq xabarini yuboradi.'
        ),
        request=PaymentSerializer,
    )
    @action(detail=True, methods=['post'], url_path='pay-debt')
    def pay_debt(self, request, pk=None):
        customer = self.get_object()
        serializer = PaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount_uzs = Decimal(serializer.validated_data.get('amount_uzs', 0))
        amount_usd = Decimal(serializer.validated_data.get('amount_usd', 0))

        # Qarzdan oshmasligi uchun cheklash
        amount_uzs = min(amount_uzs, customer.debt_uzs)
        amount_usd = min(amount_usd, customer.debt_usd)

        customer.debt_uzs -= amount_uzs
        customer.debt_usd -= amount_usd
        customer.update_status()
        customer.save()

        send_payment_received(customer, amount_uzs, amount_usd, customer.debt_uzs, customer.debt_usd)
        return Response({
            'detail': "To'lov qabul qilindi",
            'paid_uzs': float(amount_uzs),
            'paid_usd': float(amount_usd),
            'remaining_debt_uzs': float(customer.debt_uzs),
            'remaining_debt_usd': float(customer.debt_usd),
        })


@extend_schema(tags=['customers'])
class LinkByPhoneView(APIView):
    """Bot ishlatadi: mijoz Telegram contact share qilganda."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Telefon raqami orqali mijozni botga bog\'lash',
        description=(
            'Bot mijoz contact share qilganda chaqiradi. Telefon raqami CRM dagi mijoz bilan '
            'mos kelsa, `telegram_chat_id` to\'ldiriladi va mijoz tasdiqlangan hisoblanadi.'
        ),
        request=LinkByPhoneSerializer,
        responses={
            200: CustomerSerializer,
            404: OpenApiResponse(description='Bu telefon raqamli mijoz topilmadi'),
            409: OpenApiResponse(description='Boshqa chat_id ga ulangan'),
        },
    )
    def post(self, request):
        serializer = LinkByPhoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone']
        chat_id = str(serializer.validated_data['chat_id'])

        customer = find_customer_by_phone(phone)
        if not customer:
            return Response(
                {'detail': 'Bu telefon raqamli mijoz topilmadi'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if customer.telegram_chat_id and customer.telegram_chat_id != chat_id:
            return Response(
                {'detail': 'Mijoz allaqachon boshqa Telegram akkauntga ulangan'},
                status=status.HTTP_409_CONFLICT,
            )

        customer.telegram_chat_id = chat_id
        customer.telegram_verified_at = timezone.now()
        customer.save(update_fields=['telegram_chat_id', 'telegram_verified_at'])
        return Response(CustomerSerializer(customer).data)


@extend_schema(tags=['customers'])
class LinkByTokenView(APIView):
    """Bot ishlatadi: mijoz deep link orqali kirganda."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Token orqali mijozni botga bog\'lash',
        description=(
            'Bot `/start cust_<token>` deep link orqali chaqiradi. Token mos kelsa, '
            'mijozni shu Telegram chat_id ga bog\'laydi va tasdiqlangan hisoblaydi.'
        ),
        request=LinkByTokenSerializer,
        responses={
            200: CustomerSerializer,
            404: OpenApiResponse(description='Token noto\'g\'ri'),
        },
    )
    def post(self, request):
        serializer = LinkByTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['token']
        chat_id = str(serializer.validated_data['chat_id'])

        try:
            customer = Customer.objects.get(link_token=token)
        except Customer.DoesNotExist:
            return Response(
                {'detail': 'Bunday token mavjud emas'},
                status=status.HTTP_404_NOT_FOUND,
            )

        customer.telegram_chat_id = chat_id
        customer.telegram_verified_at = timezone.now()
        customer.save(update_fields=['telegram_chat_id', 'telegram_verified_at'])
        return Response(CustomerSerializer(customer).data)


@extend_schema(tags=['customers'])
class CustomerByChatIdView(APIView):
    """Bot ishlatadi: chat_id orqali mijoz haqida ma'lumot olish."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Telegram chat_id orqali mijozni topish',
        responses={
            200: CustomerSerializer,
            404: OpenApiResponse(description='Mijoz topilmadi'),
        },
    )
    def get(self, request, chat_id):
        try:
            customer = Customer.objects.get(telegram_chat_id=str(chat_id))
        except Customer.DoesNotExist:
            return Response({'detail': 'Mijoz topilmadi'}, status=status.HTTP_404_NOT_FOUND)
        return Response(CustomerSerializer(customer).data)

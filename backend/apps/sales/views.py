from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.timezone import now
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import Sale
from .serializers import SaleSerializer, SaleCreateSerializer, SaleListSerializer
from .utils import send_sale_notification
from apps.customers.services import send_sale_receipt


@extend_schema(tags=['sales'])
@extend_schema_view(
    list=extend_schema(
        summary='Sotuvlar ro\'yxati',
        description=(
            'Barcha sotuvlar. Filtrlar:\n'
            '- `?date_from=2026-01-01&date_to=2026-12-31` — sana oralig\'i\n'
            '- `?payment_method=cash` — to\'lov turi (cash/card/debt/transfer)\n'
            '- `?customer=1` — mijoz bo\'yicha\n'
            '- `?overdue=true` — muddati o\'tgan nasiyalar'
        ),
    ),
    create=extend_schema(
        summary='Yangi sotuv yaratish',
        description=(
            'Sotuv yaratish. `payment_method=debt` bo\'lsa `debt_due_date` majburiy.\n\n'
            '**Avtomatik:** stokdan kamaytiradi, mijoz qarzini yangilaydi, '
            'Telegram ga xabar yuboradi.'
        ),
        request=SaleCreateSerializer,
        responses={201: SaleSerializer},
    ),
    retrieve=extend_schema(summary='Sotuv tafsiloti (bandlar bilan)'),
    update=extend_schema(summary='Sotuv tahrirlash'),
    destroy=extend_schema(summary='Sotuv o\'chirish'),
)
class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.select_related('customer').prefetch_related('items__product', 'items__variant')
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['customer', 'payment_method']
    ordering_fields = ['created_at', 'total', 'debt_due_date']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return SaleListSerializer
        if self.action == 'create':
            return SaleCreateSerializer
        return SaleSerializer

    def create(self, request, *args, **kwargs):
        serializer = SaleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sale = serializer.save()
        send_sale_notification(sale)
        send_sale_receipt(sale)
        return Response(SaleSerializer(sale).data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        qs = super().get_queryset()
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        overdue = self.request.query_params.get('overdue')

        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        if overdue and overdue.lower() == 'true':
            today = now().date()
            qs = qs.filter(
                payment_method='debt',
                debt_due_date__lt=today,
                debt_due_date__isnull=False,
            )
        return qs

    @extend_schema(
        summary='Muddati o\'tgan nasiyalar',
        description='`payment_method=debt` va `debt_due_date` bugundan kichik bo\'lgan sotuvlar.',
    )
    @action(detail=False, methods=['get'], url_path='overdue')
    def overdue(self, request):
        today = now().date()
        qs = self.get_queryset().filter(
            payment_method='debt',
            debt_due_date__lt=today,
            debt_due_date__isnull=False,
        )
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = SaleListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = SaleListSerializer(qs, many=True)
        return Response(serializer.data)

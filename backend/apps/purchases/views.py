from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import Purchase
from .serializers import PurchaseSerializer, PurchaseCreateSerializer, PurchaseListSerializer
from .utils import send_purchase_notification


@extend_schema(tags=['purchases'])
@extend_schema_view(
    list=extend_schema(
        summary='Haridlar ro\'yxati',
        description='Filtrlar: `?date_from=2026-01-01&date_to=2026-12-31`, `?payment_method=cash`',
    ),
    create=extend_schema(
        summary='Yangi harid yaratish',
        description=(
            'Harid yaratish. Har bir `items` bandida `cost_price` — sotib olish narxi.\n\n'
            '**Avtomatik:** mahsulot stokiga qo\'shadi, `cost_price` ni yangilaydi, '
            'Telegram ga xabar yuboradi.'
        ),
        request=PurchaseCreateSerializer,
        responses={201: PurchaseSerializer},
    ),
    retrieve=extend_schema(summary='Harid tafsiloti'),
    update=extend_schema(summary='Harid tahrirlash'),
    destroy=extend_schema(summary='Harid o\'chirish'),
)
class PurchaseViewSet(viewsets.ModelViewSet):
    queryset = Purchase.objects.prefetch_related('items__product', 'items__variant')
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['payment_method']
    ordering_fields = ['created_at', 'total']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return PurchaseListSerializer
        if self.action == 'create':
            return PurchaseCreateSerializer
        return PurchaseSerializer

    def create(self, request, *args, **kwargs):
        serializer = PurchaseCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        purchase = serializer.save()
        send_purchase_notification(purchase)
        return Response(PurchaseSerializer(purchase).data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        qs = super().get_queryset()
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        return qs

from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum, Count, F, DecimalField, ExpressionWrapper
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from datetime import timedelta
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from apps.sales.models import Sale, SaleItem
from apps.purchases.models import Purchase
from apps.products.models import Product, ProductVariant
from apps.customers.models import Customer


def _a(qs, field):
    """Queryset aggregation helper — returns 0 if None."""
    return qs.aggregate(t=Sum(field))['t'] or 0


def _sum_price_quantity(qs, price_field='cost_price'):
    money_field = DecimalField(max_digits=20, decimal_places=2)
    return qs.aggregate(
        t=Sum(
            ExpressionWrapper(
                F(price_field) * F('quantity'),
                output_field=money_field,
            )
        )
    )['t'] or 0


@extend_schema(tags=['reports'])
class DashboardView(APIView):
    @extend_schema(
        summary='Dashboard statistikasi',
        description='period: today | 7kun | oylik | yillik',
        parameters=[
            OpenApiParameter('period', OpenApiTypes.STR, default='today')
        ],
    )
    def get(self, request):
        period = request.query_params.get('period', 'today')
        now = timezone.now()

        if period == 'today':
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == '7kun':
            start = now - timedelta(days=7)
        elif period == 'oylik':
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == 'yillik':
            start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        sales = Sale.objects.filter(created_at__gte=start)
        purchases = Purchase.objects.filter(created_at__gte=start)
        items = SaleItem.objects.filter(sale__created_at__gte=start)
        variants = ProductVariant.objects.filter(is_active=True, product__is_active=True)

        # Daromad valyuta bo'yicha
        revenue_uzs = _a(sales, 'total_uzs')
        revenue_usd = _a(sales, 'total_usd')

        # Ombordagi aktiv variantlar tan narxi (kategoriya API bilan bir xil hisob).
        stock_cost_uzs = _sum_price_quantity(variants.filter(currency='uzs'))
        stock_cost_usd = _sum_price_quantity(variants.filter(currency='usd'))

        # Sotilgan mahsulotlar tan narxi. Foyda shundan hisoblanadi.
        sale_cost_uzs = _sum_price_quantity(items.filter(currency='uzs'))
        sale_cost_usd = _sum_price_quantity(items.filter(currency='usd'))

        profit_uzs = revenue_uzs - sale_cost_uzs
        profit_usd = revenue_usd - sale_cost_usd

        # Harid jami valyuta bo'yicha
        purchase_total_uzs = _a(purchases, 'total_uzs')
        purchase_total_usd = _a(purchases, 'total_usd')

        sales_count = sales.count()
        purchases_count = purchases.count()

        # Jami qarzlar
        debt_uzs = _a(Customer.objects, 'debt_uzs')
        debt_usd = _a(Customer.objects, 'debt_usd')

        # Kunlik grafik — ikki valyuta alohida
        if period == 'today':
            daily_qs = (
                sales.values('created_at__hour')
                .annotate(amount_uzs=Sum('total_uzs'), amount_usd=Sum('total_usd'))
                .order_by('created_at__hour')
            )
            daily_sales = [
                {
                    'date': f"{d['created_at__hour']:02d}:00",
                    'amount_uzs': float(d['amount_uzs'] or 0),
                    'amount_usd': float(d['amount_usd'] or 0),
                }
                for d in daily_qs
            ]
        else:
            daily_qs = (
                sales.annotate(date=TruncDate('created_at'))
                .values('date')
                .annotate(amount_uzs=Sum('total_uzs'), amount_usd=Sum('total_usd'))
                .order_by('date')
            )
            daily_sales = [
                {
                    'date': str(d['date']),
                    'amount_uzs': float(d['amount_uzs'] or 0),
                    'amount_usd': float(d['amount_usd'] or 0),
                }
                for d in daily_qs
            ]

        # Top mahsulotlar — valyuta bo'yicha alohida
        top_products = (
            items
            .values('product__name', 'currency')
            .annotate(
                total_qty=Sum('quantity'),
                revenue=Sum(ExpressionWrapper(F('price') * F('quantity'), output_field=DecimalField()))
            )
            .order_by('-revenue')[:10]
        )
        top_products_data = [
            {
                'name': p['product__name'],
                'currency': p['currency'],
                'quantity': p['total_qty'],
                'revenue': float(p['revenue']),
            }
            for p in top_products
        ]

        # Top mijozlar — UZS va USD alohida
        top_customers_qs = (
            sales.filter(customer__isnull=False)
            .values(customer_name=F('customer__name'))
            .annotate(
                spent_uzs=Sum('total_uzs'),
                spent_usd=Sum('total_usd'),
                orders=Count('id'),
            )
            .order_by('-spent_uzs')[:5]
        )
        top_customers_data = [
            {
                'name': c['customer_name'],
                'spent_uzs': float(c['spent_uzs'] or 0),
                'spent_usd': float(c['spent_usd'] or 0),
                'orders': c['orders'],
            }
            for c in top_customers_qs
        ]

        return Response({
            'revenue_uzs': float(revenue_uzs),
            'revenue_usd': float(revenue_usd),
            'cost_uzs': float(sale_cost_uzs),
            'cost_usd': float(sale_cost_usd),
            'cost_usd_in_uzs': float(sale_cost_usd),
            'stock_cost_uzs': float(stock_cost_uzs),
            'stock_cost_usd': float(stock_cost_usd),
            'sale_cost_uzs': float(sale_cost_uzs),
            'sale_cost_usd': float(sale_cost_usd),
            'profit_uzs': float(profit_uzs),
            'profit_usd': float(profit_usd),
            'purchase_total_uzs': float(purchase_total_uzs),
            'purchase_total_usd': float(purchase_total_usd),
            'purchase_total': float(purchase_total_uzs),
            'sales_count': sales_count,
            'purchases_count': purchases_count,
            'debt_uzs': float(debt_uzs),
            'debt_usd': float(debt_usd),
            'daily_sales': daily_sales,
            'top_products': top_products_data,
            'top_customers': top_customers_data,
        })


@extend_schema(tags=['reports'])
class ProfitReportView(APIView):
    @extend_schema(
        summary='Foyda hisoboti',
        description=(
            'Daromad va sof foyda UZS va USD bo\'yicha alohida.\n'
            'Sotuv va harid summalari qaysi valyutada bo\'lsa, shu valyutada jamlanadi.'
        ),
        parameters=[
            OpenApiParameter('date_from', OpenApiTypes.DATE),
            OpenApiParameter('date_to', OpenApiTypes.DATE),
        ],
    )
    def get(self, request):
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        sales_qs = Sale.objects.all()
        purchases_qs = Purchase.objects.all()
        if date_from:
            sales_qs = sales_qs.filter(created_at__date__gte=date_from)
            purchases_qs = purchases_qs.filter(created_at__date__gte=date_from)
        if date_to:
            sales_qs = sales_qs.filter(created_at__date__lte=date_to)
            purchases_qs = purchases_qs.filter(created_at__date__lte=date_to)

        items_qs = SaleItem.objects.filter(sale__in=sales_qs)

        revenue_uzs = _a(sales_qs, 'total_uzs')
        revenue_usd = _a(sales_qs, 'total_usd')
        purchase_cost_uzs = _a(purchases_qs, 'total_uzs')
        purchase_cost_usd = _a(purchases_qs, 'total_usd')

        sale_cost_uzs = _sum_price_quantity(items_qs.filter(currency='uzs'))
        sale_cost_usd = _sum_price_quantity(items_qs.filter(currency='usd'))

        gross_profit_uzs = revenue_uzs - sale_cost_uzs
        gross_profit_usd = revenue_usd - sale_cost_usd

        # Oylik — sotuv va harid UZS/USD alohida
        monthly_sales = (
            sales_qs.annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(
                revenue_uzs=Sum('total_uzs'),
                revenue_usd=Sum('total_usd'),
                count=Count('id'),
            )
            .order_by('month')
        )
        monthly_purchases = (
            purchases_qs.annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(
                purchase_uzs=Sum('total_uzs'),
                purchase_usd=Sum('total_usd'),
                purchase_count=Count('id'),
            )
            .order_by('month')
        )
        monthly_map = {}
        for m in monthly_sales:
            month = m['month']
            monthly_map[month] = {
                'month': str(month)[:7],
                'revenue_uzs': float(m['revenue_uzs'] or 0),
                'revenue_usd': float(m['revenue_usd'] or 0),
                'purchase_uzs': 0,
                'purchase_usd': 0,
                'sales_count': m['count'],
                'count': m['count'],
                'purchase_count': 0,
            }
        for m in monthly_purchases:
            month = m['month']
            row = monthly_map.setdefault(month, {
                'month': str(month)[:7],
                'revenue_uzs': 0,
                'revenue_usd': 0,
                'purchase_uzs': 0,
                'purchase_usd': 0,
                'sales_count': 0,
                'count': 0,
                'purchase_count': 0,
            })
            row['purchase_uzs'] = float(m['purchase_uzs'] or 0)
            row['purchase_usd'] = float(m['purchase_usd'] or 0)
            row['purchase_count'] = m['purchase_count']

        return Response({
            'revenue_uzs': float(revenue_uzs),
            'revenue_usd': float(revenue_usd),
            'purchase_cost_uzs': float(purchase_cost_uzs),
            'purchase_cost_usd': float(purchase_cost_usd),
            'purchase_cost': float(purchase_cost_uzs),
            'sale_cost_uzs': float(sale_cost_uzs),
            'sale_cost_usd': float(sale_cost_usd),
            'sale_cost_usd_in_uzs': float(sale_cost_usd),
            'gross_profit_uzs': float(gross_profit_uzs),
            'gross_profit_usd': float(gross_profit_usd),
            'monthly': [monthly_map[m] for m in sorted(monthly_map)],
        })


@extend_schema(tags=['reports'])
class WarehouseReportView(APIView):
    @extend_schema(
        summary='Ombor holati',
        description='Variantlar UZS va USD valyutasi bo\'yicha alohida qiymat.',
    )
    def get(self, request):
        variants = ProductVariant.objects.select_related('product').filter(
            is_active=True, product__is_active=True
        )

        total_value_uzs = _sum_price_quantity(variants.filter(currency='uzs'))
        total_value_usd = _sum_price_quantity(variants.filter(currency='usd'))

        low_stock = [
            {
                'id': v.id,
                'product_id': v.product_id,
                'name': f"{v.product.name} ({v.name})",
                'quantity': v.quantity,
                'currency': v.currency,
                'status': v.status,
            }
            for v in variants if v.status in ('low', 'critical')
        ]

        return Response({
            'total_products': Product.objects.filter(is_active=True).count(),
            'total_variants': variants.count(),
            'total_value_uzs': float(total_value_uzs),
            'total_value_usd': float(total_value_usd),
            'low_stock_count': len(low_stock),
            'low_stock': low_stock,
        })

from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    CustomerViewSet, LinkByPhoneView, LinkByTokenView, CustomerByChatIdView,
)

router = DefaultRouter()
router.register('', CustomerViewSet, basename='customer')

urlpatterns = [
    # Bot uchun maxsus endpointlar (router dan oldin)
    path('link-by-phone/', LinkByPhoneView.as_view(), name='customer-link-by-phone'),
    path('link-by-token/', LinkByTokenView.as_view(), name='customer-link-by-token'),
    path('by-chat-id/<str:chat_id>/', CustomerByChatIdView.as_view(), name='customer-by-chat-id'),
] + router.urls

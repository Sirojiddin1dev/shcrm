from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ProductViewSet, ProductVariantViewSet

router = DefaultRouter()
router.register('categories', CategoryViewSet, basename='category')
router.register('variants', ProductVariantViewSet, basename='variant')
router.register('', ProductViewSet, basename='product')

urlpatterns = router.urls

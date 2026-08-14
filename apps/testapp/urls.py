from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from apps.testapp.views import CustomTokenObtainPairView, LessonViewSet, GoogleAuthView

router = DefaultRouter()

router.register(r'lessons', LessonViewSet, basename='lesson')
router.register(r'google-auth', GoogleAuthView, basename='google-auth')

urlpatterns = [
    path("", include(router.urls)),
    path('jwt/create/', CustomTokenObtainPairView.as_view(), name='create_token_pair'),
    path('jwt/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
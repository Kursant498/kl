from rest_framework_simplejwt.views import TokenObtainPairView
from apps.testapp.serializers import CustomTokenObtainPairSerializer    
from rest_framework.viewsets import ModelViewSet
from apps.testapp.models import Lesson
from apps.testapp.serializers import LessonSerializer, GoogleAuthSerializer
from apps.testapp.permissions import IsTeacherOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from apps.testapp.models import CustomUser
from apps.testapp.services import get_google_access_token, get_google_user_info
from django.core.cache import cache

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class LessonViewSet(ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    
    permission_classes = [IsTeacherOrReadOnly]

CACHE_KEY_LESSON_LIST = "lessons_list_cache"
CACHE_TIMEOUT = 300  

class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all().order_by('-views')
    serializer_class = LessonSerializer
    permission_classes = [IsTeacherOrReadOnly]

    def list(self, request, *args, **kwargs):
        cached_data = cache.get(CACHE_KEY_LESSON_LIST)
        
        if cached_data is not None:
            return Response(cached_data)
        
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        data_to_cache = serializer.data
        
        cache.set(CACHE_KEY_LESSON_LIST, data_to_cache, CACHE_TIMEOUT)
        
        return Response(data_to_cache)
    
    def retrieve(self, request, *args, **kwargs):
        instance_id = self.kwargs.get(self.lookup_url_kwarg or 'pk')
        
        lesson_cache_key = f"lesson_detail_{instance_id}"
        views_cache_key = f"lesson_views_{instance_id}"

        if cache.get(views_cache_key) is None:
            instance = self.get_object()
            cache.set(views_cache_key, instance.views_count, timeout=None) 

        actual_views = cache.incr(views_cache_key)

        cached_data = cache.get(lesson_cache_key)
        
        if cached_data is None:
            instance = locals().get('instance') or self.get_object()
            serializer = self.get_serializer(instance)
            cached_data = serializer.data
            cache.set(lesson_cache_key, cached_data, CACHE_TIMEOUT)

        cached_data['views_count'] = actual_views
        
        return Response(cached_data)

    def perform_create(self, serializer):
        serializer.save()
        
        cache.delete(CACHE_KEY_LESSON_LIST)

    def perform_update(self, serializer):
        serializer.save()
        cache.delete(CACHE_KEY_LESSON_LIST)  

    def perform_destroy(self, instance):
        instance.delete()
        cache.delete(CACHE_KEY_LESSON_LIST) 


class GoogleAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        code = serializer.validated_data['code']
        
        google_token = get_google_access_token(code)
        if not google_token:
            return Response(
                {"error": "Не удалось обменять code наз токен от Google."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_info = get_google_user_info(google_token)
        email = user_info.get('email')
        
        if not email:
            return Response(
                {"error": "Google не предоставил email пользователя."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        user = CustomUser.objects.filter(email=email).first()
        created = False

        if not user:
            user = CustomUser.objects.create_user(
                email=email,
                username=user_info.get('name', ''),
                role=CustomUser.Role.STUDENT,
                is_active=True
            )
            user.set_unusable_password()
            user.save()
            created = True

        refresh = RefreshToken.for_user(user)
        refresh['email'] = user.email
        refresh['role'] = user.role
        
        return Response({
            "message": "Успешная авторизация через Google",
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "is_new_user": created,
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role,
            },
        }, status=status.HTTP_200_OK)
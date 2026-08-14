from rest_framework_simplejwt.views import TokenObtainPairView
from apps.testapp.serializers import CustomTokenObtainPairSerializer    
from rest_framework.viewsets import ModelViewSet
from apps.testapp.models import Lesson
from apps.testapp.serializers import LessonSerializer, GoogleAuthSerializer
from apps.testapp.permissions import IsTeacherOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from apps.testapp.models import CustomUser
from apps.testapp.services import get_google_access_token, get_google_user_info

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class LessonViewSet(ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    
    permission_classes = [IsTeacherOrReadOnly]

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
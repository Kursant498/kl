from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from apps.testapp.models import Lesson

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['email'] = user.email
        token['username'] = user.username
        token['role'] = user.role
        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        user = self.user
        
        data['user'] = {
            'id': user.id,
            'email': user.email,
            'role': user.role,
            'username': user.username,
        }

        return data

class GoogleAuthSerializer(serializers.Serializer):
    code = serializers.CharField(
        required=True, 
        help_text="Одноразовый code, полученный фронтендом от Google"
    )

class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'title', 'description', 'views', 'data']
        read_only_fields = ['views']

    


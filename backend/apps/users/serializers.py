from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import TelegramBotUser, User


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        phone = data.get('phone')
        password = data.get('password')
        user = authenticate(username=phone, password=password)
        if not user:
            raise serializers.ValidationError('Telefon yoki parol noto\'g\'ri')
        if not user.is_active:
            raise serializers.ValidationError('Foydalanuvchi bloklangan')
        data['user'] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'phone', 'full_name', 'is_staff', 'created_at')
        read_only_fields = ('id', 'created_at')


class TelegramBotUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramBotUser
        fields = (
            'id',
            'chat_id',
            'full_name',
            'username',
            'is_active',
            'added_by',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'added_by', 'created_at', 'updated_at')

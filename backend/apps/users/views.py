from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from rest_framework import serializers as drf_serializers
from .models import TelegramBotUser, User
from .serializers import LoginSerializer, TelegramBotUserSerializer, UserSerializer


@extend_schema(tags=['auth'])
class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary='Login — JWT token olish',
        description=(
            'Telefon raqami va parol bilan tizimga kirish.\n\n'
            '**Default:** `+998111111111` / `nsdadmin123`\n\n'
            'Qaytarilgan `access` tokenini keyingi so\'rovlarda ishlatish uchun:\n'
            '`Authorization: Bearer <access>`'
        ),
        request=LoginSerializer,
        responses={
            200: inline_serializer('LoginResponse', fields={
                'access': drf_serializers.CharField(),
                'refresh': drf_serializers.CharField(),
                'user': UserSerializer(),
            }),
            400: OpenApiResponse(description='Noto\'g\'ri telefon yoki parol'),
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        })


@extend_schema(tags=['auth'])
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Logout',
        description='Refresh tokenni bekor qiladi.',
        request=inline_serializer('LogoutRequest', fields={
            'refresh': drf_serializers.CharField(required=False),
        }),
        responses={200: OpenApiResponse(description='Muvaffaqiyatli chiqildi')},
    )
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass
        return Response({'detail': 'Chiqildi'}, status=status.HTTP_200_OK)


@extend_schema(tags=['auth'])
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Joriy foydalanuvchi ma\'lumoti',
        responses={200: UserSerializer},
    )
    def get(self, request):
        return Response(UserSerializer(request.user).data)


@extend_schema(tags=['bot-users'])
class TelegramBotUserListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Telegram bot foydalanuvchilari ro\'yxati',
        responses={200: TelegramBotUserSerializer(many=True)},
    )
    def get(self, request):
        users = TelegramBotUser.objects.all()
        return Response(TelegramBotUserSerializer(users, many=True).data)

    @extend_schema(
        summary='Telegram bot foydalanuvchisini qo\'shish',
        request=TelegramBotUserSerializer,
        responses={201: TelegramBotUserSerializer},
    )
    def post(self, request):
        serializer = TelegramBotUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save(added_by=request.user)
        return Response(TelegramBotUserSerializer(user).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['bot-users'])
class TelegramBotUserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Telegram chat ID botdan foydalana olishini tekshirish',
        responses={200: inline_serializer('TelegramBotUserAllowedResponse', fields={
            'allowed': drf_serializers.BooleanField(),
            'user': TelegramBotUserSerializer(required=False, allow_null=True),
        })},
    )
    def get(self, request, chat_id):
        user = TelegramBotUser.objects.filter(chat_id=chat_id, is_active=True).first()
        return Response({
            'allowed': user is not None,
            'user': TelegramBotUserSerializer(user).data if user else None,
        })

    @extend_schema(
        summary='Telegram bot foydalanuvchisini o\'chirish',
        responses={204: OpenApiResponse(description='O\'chirildi')},
    )
    def delete(self, request, chat_id):
        deleted, _ = TelegramBotUser.objects.filter(chat_id=chat_id).delete()
        if not deleted:
            return Response({'detail': 'Foydalanuvchi topilmadi'}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=['auth'])
class VerifyStaffByPhoneView(APIView):
    """Bot ishlatadi: telefon share qilinganda staff (is_staff=True) ekanini tekshiradi."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Telefon orqali staff tekshirish va bot ga ulash',
        request=inline_serializer('VerifyStaffRequest', fields={
            'phone': drf_serializers.CharField(),
            'chat_id': drf_serializers.IntegerField(),
            'full_name': drf_serializers.CharField(required=False),
            'username': drf_serializers.CharField(required=False),
        }),
        responses={
            200: inline_serializer('VerifyStaffResponse', fields={
                'is_staff': drf_serializers.BooleanField(),
                'full_name': drf_serializers.CharField(),
            }),
        },
    )
    def post(self, request):
        phone_raw = request.data.get('phone', '')
        chat_id = request.data.get('chat_id')
        full_name = request.data.get('full_name', '')
        username = request.data.get('username', '')

        # Telefon raqamni normallashtirish
        digits = ''.join(c for c in phone_raw if c.isdigit())

        # Barcha stafflarni tekshirish
        staff_user = None
        for u in User.objects.filter(is_staff=True, is_active=True):
            u_digits = ''.join(c for c in (u.phone or '') if c.isdigit())
            if u_digits and (u_digits == digits or
                             ('998' + u_digits[-9:] == digits[-12:]) or
                             (u_digits[-9:] == digits[-9:])):
                staff_user = u
                break

        if not staff_user:
            return Response({'is_staff': False, 'full_name': ''})

        # TelegramBotUser ga qo'shish yoki yangilash
        bot_user, _ = TelegramBotUser.objects.get_or_create(
            chat_id=chat_id,
            defaults={
                'full_name': full_name or staff_user.full_name,
                'username': username,
                'is_active': True,
                'added_by': request.user,
            }
        )
        if not bot_user.is_active:
            bot_user.is_active = True
            bot_user.save(update_fields=['is_active'])

        return Response({
            'is_staff': True,
            'full_name': staff_user.full_name or full_name,
        })

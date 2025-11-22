from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout, update_session_auth_hash
from apps.users.models import User  # ← ИЗМЕНИТЕ ИМПОРТ
from apps.users.serializers import (  # ← ИЗМЕНИТЕ ИМПОРТ
    UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer,
    UserUpdateSerializer, ChangePasswordSerializer
)


class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Автоматически логиним пользователя после регистрации
        login(request, user)
        token, created = Token.objects.get_or_create(user=user)

        return Response({
            'user': UserProfileSerializer(user).data,
            'token': token.key,
            'detail': 'Пользователь успешно зарегистрирован'
        }, status=status.HTTP_201_CREATED)


class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserUpdateView(generics.UpdateAPIView):
    serializer_class = UserUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response({
            'detail': 'Профиль успешно обновлен',
            'user': UserProfileSerializer(instance).data
        })


class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = self.get_object()

        # Проверяем старый пароль
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'old_password': ['Неверный текущий пароль']},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Устанавливаем новый пароль
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        # Обновляем сессию чтобы пользователь не разлогинился
        update_session_auth_hash(request, user)

        return Response({'detail': 'Пароль успешно изменен'})


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def user_login(request):
    serializer = UserLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = serializer.validated_data['user']
    login(request, user)

    token, created = Token.objects.get_or_create(user=user)

    return Response({
        'user': UserProfileSerializer(user).data,
        'token': token.key,
        'detail': 'Успешный вход в систему'
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def user_logout(request):
    try:
        # Удаляем токен аутентификации
        request.user.auth_token.delete()
    except:
        pass

    # Выход из системы
    logout(request)

    return Response({'detail': 'Успешный выход из системы'})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_info(request):
    """Информация о текущем пользователе"""
    user = request.user
    serializer = UserProfileSerializer(user)

    # Добавляем дополнительную информацию в зависимости от типа пользователя
    data = serializer.data
    if user.is_supplier and hasattr(user, 'supplier_profile'):
        from apps.suppliers.serializers import SupplierSerializer
        supplier_serializer = SupplierSerializer(user.supplier_profile)
        data['supplier_profile'] = supplier_serializer.data

    return Response(data)

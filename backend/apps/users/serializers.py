from rest_framework import serializers
from django.contrib.auth import authenticate
from apps.users.models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'user_type', 'phone', 'company_name', 'first_name', 'last_name'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Пароли не совпадают"})

        if User.objects.filter(email=attrs.get('email')).exists():
            raise serializers.ValidationError({"email": "Пользователь с таким email уже существует"})

        if User.objects.filter(username=attrs.get('username')).exists():
            raise serializers.ValidationError({"username": "Пользователь с таким именем уже существует"})

        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Неверные учетные данные')
            if not user.is_active:
                raise serializers.ValidationError('Аккаунт отключен')
            attrs['user'] = user
            return attrs
        raise serializers.ValidationError('Необходимо указать username и password')


class UserProfileSerializer(serializers.ModelSerializer):
    user_type_display = serializers.CharField(source='get_user_type_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'user_type', 'user_type_display',
            'phone', 'company_name', 'address', 'first_name', 'last_name',
            'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'user_type', 'date_joined', 'last_login']


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone', 'company_name', 'address'
        ]


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    new_password_confirm = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password_confirm": "Новые пароли не совпадают"})
        return attrs

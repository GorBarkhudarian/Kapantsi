import random
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, UserSerializer
from .forms import RegisterForm, LoginForm
from .models import EmailVerification

User = get_user_model()


# --- REST API ---
class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            })
        return Response({'detail': _('Invalid credentials.')}, status=status.HTTP_401_UNAUTHORIZED)


class MeAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


# --- Web Views ---
def _send_verification_email(user, code):
    send_mail(
        subject='Kapantsi — Verify your email / Հաստատեք Ձեր էլ. հասցեն',
        message=(
            f'Your verification code is: {code}\n\n'
            f'Ձեր հաստատման կոդն է՝ {code}\n\n'
            f'The code expires in 10 minutes.\n'
            f'Կոդն անվավեր է դառնում 10 րոպե անց։'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def register_view(request):
    if request.user.is_authenticated:
        if getattr(request.user, 'is_admin_user', False):
            return redirect('admin_dashboard')
        return redirect('dashboard')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            code = str(random.randint(100000, 999999))
            EmailVerification.objects.update_or_create(
                user=user,
                defaults={
                    'code': code,
                    'expires_at': timezone.now() + timezone.timedelta(minutes=10),
                    'is_used': False,
                }
            )
            try:
                _send_verification_email(user, code)
                request.session['pending_user_id'] = user.pk
                return redirect('verify_email')
            except Exception as e:
                print(f'[EMAIL ERROR] {type(e).__name__}: {e}')
                user.delete()
                messages.error(request, _('Could not send verification email. Please check your email address.'))
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


@ensure_csrf_cookie
def verify_email_view(request):
    user_id = request.session.get('pending_user_id')
    if not user_id:
        return redirect('register')

    try:
        user = User.objects.get(pk=user_id)
        verification = EmailVerification.objects.get(user=user)
    except (User.DoesNotExist, EmailVerification.DoesNotExist):
        return redirect('register')

    error = None
    if request.method == 'POST':
        entered_code = request.POST.get('code', '').strip()
        if verification.is_used:
            error = _('This code has already been used.')
        elif timezone.now() > verification.expires_at:
            error = _('The code has expired. Please register again.')
        elif entered_code != verification.code:
            error = _('Incorrect code. Please try again.')
        else:
            verification.is_used = True
            verification.save()
            user.is_active = True
            user.save()
            del request.session['pending_user_id']
            login(request, user)
            messages.success(request, _('Email verified! Welcome to Կապանցի.'))
            return redirect('dashboard')

    return render(request, 'accounts/verify_email.html', {
        'email': user.email,
        'error': error,
    })


def login_view(request):
    if request.user.is_authenticated:
        if getattr(request.user, 'is_admin_user', False):
            return redirect('admin_dashboard')
        return redirect('dashboard')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            if getattr(user, 'is_admin_user', False):
                return redirect('admin_dashboard')
            return redirect('dashboard')
        else:
            # Check if user exists but is not verified yet
            username = request.POST.get('username', '').strip()
            try:
                unverified = User.objects.get(username=username, is_active=False)
                # Redirect them back to verify email if session still has their id
                request.session['pending_user_id'] = unverified.pk
                messages.warning(request, _('Your email is not verified yet. Please enter the code sent to your email.'))
                return redirect('verify_email')
            except User.DoesNotExist:
                messages.error(request, _('Invalid username or password.'))
    else:
        form = LoginForm(request)
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('home')

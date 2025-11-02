# SPEC-AUTH-001 구현 계획 (Implementation Plan)

**SPEC ID**: SPEC-AUTH-001
**작성일**: 2025-11-03
**작성자**: @Sam
**예상 기간**: 2주 (10 작업일)

---

## 📋 목차

1. [구현 전략](#1-구현-전략)
2. [개발 단계](#2-개발-단계)
3. [기술 스택 상세](#3-기술-스택-상세)
4. [디렉토리 구조](#4-디렉토리-구조)
5. [테스트 계획](#5-테스트-계획)
6. [배포 전략](#6-배포-전략)
7. [리스크 및 대응 방안](#7-리스크-및-대응-방안)
8. [타임라인](#8-타임라인)

---

## 1. 구현 전략

### 1.1 전체 접근 방식

**TDD (Test-Driven Development) 원칙 적용**:
- RED: 실패하는 테스트 작성
- GREEN: 최소 코드로 테스트 통과
- REFACTOR: 코드 개선 및 최적화

**점진적 전환 전략**:
- Phase 1: JWT 인증 시스템 추가 (기존 세션 인증 유지)
- Phase 2: 프론트엔드 통합 및 테스트
- Phase 3: 세션 인증 제거 및 JWT 완전 전환

### 1.2 개발 우선순위

**우선순위 1 (Critical)**:
- JWT 토큰 발급/검증 (REQ-AUTH-001, REQ-AUTH-002)
- 역할 기반 권한 제어 (REQ-AUTH-005, REQ-AUTH-006)
- 로그아웃 및 블랙리스트 (REQ-AUTH-007)

**우선순위 2 (High)**:
- Access Token 자동 갱신 (REQ-AUTH-003)
- 프론트엔드 Axios interceptor
- 사용자 관리 API (Admin)

**우선순위 3 (Medium)**:
- 비밀번호 변경/재설정 (REQ-AUTH-009, REQ-AUTH-010)
- 감사 로그 (NFR-AUTH-008)
- Rate limiting (NFR-AUTH-003)

---

## 2. 개발 단계

### 2.1 Backend 구현 (Day 1-7)

#### Day 1-2: 환경 설정 및 모델 설계

**작업 내용**:
1. Django REST Framework Simple JWT 설치
```bash
pip install djangorestframework-simplejwt==5.3.1
pip freeze > requirements.txt
```

2. settings.py 설정
```python
# backend/config/settings.py

INSTALLED_APPS = [
    # ...
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        # 기존 세션 인증 유지 (Phase 1)
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '5/minute',
        'user': '1000/hour'
    }
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}
```

3. User 모델 확장
```python
# backend/dashboard/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('viewer', 'Viewer'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer')
    full_name = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)

    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    failed_login_attempts = models.IntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'auth_user_extended'
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['department']),
        ]
```

4. 마이그레이션 실행
```bash
# AUTH_USER_MODEL 설정 (settings.py)
AUTH_USER_MODEL = 'dashboard.User'

# 마이그레이션
python manage.py makemigrations
python manage.py migrate
```

**테스트**:
```python
# tests/test_models.py
@pytest.mark.django_db
def test_user_model_role_default():
    user = User.objects.create_user(username='testuser', password='test123')
    assert user.role == 'viewer'

@pytest.mark.django_db
def test_user_is_admin():
    admin = User.objects.create_user(username='admin', role='admin')
    assert admin.is_admin() == True
```

---

#### Day 3-4: JWT 인증 API 구현

**작업 내용**:
1. Serializers 작성
```python
# backend/dashboard/serializers.py

from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'full_name', 'department']
        read_only_fields = ['id']

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value):
        # 비밀번호 강도 검증
        import re
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("대문자를 포함해야 합니다.")
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError("소문자를 포함해야 합니다.")
        if not re.search(r'[0-9]', value):
            raise serializers.ValidationError("숫자를 포함해야 합니다.")
        if not re.search(r'[!@#$%^&*]', value):
            raise serializers.ValidationError("특수문자를 포함해야 합니다.")
        return value
```

2. Views 작성
```python
# backend/dashboard/views.py

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User, BlacklistedToken, AuthLog
from .serializers import LoginSerializer, UserSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """사용자 로그인 및 JWT 토큰 발급"""
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username = serializer.validated_data['username']
    password = serializer.validated_data['password']

    # 계정 잠금 확인
    try:
        user = User.objects.get(username=username)
        if user.account_locked_until and user.account_locked_until > timezone.now():
            return Response({
                'error': '계정이 잠겼습니다',
                'message': f'{user.account_locked_until}까지 로그인할 수 없습니다.',
                'code': 'ACCOUNT_LOCKED'
            }, status=status.HTTP_403_FORBIDDEN)
    except User.DoesNotExist:
        pass

    # 인증
    user = authenticate(username=username, password=password)

    if user is not None:
        # 로그인 성공
        user.failed_login_attempts = 0
        user.last_login_ip = get_client_ip(request)
        user.save()

        # JWT 토큰 발급
        refresh = RefreshToken.for_user(user)
        refresh['role'] = user.role  # Custom claim

        # 감사 로그
        AuthLog.objects.create(
            user=user,
            event_type='login_success',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        })
    else:
        # 로그인 실패
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.account_locked_until = timezone.now() + timedelta(minutes=15)
            user.save()

        # 감사 로그
        AuthLog.objects.create(
            user=user,
            event_type='login_failure',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=False
        )

        return Response({
            'error': '인증 실패',
            'message': '아이디 또는 비밀번호가 올바르지 않습니다.',
            'code': 'INVALID_CREDENTIALS'
        }, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """로그아웃 및 Refresh Token 블랙리스트 추가"""
    try:
        refresh_token = request.data.get('refresh')
        token = RefreshToken(refresh_token)

        # 블랙리스트 추가
        BlacklistedToken.objects.create(
            token=str(token),
            user=request.user,
            reason='logout'
        )

        # 감사 로그
        AuthLog.objects.create(
            user=request.user,
            event_type='logout',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )

        return Response({'message': '로그아웃되었습니다.'})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

def get_client_ip(request):
    """클라이언트 IP 주소 추출"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
```

3. URLs 설정
```python
# backend/dashboard/urls.py

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
```

**테스트**:
```python
# tests/test_auth_api.py
@pytest.mark.django_db
def test_login_success(client):
    user = User.objects.create_user(username='testuser', password='TestPassword123!')
    response = client.post('/api/auth/login/', {
        'username': 'testuser',
        'password': 'TestPassword123!'
    })
    assert response.status_code == 200
    assert 'access' in response.data
    assert 'refresh' in response.data
```

---

#### Day 5-6: 역할 기반 권한 제어

**작업 내용**:
1. Custom Permission 클래스
```python
# backend/dashboard/permissions.py

from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    """Admin 역할만 허용"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'

class IsManagerOrAdmin(permissions.BasePermission):
    """Manager 또는 Admin 역할만 허용"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['admin', 'manager']

class IsOwnerOrAdmin(permissions.BasePermission):
    """소유자 또는 Admin만 허용"""
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        return obj.uploaded_by == request.user
```

2. ViewSets에 권한 적용
```python
# backend/dashboard/views.py

from rest_framework import viewsets
from .permissions import IsAdminUser, IsManagerOrAdmin

class DatasetViewSet(viewsets.ModelViewSet):
    queryset = Dataset.objects.all()
    serializer_class = DatasetSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update']:
            return [IsManagerOrAdmin()]
        elif self.action == 'destroy':
            return [IsAdminUser()]
        return [permissions.IsAuthenticated()]

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]  # Admin만 사용자 관리 가능
```

**테스트**:
```python
# tests/test_permissions.py
@pytest.mark.django_db
def test_viewer_cannot_delete_dataset(api_client):
    viewer = User.objects.create_user(username='viewer', password='test', role='viewer')
    dataset = Dataset.objects.create(title='Test', uploaded_by=viewer)

    api_client.force_authenticate(user=viewer)
    response = api_client.delete(f'/api/datasets/{dataset.id}/')
    assert response.status_code == 403
```

---

#### Day 7: 블랙리스트 및 감사 로그 모델

**작업 내용**:
1. 모델 추가
```python
# backend/dashboard/models.py

class BlacklistedToken(models.Model):
    token = models.CharField(max_length=500, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blacklisted_tokens')
    blacklisted_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=100, default='logout')

    class Meta:
        db_table = 'blacklisted_tokens'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', 'blacklisted_at']),
        ]

class AuthLog(models.Model):
    EVENT_TYPES = [
        ('login_success', '로그인 성공'),
        ('login_failure', '로그인 실패'),
        ('token_refresh', '토큰 갱신'),
        ('logout', '로그아웃'),
        ('logout_all', '전체 기기 로그아웃'),
        ('password_change', '비밀번호 변경'),
        ('permission_denied', '권한 거부'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='auth_logs')
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    success = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict)

    class Meta:
        db_table = 'auth_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['event_type', '-timestamp']),
        ]
```

2. 블랙리스트 미들웨어
```python
# backend/dashboard/middleware.py

from rest_framework_simplejwt.exceptions import TokenError
from .models import BlacklistedToken

class TokenBlacklistMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            if BlacklistedToken.objects.filter(token=token).exists():
                # 블랙리스트된 토큰 사용 시 401 반환
                from django.http import JsonResponse
                return JsonResponse({
                    'error': '토큰이 무효화되었습니다.',
                    'code': 'TOKEN_BLACKLISTED'
                }, status=401)

        response = self.get_response(request)
        return response
```

---

### 2.2 Frontend 구현 (Day 8-10)

#### Day 8: Axios Interceptor 및 상태 관리

**작업 내용**:
1. Zustand 스토어 설정
```bash
cd frontend
npm install zustand@^4.5.2 js-cookie@^3.0.5
```

```typescript
// frontend/lib/stores/authStore.ts

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: number
  username: string
  email: string
  role: 'admin' | 'manager' | 'viewer'
  full_name: string
  department: string
}

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  setAuth: (user: User, accessToken: string, refreshToken: string) => void
  clearAuth: () => void
  updateAccessToken: (accessToken: string) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      setAuth: (user, accessToken, refreshToken) =>
        set({ user, accessToken, refreshToken }),
      clearAuth: () =>
        set({ user: null, accessToken: null, refreshToken: null }),
      updateAccessToken: (accessToken) =>
        set({ accessToken }),
    }),
    {
      name: 'auth-storage',
    }
  )
)
```

2. Axios 인스턴스 및 Interceptor
```typescript
// frontend/lib/api/client.ts

import axios from 'axios'
import { useAuthStore } from '@/lib/stores/authStore'

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request Interceptor: Access Token 자동 추가
apiClient.interceptors.request.use(
  (config) => {
    const { accessToken } = useAuthStore.getState()
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response Interceptor: 401 시 자동 토큰 갱신
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // 401 에러이고 재시도하지 않은 경우
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const { refreshToken, updateAccessToken, clearAuth } = useAuthStore.getState()

        if (!refreshToken) {
          clearAuth()
          window.location.href = '/login'
          return Promise.reject(error)
        }

        // Refresh Token으로 새 Access Token 발급
        const response = await axios.post(
          `${apiClient.defaults.baseURL}/auth/token/refresh/`,
          { refresh: refreshToken }
        )

        const newAccessToken = response.data.access
        updateAccessToken(newAccessToken)

        // 원래 요청 재시도
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
        return apiClient(originalRequest)
      } catch (refreshError) {
        // Refresh Token도 만료됨 → 로그아웃
        useAuthStore.getState().clearAuth()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

export default apiClient
```

3. 로그인 API 함수
```typescript
// frontend/lib/api/auth.ts

import apiClient from './client'
import { useAuthStore } from '@/lib/stores/authStore'

export const authApi = {
  login: async (username: string, password: string) => {
    const response = await apiClient.post('/auth/login/', { username, password })
    const { user, access, refresh } = response.data

    useAuthStore.getState().setAuth(user, access, refresh)
    return response.data
  },

  logout: async () => {
    const { refreshToken, clearAuth } = useAuthStore.getState()
    try {
      await apiClient.post('/auth/logout/', { refresh: refreshToken })
    } finally {
      clearAuth()
    }
  },

  getCurrentUser: async () => {
    const response = await apiClient.get('/auth/user/')
    return response.data
  },
}
```

---

#### Day 9: 로그인 페이지 및 Protected Routes

**작업 내용**:
1. 로그인 페이지
```typescript
// frontend/app/login/page.tsx

'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { authApi } from '@/lib/api/auth'

export default function LoginPage() {
  const router = useRouter()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await authApi.login(username, password)
      router.push('/')
    } catch (err: any) {
      setError(err.response?.data?.message || '로그인에 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded-lg shadow-md w-96">
        <h1 className="text-2xl font-bold mb-6">로그인</h1>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-gray-700 mb-2">아이디</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg"
              required
            />
          </div>

          <div className="mb-6">
            <label className="block text-gray-700 mb-2">비밀번호</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-500 text-white py-2 rounded-lg hover:bg-blue-600 disabled:bg-gray-400"
          >
            {loading ? '로그인 중...' : '로그인'}
          </button>
        </form>
      </div>
    </div>
  )
}
```

2. Protected Route HOC
```typescript
// frontend/components/ProtectedRoute.tsx

'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/lib/stores/authStore'

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const { user, accessToken } = useAuthStore()

  useEffect(() => {
    if (!accessToken) {
      router.push('/login')
    }
  }, [accessToken, router])

  if (!accessToken) {
    return <div>Loading...</div>
  }

  return <>{children}</>
}
```

3. 역할 기반 UI 렌더링
```typescript
// frontend/components/RoleGuard.tsx

'use client'

import { useAuthStore } from '@/lib/stores/authStore'

interface RoleGuardProps {
  allowedRoles: ('admin' | 'manager' | 'viewer')[]
  children: React.ReactNode
  fallback?: React.ReactNode
}

export default function RoleGuard({ allowedRoles, children, fallback }: RoleGuardProps) {
  const { user } = useAuthStore()

  if (!user || !allowedRoles.includes(user.role)) {
    return <>{fallback || null}</>
  }

  return <>{children}</>
}
```

**사용 예시**:
```tsx
<RoleGuard allowedRoles={['admin', 'manager']}>
  <button onClick={handleDelete}>삭제</button>
</RoleGuard>

<RoleGuard allowedRoles={['admin']}>
  <Link href="/users">사용자 관리</Link>
</RoleGuard>
```

---

#### Day 10: 통합 테스트 및 버그 수정

**작업 내용**:
- E2E 테스트 시나리오 실행
- 로그인 → API 요청 → 토큰 갱신 → 로그아웃 플로우 검증
- CORS 설정 확인
- 에러 핸들링 개선

---

## 3. 기술 스택 상세

### 3.1 Backend

| 라이브러리 | 버전 | 용도 |
|-----------|------|------|
| Django | 5.0.7 | 웹 프레임워크 |
| djangorestframework | 3.15.2 | REST API |
| djangorestframework-simplejwt | 5.3.1 | JWT 토큰 관리 |
| django-cors-headers | 4.4.0 | CORS 설정 |
| psycopg2-binary | 2.9.9 | PostgreSQL 드라이버 |

### 3.2 Frontend

| 라이브러리 | 버전 | 용도 |
|-----------|------|------|
| Next.js | 14.2.5 | React 프레임워크 |
| axios | 1.7.2 | HTTP 클라이언트 |
| zustand | 4.5.2 | 상태 관리 |
| js-cookie | 3.0.5 | 쿠키 관리 (옵션) |

---

## 4. 디렉토리 구조

```
backend/
├── dashboard/
│   ├── models.py (User, BlacklistedToken, AuthLog)
│   ├── serializers.py (UserSerializer, LoginSerializer)
│   ├── views.py (login_view, logout_view)
│   ├── permissions.py (IsAdminUser, IsManagerOrAdmin)
│   ├── middleware.py (TokenBlacklistMiddleware)
│   └── urls.py
├── config/
│   ├── settings.py (SIMPLE_JWT 설정)
│   └── urls.py
└── tests/
    ├── test_models.py
    ├── test_auth_api.py
    └── test_permissions.py

frontend/
├── app/
│   ├── login/
│   │   └── page.tsx
│   └── layout.tsx
├── lib/
│   ├── api/
│   │   ├── client.ts (Axios interceptor)
│   │   └── auth.ts (authApi)
│   └── stores/
│       └── authStore.ts (Zustand)
└── components/
    ├── ProtectedRoute.tsx
    └── RoleGuard.tsx
```

---

## 5. 테스트 계획

### 5.1 Backend 테스트

**Unit Tests** (pytest):
- 모델 테스트 (User, BlacklistedToken, AuthLog)
- Serializer 검증
- Permission 클래스

**Integration Tests** (pytest-django):
- 로그인 API (성공/실패)
- 토큰 갱신 API
- 로그아웃 API
- 역할 기반 권한 검증

**테스트 커버리지 목표**: ≥ 90%

### 5.2 Frontend 테스트

**Unit Tests** (Vitest):
- Zustand 스토어 상태 변경
- API 함수 모킹

**Integration Tests**:
- Axios interceptor 동작 확인
- 토큰 자동 갱신 플로우

---

## 6. 배포 전략

### 6.1 Railway 배포 설정

1. 환경 변수 추가
```bash
SECRET_KEY=<256-bit-random-key>
SIMPLE_JWT_SIGNING_KEY=<same-as-secret-key>
```

2. CORS 설정
```python
# settings.py
CORS_ALLOWED_ORIGINS = [
    'https://your-frontend.vercel.app',
]
```

3. 마이그레이션 자동 실행
```bash
# Procfile
release: python manage.py migrate
web: gunicorn config.wsgi
```

### 6.2 Vercel 배포

1. 환경 변수
```
NEXT_PUBLIC_API_URL=https://your-backend.railway.app/api
```

---

## 7. 리스크 및 대응 방안

| 리스크 | 영향도 | 대응 방안 |
|-------|--------|----------|
| 기존 세션 인증과 충돌 | 중간 | Phase 1에서 병행 사용, Phase 3에서 제거 |
| Refresh Token 블랙리스트 성능 | 중간 | 인덱스 생성, 만료 토큰 주기적 삭제 |
| CORS 설정 오류 | 낮음 | django-cors-headers 사용, 명시적 origin 지정 |
| JWT 시크릿 키 노출 | 높음 | 환경 변수 사용, .gitignore 확인 |

---

## 8. 타임라인

| 기간 | 작업 내용 | 담당 | 상태 |
|------|----------|------|------|
| Day 1-2 | Backend 환경 설정, User 모델 확장 | Backend | Pending |
| Day 3-4 | JWT 인증 API 구현 | Backend | Pending |
| Day 5-6 | 역할 기반 권한 제어 | Backend | Pending |
| Day 7 | 블랙리스트 및 감사 로그 | Backend | Pending |
| Day 8 | Frontend Axios interceptor | Frontend | Pending |
| Day 9 | 로그인 페이지, Protected Routes | Frontend | Pending |
| Day 10 | 통합 테스트 및 배포 | Full-stack | Pending |

---

## 9. 다음 단계

1. ✅ **spec.md** 작성 완료
2. ✅ **plan.md** 작성 완료
3. ⏳ **acceptance.md** 작성 (다음)
4. ⏳ Git 브랜치 생성 및 커밋
5. ⏳ TDD 구현 시작 (alfred:2-run)

---

_이 문서는 MoAI-ADK 표준을 따릅니다._
_작성일: 2025-11-03 by @Sam_
_@TAG: @PLAN:AUTH-001_

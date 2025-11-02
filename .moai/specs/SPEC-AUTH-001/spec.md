# SPEC-AUTH-001: JWT 기반 사용자 인증 시스템

**Status**: Draft
**Created**: 2025-11-03
**Author**: @Sam
**Tech Lead**: 🎩 Alfred@[MoAI](https://adk.mo.ai.kr)
**Priority**: Critical
**Complexity**: 3/5
**Estimated Duration**: 2 weeks

---

## 1. Overview

### 1.1 Purpose
Django 세션 기반 인증을 JWT (JSON Web Token) 기반 Stateless 인증으로 전환하여 확장 가능한 다중 사용자 시스템을 구축합니다. 역할 기반 접근 제어(RBAC)를 통해 Admin, Manager, Viewer 권한을 구분하고, 마이크로서비스 아키텍처 전환을 위한 기반을 마련합니다.

### 1.2 Business Value
- **보안 강화**: Stateless 인증으로 세션 하이재킹 위험 감소
- **확장성**: 다중 서버 환경에서 세션 공유 불필요
- **사용자 경험**: 자동 토큰 갱신으로 로그인 유지 (최대 7일)
- **다중 사용자 지원**: 조직 내 여러 사용자 및 역할 관리

### 1.3 Dependencies
- **선행 조건**: SPEC-DASH-001 완료 (기본 인증 시스템 존재)
- **연관 SPEC**:
  - SPEC-EXPORT-001: 역할별 내보내기 권한 제어
  - SPEC-FILTER-001: 사용자별 필터 프리셋 저장

### 1.4 Tech Stack
- **Backend**: Django REST Framework Simple JWT 5.3.1
- **Frontend**: Axios 1.7.2 (interceptors), Zustand 4.5.2 (state management)
- **Database**: PostgreSQL (기존 User 모델 확장)
- **Security**: bcrypt 패스워드 해싱, HTTP-only 쿠키 (옵션)

### 1.5 Success Criteria
- ✅ 모든 API 엔드포인트에서 JWT 토큰 검증 통과
- ✅ Access Token 만료 시 자동 갱신 성공률 100%
- ✅ 역할별 권한 제어 정상 작동 (Admin/Manager/Viewer)
- ✅ 로그아웃 시 Refresh Token 무효화 및 재사용 불가
- ✅ pytest 테스트 커버리지 ≥ 90%
- ✅ 보안 감사 통과 (OWASP Top 10 기준)

---

## 2. Functional Requirements (EARS Format)

### 2.1 토큰 발급 및 인증

**@SPEC:REQ-AUTH-001** - JWT 토큰 발급
- **WHEN** 사용자가 유효한 username/password로 로그인 요청을 하면
- **THE SYSTEM SHALL** Django User 모델에서 자격 증명을 검증하고
- **AND** 검증 성공 시 다음 토큰을 발급하며
  - **Access Token**: 15분 유효, API 요청 인증용
  - **Refresh Token**: 7일 유효, Access Token 갱신용
- **AND** 응답 본문에 토큰과 사용자 정보를 JSON으로 반환한다
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@university.edu",
    "role": "admin",
    "full_name": "김관리자"
  }
}
```

**@SPEC:REQ-AUTH-002** - 토큰 기반 API 인증
- **WHEN** 클라이언트가 보호된 API 엔드포인트에 요청하면
- **THE SYSTEM SHALL** HTTP Authorization 헤더에서 Bearer 토큰을 추출하고
  ```
  Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
  ```
- **AND** 토큰의 서명(signature)을 검증하며
- **AND** 토큰의 만료 시간(exp)을 확인하고
- **IF** 토큰이 유효하면 요청을 처리하며
- **ELSE IF** 토큰이 만료되었으면 401 Unauthorized 반환
  ```json
  {
    "detail": "Given token not valid for any token type",
    "code": "token_not_valid",
    "messages": [{"token_class": "AccessToken", "token_type": "access", "message": "Token is expired"}]
  }
  ```
- **ELSE** 토큰이 유효하지 않으면 401 Unauthorized 반환

**@SPEC:REQ-AUTH-003** - Access Token 자동 갱신
- **WHEN** Access Token이 만료되고 클라이언트가 유효한 Refresh Token을 제출하면
- **THE SYSTEM SHALL** Refresh Token의 유효성을 검증하고
- **AND** 블랙리스트에 등록되지 않았는지 확인하며
- **AND** 새로운 Access Token을 발급하여 반환한다
- **AND** 프론트엔드 Axios interceptor가 자동으로 재요청을 수행한다

**@SPEC:REQ-AUTH-004** - Refresh Token 갱신
- **WHEN** Refresh Token이 만료 3일 전이고 사용자가 활성 상태이면
- **THE SYSTEM SHALL** 새로운 Refresh Token을 발급하고
- **AND** 기존 Refresh Token을 블랙리스트에 추가하며
- **AND** 프론트엔드에 새 토큰 저장을 안내한다

### 2.2 사용자 역할 및 권한

**@SPEC:REQ-AUTH-005** - 역할 기반 접근 제어 (RBAC)
- **THE SYSTEM SHALL** 다음 3가지 사용자 역할을 정의하고
  - **Admin**: 모든 권한 (CRUD, 사용자 관리, 설정 변경)
  - **Manager**: 데이터 CRUD, 내보내기 (사용자 관리 제외)
  - **Viewer**: 조회 및 필터링만 가능 (생성/수정/삭제 불가)
- **AND** User 모델에 `role` 필드를 추가하며
```python
class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('viewer', 'Viewer'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer')
    full_name = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
```
- **AND** JWT 토큰 payload에 역할 정보를 포함한다
```json
{
  "token_type": "access",
  "exp": 1699000000,
  "iat": 1698999100,
  "jti": "abc123...",
  "user_id": 1,
  "username": "admin",
  "role": "admin"
}
```

**@SPEC:REQ-AUTH-006** - 엔드포인트별 권한 검증
- **WHEN** 사용자가 특정 API 엔드포인트에 요청하면
- **THE SYSTEM SHALL** DRF Permission 클래스로 역할을 확인하고
- **IF** 필요한 권한이 없으면 403 Forbidden을 반환하며
  ```json
  {
    "detail": "You do not have permission to perform this action.",
    "required_role": "admin",
    "current_role": "viewer"
  }
  ```
- **ELSE** 요청을 정상 처리한다

**권한 매트릭스**:
| 엔드포인트 | Admin | Manager | Viewer |
|-----------|-------|---------|--------|
| GET /api/datasets/ | ✅ | ✅ | ✅ |
| POST /api/datasets/ | ✅ | ✅ | ❌ |
| PUT /api/datasets/{id}/ | ✅ | ✅ | ❌ |
| DELETE /api/datasets/{id}/ | ✅ | ❌ | ❌ |
| POST /api/datasets/upload/ | ✅ | ✅ | ❌ |
| POST /api/export/ | ✅ | ✅ | ❌ |
| GET /api/users/ | ✅ | ❌ | ❌ |
| POST /api/users/ | ✅ | ❌ | ❌ |

### 2.3 로그아웃 및 토큰 무효화

**@SPEC:REQ-AUTH-007** - 로그아웃 처리
- **WHEN** 사용자가 로그아웃 요청을 하면
- **THE SYSTEM SHALL** Refresh Token을 블랙리스트 테이블에 추가하고
```python
class BlacklistedToken(models.Model):
    token = models.CharField(max_length=500, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    blacklisted_at = models.DateTimeField(auto_now_add=True)
```
- **AND** 프론트엔드에서 localStorage 또는 쿠키의 토큰을 삭제하며
- **AND** 로그인 페이지로 리디렉션한다
- **AND** 블랙리스트된 토큰으로 재요청 시 401 반환

**@SPEC:REQ-AUTH-008** - 전체 기기 로그아웃
- **WHEN** 사용자가 "모든 기기에서 로그아웃" 요청을 하면
- **THE SYSTEM SHALL** 해당 사용자의 모든 Refresh Token을 블랙리스트에 추가하고
- **AND** 모든 기기에서 다음 API 요청 시 재로그인을 요구한다

### 2.4 비밀번호 관리

**@SPEC:REQ-AUTH-009** - 비밀번호 변경
- **WHEN** 인증된 사용자가 비밀번호 변경을 요청하면
- **THE SYSTEM SHALL** 현재 비밀번호를 검증하고
- **AND** 새 비밀번호 강도를 확인하며 (최소 8자, 대소문자+숫자+특수문자)
- **AND** Django의 `make_password()`로 해싱하여 저장하고
- **AND** 모든 기존 Refresh Token을 무효화한다

**@SPEC:REQ-AUTH-010** - 비밀번호 재설정
- **WHEN** 사용자가 비밀번호 분실 시 재설정 요청을 하면
- **THE SYSTEM SHALL** 이메일로 재설정 링크를 전송하고 (1시간 유효)
- **AND** 토큰 검증 후 새 비밀번호 설정을 허용하며
- **AND** 기존 모든 세션 및 토큰을 무효화한다

---

## 3. Non-Functional Requirements

### 3.1 보안 (Security)

**@SPEC:NFR-AUTH-001** - 토큰 보안
- **THE SYSTEM SHALL** JWT 토큰을 HS256 알고리즘으로 서명하고
- **AND** SECRET_KEY는 환경 변수로 관리하며 (최소 256비트)
- **AND** Refresh Token을 HTTP-only 쿠키에 저장하는 옵션을 제공한다 (XSS 방지)

**@SPEC:NFR-AUTH-002** - 비밀번호 보안
- **THE SYSTEM SHALL** Django의 PBKDF2 해싱 (기본 600,000 iterations)을 사용하고
- **AND** 비밀번호 강도 검증을 필수로 적용하며
- **AND** 로그인 실패 시 사용자명/비밀번호 중 어느 것이 틀렸는지 노출하지 않는다

**@SPEC:NFR-AUTH-003** - Brute Force 방지
- **THE SYSTEM SHALL** 동일 IP에서 5회 로그인 실패 시 15분간 차단하고
- **AND** django-ratelimit 또는 DRF Throttling을 적용하며
- **AND** 차단 이벤트를 로그에 기록한다

### 3.2 성능 (Performance)

**@SPEC:NFR-AUTH-004** - 토큰 검증 성능
- **THE SYSTEM SHALL** JWT 토큰 검증을 10ms 이내 완료하고
- **AND** 블랙리스트 조회를 위해 인덱스를 생성하며
```sql
CREATE INDEX idx_blacklisted_token ON blacklistedtoken(token);
CREATE INDEX idx_blacklisted_user_date ON blacklistedtoken(user_id, blacklisted_at);
```
- **AND** 만료된 블랙리스트 항목을 주기적으로 삭제한다 (Celery task)

**@SPEC:NFR-AUTH-005** - 확장성
- **THE SYSTEM SHALL** Stateless 인증으로 수평 확장(scale-out)을 지원하고
- **AND** 서버 간 세션 공유 없이 독립적으로 토큰을 검증하며
- **AND** 초당 1,000개 토큰 검증 요청을 처리한다

### 3.3 사용성 (Usability)

**@SPEC:NFR-AUTH-006** - 자동 로그인 유지
- **THE SYSTEM SHALL** "로그인 상태 유지" 옵션 선택 시 Refresh Token 유효 기간을 30일로 연장하고
- **AND** Access Token 만료 시 사용자 경험 중단 없이 자동 갱신하며
- **AND** 네트워크 오류 시 재시도 로직을 적용한다 (최대 3회)

**@SPEC:NFR-AUTH-007** - 명확한 에러 메시지
- **THE SYSTEM SHALL** 인증 실패 시 사용자 친화적인 한글 메시지를 반환하고
```json
{
  "error": "인증 실패",
  "message": "아이디 또는 비밀번호가 올바르지 않습니다.",
  "code": "INVALID_CREDENTIALS"
}
```
- **AND** 토큰 만료 시 재로그인 안내를 표시하며
- **AND** 권한 부족 시 필요한 역할을 명시한다

### 3.4 감사 추적 (Audit Trail)

**@SPEC:NFR-AUTH-008** - 인증 로그
- **THE SYSTEM SHALL** 다음 이벤트를 로그 테이블에 기록하고
  - 로그인 성공/실패 (IP 주소, User-Agent, 시각)
  - 토큰 갱신 (Access/Refresh)
  - 로그아웃 (일반/전체 기기)
  - 비밀번호 변경/재설정
  - 권한 거부 (403 이벤트)
```python
class AuthLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    event_type = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    success = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict)
```
- **AND** Admin 사용자는 감사 로그를 조회할 수 있다

---

## 4. Data Model

### 4.1 User 모델 확장

```python
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """확장된 사용자 모델 (역할 및 프로필 정보 추가)"""

    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('viewer', 'Viewer'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='viewer',
        help_text="사용자 역할"
    )
    full_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="전체 이름"
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        help_text="부서"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="전화번호"
    )

    # 보안 필드
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    failed_login_attempts = models.IntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'auth_user_extended'
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['department']),
        ]

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def has_role(self, role_name):
        """역할 확인 헬퍼 메서드"""
        return self.role == role_name

    def is_admin(self):
        return self.role == 'admin'

    def is_manager_or_above(self):
        return self.role in ['admin', 'manager']
```

### 4.2 블랙리스트 모델

```python
class BlacklistedToken(models.Model):
    """로그아웃된 Refresh Token 블랙리스트"""

    token = models.CharField(
        max_length=500,
        unique=True,
        help_text="블랙리스트된 Refresh Token"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='blacklisted_tokens',
        help_text="토큰 소유자"
    )
    blacklisted_at = models.DateTimeField(
        auto_now_add=True,
        help_text="블랙리스트 추가 시각"
    )
    reason = models.CharField(
        max_length=100,
        default='logout',
        help_text="블랙리스트 사유 (logout, password_change, admin_revoke)"
    )

    class Meta:
        db_table = 'blacklisted_tokens'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', 'blacklisted_at']),
        ]

    def __str__(self):
        return f"Blacklisted token for {self.user.username}"
```

### 4.3 감사 로그 모델

```python
class AuthLog(models.Model):
    """인증 관련 이벤트 로그"""

    EVENT_TYPES = [
        ('login_success', '로그인 성공'),
        ('login_failure', '로그인 실패'),
        ('token_refresh', '토큰 갱신'),
        ('logout', '로그아웃'),
        ('logout_all', '전체 기기 로그아웃'),
        ('password_change', '비밀번호 변경'),
        ('password_reset', '비밀번호 재설정'),
        ('permission_denied', '권한 거부'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='auth_logs'
    )
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
            models.Index(fields=['ip_address', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.user} @ {self.timestamp}"
```

---

## 5. API Endpoints

### 5.1 인증 엔드포인트

#### POST /api/auth/login/
**설명**: 사용자 로그인 및 JWT 토큰 발급

**Request**:
```json
{
  "username": "admin",
  "password": "SecurePassword123!"
}
```

**Response (200 OK)**:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@university.edu",
    "role": "admin",
    "full_name": "김관리자",
    "department": "정보전산팀"
  }
}
```

**Response (401 Unauthorized)**:
```json
{
  "error": "인증 실패",
  "message": "아이디 또는 비밀번호가 올바르지 않습니다.",
  "code": "INVALID_CREDENTIALS"
}
```

---

#### POST /api/auth/token/refresh/
**설명**: Refresh Token으로 새로운 Access Token 발급

**Request**:
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response (200 OK)**:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

#### POST /api/auth/logout/
**설명**: 로그아웃 및 Refresh Token 무효화

**Request**:
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response (200 OK)**:
```json
{
  "message": "로그아웃되었습니다."
}
```

---

#### POST /api/auth/logout-all/
**설명**: 모든 기기에서 로그아웃

**Headers**: `Authorization: Bearer {access_token}`

**Response (200 OK)**:
```json
{
  "message": "모든 기기에서 로그아웃되었습니다.",
  "revoked_tokens": 3
}
```

---

### 5.2 사용자 관리 엔드포인트 (Admin only)

#### GET /api/users/
**설명**: 사용자 목록 조회 (Admin만)

**Response (200 OK)**:
```json
{
  "count": 15,
  "results": [
    {
      "id": 1,
      "username": "admin",
      "email": "admin@university.edu",
      "role": "admin",
      "full_name": "김관리자",
      "department": "정보전산팀",
      "last_login": "2025-11-03T10:30:00Z"
    }
  ]
}
```

---

#### POST /api/users/
**설명**: 새 사용자 생성 (Admin만)

**Request**:
```json
{
  "username": "newuser",
  "email": "newuser@university.edu",
  "password": "SecurePassword123!",
  "role": "manager",
  "full_name": "박매니저",
  "department": "행정팀"
}
```

---

#### PATCH /api/users/{id}/change-role/
**설명**: 사용자 역할 변경 (Admin만)

**Request**:
```json
{
  "role": "viewer"
}
```

---

### 5.3 비밀번호 관리 엔드포인트

#### POST /api/auth/password/change/
**설명**: 비밀번호 변경

**Request**:
```json
{
  "old_password": "OldPassword123!",
  "new_password": "NewSecurePassword456!"
}
```

---

#### POST /api/auth/password/reset/request/
**설명**: 비밀번호 재설정 이메일 전송

**Request**:
```json
{
  "email": "admin@university.edu"
}
```

---

## 6. Security Considerations

### 6.1 토큰 저장 전략

**Option 1: localStorage (기본)**
- **장점**: 구현 간단, CORS 문제 없음
- **단점**: XSS 취약점 존재
- **권장**: CSP (Content Security Policy) 헤더로 XSS 완화

**Option 2: HTTP-only 쿠키**
- **장점**: XSS 공격 방지
- **단점**: CSRF 토큰 필요, SameSite 설정 복잡
- **권장**: 프로덕션 환경에서 권장

### 6.2 OWASP Top 10 대응

| 위협 | 대응 방안 |
|------|-----------|
| A01:2021 - Broken Access Control | 역할 기반 권한 검증, DRF Permissions |
| A02:2021 - Cryptographic Failures | HTTPS 강제, JWT HS256 서명 |
| A03:2021 - Injection | Django ORM 사용, 파라미터 검증 |
| A05:2021 - Security Misconfiguration | SECRET_KEY 환경 변수, DEBUG=False |
| A07:2021 - Identification Failures | JWT 토큰, 비밀번호 강도 검증 |

### 6.3 Rate Limiting

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '5/minute',  # 로그인 시도
        'user': '1000/hour'  # 일반 API 요청
    }
}
```

---

## 7. Testing Strategy

### 7.1 Backend Testing (pytest)

**테스트 커버리지 목표**: ≥ 90%

**주요 테스트 케이스**:
```python
# tests/test_auth.py

def test_login_success():
    """유효한 자격 증명으로 로그인 시 토큰 발급"""
    response = client.post('/api/auth/login/', {
        'username': 'testuser',
        'password': 'TestPassword123!'
    })
    assert response.status_code == 200
    assert 'access' in response.data
    assert 'refresh' in response.data

def test_login_failure_invalid_credentials():
    """잘못된 비밀번호로 로그인 시 401 반환"""
    response = client.post('/api/auth/login/', {
        'username': 'testuser',
        'password': 'WrongPassword'
    })
    assert response.status_code == 401

def test_api_access_with_valid_token():
    """유효한 Access Token으로 API 접근 성공"""
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    response = client.get('/api/datasets/')
    assert response.status_code == 200

def test_api_access_with_expired_token():
    """만료된 Access Token으로 API 접근 시 401 반환"""
    # 만료된 토큰 생성 로직
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {expired_token}')
    response = client.get('/api/datasets/')
    assert response.status_code == 401

def test_token_refresh_success():
    """유효한 Refresh Token으로 Access Token 갱신 성공"""
    response = client.post('/api/auth/token/refresh/', {
        'refresh': refresh_token
    })
    assert response.status_code == 200
    assert 'access' in response.data

def test_logout_blacklists_token():
    """로그아웃 시 Refresh Token이 블랙리스트에 추가"""
    response = client.post('/api/auth/logout/', {
        'refresh': refresh_token
    })
    assert response.status_code == 200
    assert BlacklistedToken.objects.filter(token=refresh_token).exists()

def test_role_based_access_admin_only():
    """Admin만 사용자 목록 조회 가능"""
    # Manager로 로그인
    manager_token = login_as('manager')
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {manager_token}')
    response = client.get('/api/users/')
    assert response.status_code == 403

def test_brute_force_protection():
    """5회 로그인 실패 시 계정 잠금"""
    for _ in range(5):
        client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'WrongPassword'
        })

    response = client.post('/api/auth/login/', {
        'username': 'testuser',
        'password': 'TestPassword123!'
    })
    assert response.status_code == 429  # Too Many Requests
```

### 7.2 Frontend Testing (Vitest)

**주요 테스트 케이스**:
```typescript
// tests/auth.test.ts

describe('Axios Interceptor - Token Refresh', () => {
  it('자동으로 만료된 Access Token을 갱신', async () => {
    // Mock expired token response
    mock.onGet('/api/datasets/').replyOnce(401)
    mock.onPost('/api/auth/token/refresh/').replyOnce(200, {
      access: 'new_access_token'
    })
    mock.onGet('/api/datasets/').replyOnce(200, { results: [] })

    const response = await apiClient.get('/api/datasets/')
    expect(response.status).toBe(200)
  })
})

describe('Role-based UI Rendering', () => {
  it('Viewer는 삭제 버튼을 볼 수 없음', () => {
    const { queryByText } = render(<DataTable />, {
      initialState: { user: { role: 'viewer' } }
    })
    expect(queryByText('삭제')).toBeNull()
  })

  it('Admin은 모든 액션 버튼을 볼 수 있음', () => {
    const { getByText } = render(<DataTable />, {
      initialState: { user: { role: 'admin' } }
    })
    expect(getByText('삭제')).toBeInTheDocument()
    expect(getByText('수정')).toBeInTheDocument()
  })
})
```

---

## 8. Migration Strategy

### 8.1 기존 Django 세션 인증에서 JWT로 전환

**Phase 1**: JWT 인증 시스템 추가 (기존 세션 인증 유지)
- Django Simple JWT 설치 및 설정
- User 모델 확장 (role 필드 추가)
- JWT 엔드포인트 추가

**Phase 2**: 프론트엔드 JWT 통합
- Axios interceptor 구현
- Zustand 상태 관리 추가
- 기존 세션 쿠키와 JWT 병행 사용

**Phase 3**: JWT 완전 전환
- 모든 API 엔드포인트에서 JWT 검증 필수화
- 세션 인증 제거
- 마이그레이션 공지 및 사용자 재로그인 안내

### 8.2 데이터베이스 마이그레이션

```bash
# 1. User 모델 확장
python manage.py makemigrations
python manage.py migrate

# 2. 기본 역할 할당 (기존 사용자)
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> User.objects.filter(is_superuser=True).update(role='admin')
>>> User.objects.filter(is_staff=True, is_superuser=False).update(role='manager')
>>> User.objects.filter(is_staff=False).update(role='viewer')

# 3. 블랙리스트 및 로그 테이블 생성
python manage.py migrate
```

---

## 9. Out of Scope (v1.0)

다음 기능은 SPEC-AUTH-001에 포함되지 않으며, 향후 SPEC에서 다룹니다:

- **OAuth 2.0 통합** (Google, Microsoft SSO): SPEC-AUTH-002
- **다단계 인증 (MFA/2FA)**: SPEC-AUTH-003
- **API Key 기반 인증** (서드파티 통합용): SPEC-AUTH-004
- **세션 관리 대시보드** (활성 세션 조회/종료): SPEC-USER-001
- **사용자 활동 분석**: SPEC-ANALYTICS-001

---

## 10. References

- **Django REST Framework Simple JWT**: https://django-rest-framework-simplejwt.readthedocs.io/
- **JWT Introduction**: https://jwt.io/introduction
- **OWASP Authentication Cheat Sheet**: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
- **OWASP Top 10 (2021)**: https://owasp.org/Top10/
- **Django Security Best Practices**: https://docs.djangoproject.com/en/5.0/topics/security/
- **Axios Interceptors**: https://axios-http.com/docs/interceptors
- **Zustand State Management**: https://docs.pmnd.rs/zustand/getting-started/introduction

---

## 11. Acceptance Criteria Summary

SPEC-AUTH-001은 다음 조건을 모두 만족할 때 완료로 간주합니다:

- ✅ **REQ-AUTH-001 ~ REQ-AUTH-010**: 모든 기능 요구사항 구현 및 검증
- ✅ **NFR-AUTH-001 ~ NFR-AUTH-008**: 모든 비기능 요구사항 충족
- ✅ **pytest 테스트 커버리지**: ≥ 90%
- ✅ **Vitest 테스트 통과**: 모든 프론트엔드 테스트 성공
- ✅ **보안 감사**: OWASP Top 10 기준 검증
- ✅ **성능 테스트**: 초당 1,000개 토큰 검증 처리
- ✅ **문서화**: API 문서, 사용자 가이드, 배포 가이드 작성
- ✅ **Railway 배포**: 프로덕션 환경에서 JWT 인증 정상 작동

---

_이 문서는 MoAI-ADK 표준을 따릅니다._
_작성일: 2025-11-03 by @Sam_
_@TAG: @SPEC:AUTH-001_

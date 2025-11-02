# SPEC-AUTH-001 수락 기준 (Acceptance Criteria)

**SPEC ID**: SPEC-AUTH-001
**작성일**: 2025-11-03
**작성자**: @Sam
**버전**: 1.0.0

---

## 📋 목차

1. [개요](#1-개요)
2. [기능별 수락 기준](#2-기능별-수락-기준)
3. [테스트 시나리오](#3-테스트-시나리오)
4. [성능 벤치마크](#4-성능-벤치마크)
5. [보안 검증](#5-보안-검증)
6. [사용자 시나리오](#6-사용자-시나리오)
7. [체크리스트](#7-체크리스트)

---

## 1. 개요

### 1.1 목적
SPEC-AUTH-001이 완료되었음을 판단하기 위한 **명확하고 측정 가능한 기준**을 정의합니다. 모든 수락 기준이 충족되어야 SPEC이 완료로 간주됩니다.

### 1.2 검증 방법
- **자동 테스트**: pytest, Vitest로 검증 가능한 기준
- **수동 테스트**: QA 팀 또는 개발자가 직접 확인
- **성능 테스트**: 벤치마크 도구로 측정
- **보안 감사**: OWASP ZAP, Burp Suite 등 도구 사용

### 1.3 완료 정의 (Definition of Done)
✅ 모든 기능 요구사항 (REQ-AUTH-001 ~ REQ-AUTH-010) 구현
✅ 모든 비기능 요구사항 (NFR-AUTH-001 ~ NFR-AUTH-008) 충족
✅ pytest 테스트 커버리지 ≥ 90%
✅ Vitest 테스트 100% 통과
✅ 보안 감사 통과 (OWASP Top 10 기준)
✅ 성능 벤치마크 목표 달성
✅ 문서화 완료 (API 문서, 사용자 가이드, 배포 가이드)
✅ Railway 프로덕션 환경 배포 성공

---

## 2. 기능별 수락 기준

### 2.1 REQ-AUTH-001: JWT 토큰 발급

#### ✅ AC-AUTH-001.1: 유효한 자격 증명으로 로그인 성공
**Given**: 데이터베이스에 사용자 `testuser` (비밀번호: `TestPassword123!`)가 존재
**When**: POST `/api/auth/login/` 요청
```json
{
  "username": "testuser",
  "password": "TestPassword123!"
}
```
**Then**:
- HTTP 200 OK 응답
- 응답 본문에 `access` 토큰 포함 (JWT 형식)
- 응답 본문에 `refresh` 토큰 포함 (JWT 형식)
- 응답 본문에 `user` 객체 포함 (id, username, email, role, full_name, department)
- Access Token 유효 기간: 15분
- Refresh Token 유효 기간: 7일
- 토큰 payload에 `role` claim 포함

**테스트 코드**:
```python
@pytest.mark.django_db
def test_login_success_returns_jwt_tokens(client):
    user = User.objects.create_user(
        username='testuser',
        password='TestPassword123!',
        role='manager'
    )
    response = client.post('/api/auth/login/', {
        'username': 'testuser',
        'password': 'TestPassword123!'
    })

    assert response.status_code == 200
    assert 'access' in response.data
    assert 'refresh' in response.data
    assert 'user' in response.data

    # JWT 토큰 형식 확인
    import jwt
    access_token = jwt.decode(
        response.data['access'],
        settings.SECRET_KEY,
        algorithms=['HS256']
    )
    assert access_token['user_id'] == user.id
    assert access_token['role'] == 'manager'
```

---

#### ✅ AC-AUTH-001.2: 잘못된 비밀번호로 로그인 실패
**Given**: 데이터베이스에 사용자 `testuser`가 존재
**When**: 잘못된 비밀번호로 로그인 시도
**Then**:
- HTTP 401 Unauthorized 응답
- 에러 메시지: "아이디 또는 비밀번호가 올바르지 않습니다."
- 토큰 발급되지 않음
- `failed_login_attempts` 카운터 증가

**테스트 코드**:
```python
@pytest.mark.django_db
def test_login_failure_invalid_password(client):
    user = User.objects.create_user(username='testuser', password='TestPassword123!')
    response = client.post('/api/auth/login/', {
        'username': 'testuser',
        'password': 'WrongPassword'
    })

    assert response.status_code == 401
    assert response.data['code'] == 'INVALID_CREDENTIALS'
    assert 'access' not in response.data

    user.refresh_from_db()
    assert user.failed_login_attempts == 1
```

---

#### ✅ AC-AUTH-001.3: 존재하지 않는 사용자로 로그인 실패
**Given**: 사용자 `nonexistent`가 데이터베이스에 없음
**When**: 로그인 시도
**Then**:
- HTTP 401 Unauthorized 응답
- 동일한 에러 메시지 (보안상 사용자 존재 여부 노출 금지)

---

### 2.2 REQ-AUTH-002: 토큰 기반 API 인증

#### ✅ AC-AUTH-002.1: 유효한 Access Token으로 API 접근 성공
**Given**: 로그인하여 발급받은 유효한 Access Token
**When**: Authorization 헤더에 Bearer 토큰을 포함하여 GET `/api/datasets/` 요청
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```
**Then**:
- HTTP 200 OK 응답
- 데이터셋 목록 정상 반환

**테스트 코드**:
```python
@pytest.mark.django_db
def test_api_access_with_valid_token(api_client):
    user = User.objects.create_user(username='testuser', password='test', role='manager')
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    response = api_client.get('/api/datasets/')

    assert response.status_code == 200
```

---

#### ✅ AC-AUTH-002.2: 만료된 Access Token으로 API 접근 실패
**Given**: 15분 이상 경과하여 만료된 Access Token
**When**: API 요청
**Then**:
- HTTP 401 Unauthorized 응답
- 에러 코드: `token_not_valid`
- 에러 메시지: "Token is expired"

**테스트 코드**:
```python
@pytest.mark.django_db
def test_api_access_with_expired_token(api_client):
    user = User.objects.create_user(username='testuser', password='test')

    # 만료된 토큰 생성 (15분 전)
    from datetime import timedelta
    from django.utils import timezone
    from rest_framework_simplejwt.tokens import AccessToken

    token = AccessToken.for_user(user)
    token.set_exp(from_time=timezone.now() - timedelta(minutes=16))

    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token)}')
    response = api_client.get('/api/datasets/')

    assert response.status_code == 401
    assert 'token_not_valid' in str(response.data)
```

---

#### ✅ AC-AUTH-002.3: 토큰 없이 API 접근 실패
**Given**: Authorization 헤더 없음
**When**: 보호된 API 엔드포인트 요청
**Then**:
- HTTP 401 Unauthorized 응답

---

### 2.3 REQ-AUTH-003: Access Token 자동 갱신

#### ✅ AC-AUTH-003.1: 유효한 Refresh Token으로 Access Token 갱신 성공
**Given**: 유효한 Refresh Token
**When**: POST `/api/auth/token/refresh/` 요청
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```
**Then**:
- HTTP 200 OK 응답
- 새로운 Access Token 반환
- 새 토큰의 유효 기간: 15분

**테스트 코드**:
```python
@pytest.mark.django_db
def test_token_refresh_success(client):
    user = User.objects.create_user(username='testuser', password='test')
    refresh = RefreshToken.for_user(user)
    refresh_token = str(refresh)

    response = client.post('/api/auth/token/refresh/', {
        'refresh': refresh_token
    })

    assert response.status_code == 200
    assert 'access' in response.data
```

---

#### ✅ AC-AUTH-003.2: 블랙리스트된 Refresh Token으로 갱신 실패
**Given**: 로그아웃으로 블랙리스트에 추가된 Refresh Token
**When**: 토큰 갱신 시도
**Then**:
- HTTP 401 Unauthorized 응답

---

#### ✅ AC-AUTH-003.3: Axios Interceptor 자동 갱신 (Frontend)
**Given**: Access Token이 만료되고 유효한 Refresh Token 존재
**When**: 프론트엔드에서 API 요청 시 401 응답 받음
**Then**:
- Axios interceptor가 자동으로 `/api/auth/token/refresh/` 호출
- 새 Access Token 저장
- 원래 요청 재시도
- 사용자 경험 중단 없음

**테스트 코드** (Vitest):
```typescript
describe('Axios Interceptor - Token Refresh', () => {
  it('자동으로 만료된 Access Token을 갱신하고 재요청', async () => {
    const mockAdapter = new MockAdapter(apiClient)

    // 첫 번째 요청: 401 (토큰 만료)
    mockAdapter.onGet('/api/datasets/').replyOnce(401, {
      code: 'token_not_valid'
    })

    // Refresh 요청: 성공
    mockAdapter.onPost('/api/auth/token/refresh/').replyOnce(200, {
      access: 'new_access_token_123'
    })

    // 재시도 요청: 성공
    mockAdapter.onGet('/api/datasets/').replyOnce(200, {
      results: []
    })

    const response = await apiClient.get('/api/datasets/')

    expect(response.status).toBe(200)
    expect(useAuthStore.getState().accessToken).toBe('new_access_token_123')
  })
})
```

---

### 2.4 REQ-AUTH-005: 역할 기반 접근 제어

#### ✅ AC-AUTH-005.1: Admin 역할 권한 확인
**Given**: Admin 역할 사용자로 로그인
**When**: 다음 작업 수행
- GET `/api/users/` (사용자 목록 조회)
- DELETE `/api/datasets/1/` (데이터셋 삭제)
**Then**:
- 모든 요청 성공 (HTTP 200/204)

**테스트 코드**:
```python
@pytest.mark.django_db
def test_admin_can_delete_dataset(api_client):
    admin = User.objects.create_user(username='admin', password='test', role='admin')
    dataset = Dataset.objects.create(title='Test', uploaded_by=admin)

    api_client.force_authenticate(user=admin)
    response = api_client.delete(f'/api/datasets/{dataset.id}/')

    assert response.status_code == 204
```

---

#### ✅ AC-AUTH-005.2: Manager 역할 권한 확인
**Given**: Manager 역할 사용자로 로그인
**When**: 다음 작업 수행
- GET `/api/datasets/` ✅ 성공
- POST `/api/datasets/` ✅ 성공
- PUT `/api/datasets/1/` ✅ 성공
- DELETE `/api/datasets/1/` ❌ **실패** (HTTP 403)
- GET `/api/users/` ❌ **실패** (HTTP 403)
**Then**: 위 예상 결과 일치

**테스트 코드**:
```python
@pytest.mark.django_db
def test_manager_cannot_delete_dataset(api_client):
    manager = User.objects.create_user(username='manager', password='test', role='manager')
    dataset = Dataset.objects.create(title='Test', uploaded_by=manager)

    api_client.force_authenticate(user=manager)
    response = api_client.delete(f'/api/datasets/{dataset.id}/')

    assert response.status_code == 403
    assert 'permission' in str(response.data).lower()
```

---

#### ✅ AC-AUTH-005.3: Viewer 역할 권한 확인
**Given**: Viewer 역할 사용자로 로그인
**When**: 다음 작업 수행
- GET `/api/datasets/` ✅ 성공
- POST `/api/datasets/` ❌ **실패** (HTTP 403)
**Then**: 조회만 가능, 생성/수정/삭제 불가

---

### 2.5 REQ-AUTH-007: 로그아웃 처리

#### ✅ AC-AUTH-007.1: 로그아웃 시 Refresh Token 블랙리스트 추가
**Given**: 로그인된 사용자
**When**: POST `/api/auth/logout/` 요청
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```
**Then**:
- HTTP 200 OK 응답
- `BlacklistedToken` 테이블에 토큰 추가
- 블랙리스트된 토큰으로 재요청 시 401 응답

**테스트 코드**:
```python
@pytest.mark.django_db
def test_logout_blacklists_refresh_token(client):
    user = User.objects.create_user(username='testuser', password='test')
    refresh = RefreshToken.for_user(user)
    refresh_token = str(refresh)

    client.force_login(user)
    response = client.post('/api/auth/logout/', {
        'refresh': refresh_token
    })

    assert response.status_code == 200
    assert BlacklistedToken.objects.filter(token=refresh_token).exists()

    # 블랙리스트된 토큰으로 재사용 시도
    response = client.post('/api/auth/token/refresh/', {
        'refresh': refresh_token
    })
    assert response.status_code == 401
```

---

#### ✅ AC-AUTH-007.2: 로그아웃 감사 로그 기록
**Given**: 로그아웃 요청
**Then**:
- `AuthLog` 테이블에 로그 생성
  - `event_type`: 'logout'
  - `user`: 로그아웃한 사용자
  - `ip_address`: 클라이언트 IP
  - `success`: True

---

### 2.6 REQ-AUTH-009: 비밀번호 변경

#### ✅ AC-AUTH-009.1: 유효한 비밀번호 변경 성공
**Given**: 로그인된 사용자
**When**: POST `/api/auth/password/change/` 요청
```json
{
  "old_password": "OldPassword123!",
  "new_password": "NewSecurePassword456!"
}
```
**Then**:
- HTTP 200 OK 응답
- 기존 모든 Refresh Token 무효화 (블랙리스트 추가)
- 새 비밀번호로 로그인 가능

**테스트 코드**:
```python
@pytest.mark.django_db
def test_password_change_invalidates_all_tokens(api_client):
    user = User.objects.create_user(username='testuser', password='OldPassword123!')
    refresh = RefreshToken.for_user(user)

    api_client.force_authenticate(user=user)
    response = api_client.post('/api/auth/password/change/', {
        'old_password': 'OldPassword123!',
        'new_password': 'NewSecurePassword456!'
    })

    assert response.status_code == 200

    # 기존 토큰 무효화 확인
    response = api_client.post('/api/auth/token/refresh/', {
        'refresh': str(refresh)
    })
    assert response.status_code == 401

    # 새 비밀번호로 로그인 가능
    response = api_client.post('/api/auth/login/', {
        'username': 'testuser',
        'password': 'NewSecurePassword456!'
    })
    assert response.status_code == 200
```

---

#### ✅ AC-AUTH-009.2: 약한 비밀번호 거부
**Given**: 로그인된 사용자
**When**: 약한 비밀번호로 변경 시도 (예: "password123")
**Then**:
- HTTP 400 Bad Request 응답
- 에러 메시지: "대문자/소문자/숫자/특수문자를 포함해야 합니다."

---

### 2.7 NFR-AUTH-003: Brute Force 방지

#### ✅ AC-AUTH-003.1: 5회 로그인 실패 시 계정 잠금
**Given**: 사용자 계정 존재
**When**: 5회 연속 로그인 실패
**Then**:
- `User.account_locked_until` = 현재 시각 + 15분
- 6번째 로그인 시도 시 올바른 비밀번호라도 HTTP 403 응답
- 에러 메시지: "계정이 잠겼습니다. {시각}까지 로그인할 수 없습니다."

**테스트 코드**:
```python
@pytest.mark.django_db
def test_account_locked_after_5_failed_attempts(client):
    user = User.objects.create_user(username='testuser', password='CorrectPassword123!')

    # 5회 로그인 실패
    for _ in range(5):
        client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'WrongPassword'
        })

    user.refresh_from_db()
    assert user.account_locked_until is not None

    # 올바른 비밀번호로도 로그인 불가
    response = client.post('/api/auth/login/', {
        'username': 'testuser',
        'password': 'CorrectPassword123!'
    })
    assert response.status_code == 403
    assert 'ACCOUNT_LOCKED' in response.data['code']
```

---

#### ✅ AC-AUTH-003.2: 15분 후 계정 잠금 자동 해제
**Given**: 계정이 잠긴 상태
**When**: 15분 경과 후 로그인 시도
**Then**:
- 로그인 성공
- `User.account_locked_until` = None
- `User.failed_login_attempts` = 0

---

## 3. 테스트 시나리오

### 3.1 엔드투엔드 시나리오 1: 완전한 인증 플로우

```gherkin
Feature: 완전한 JWT 인증 플로우

Scenario: 사용자 로그인부터 로그아웃까지
  Given 데이터베이스에 사용자 "testuser"가 존재
  When 사용자가 로그인 페이지에서 자격 증명을 입력하고 제출
  Then Access Token과 Refresh Token이 발급됨
  And 사용자 정보가 Zustand 스토어에 저장됨
  And 홈페이지 (/)로 리디렉션됨

  When 사용자가 "/datasets" 페이지를 방문
  Then API 요청이 Access Token과 함께 전송됨
  And 데이터셋 목록이 정상 표시됨

  When 15분 경과하여 Access Token이 만료됨
  And 사용자가 다른 API 요청을 수행
  Then Axios interceptor가 자동으로 토큰을 갱신
  And 원래 요청이 재시도되어 성공

  When 사용자가 로그아웃 버튼을 클릭
  Then Refresh Token이 블랙리스트에 추가됨
  And 로컬 스토리지에서 토큰이 삭제됨
  And 로그인 페이지로 리디렉션됨
```

---

### 3.2 엔드투엔드 시나리오 2: 역할 기반 UI 렌더링

```gherkin
Feature: 역할별 UI 요소 표시

Scenario: Viewer 역할 사용자는 읽기 전용 UI만 표시
  Given Viewer 역할 사용자로 로그인
  When 데이터셋 페이지 방문
  Then "업로드" 버튼이 표시되지 않음
  And "삭제" 버튼이 표시되지 않음
  And "수정" 버튼이 표시되지 않음
  And 데이터 조회 및 필터링만 가능

Scenario: Admin 역할 사용자는 모든 UI 요소 표시
  Given Admin 역할 사용자로 로그인
  When 데이터셋 페이지 방문
  Then "업로드" 버튼이 표시됨
  And "삭제" 버튼이 표시됨
  And "수정" 버튼이 표시됨
  And "사용자 관리" 메뉴가 표시됨
```

---

## 4. 성능 벤치마크

### 4.1 토큰 검증 성능

| 메트릭 | 목표 | 측정 방법 |
|-------|------|----------|
| JWT 토큰 검증 시간 | ≤ 10ms | pytest-benchmark |
| 블랙리스트 조회 시간 | ≤ 5ms | SQL EXPLAIN ANALYZE |
| 동시 토큰 검증 처리량 | ≥ 1,000 req/s | Apache Bench (ab) |

**테스트 코드**:
```python
def test_jwt_verification_performance(benchmark):
    user = User.objects.create_user(username='testuser')
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    def verify_token():
        from rest_framework_simplejwt.tokens import AccessToken
        AccessToken(access_token)

    result = benchmark(verify_token)
    assert result < 0.01  # 10ms 이하
```

---

### 4.2 로그인 API 성능

| 메트릭 | 목표 |
|-------|------|
| 평균 응답 시간 | ≤ 200ms |
| 95th percentile | ≤ 500ms |
| 동시 로그인 처리 | ≥ 100 req/s |

**벤치마크 명령**:
```bash
ab -n 1000 -c 10 -T 'application/json' \
   -p login.json \
   http://localhost:8000/api/auth/login/
```

---

## 5. 보안 검증

### 5.1 OWASP Top 10 (2021) 체크리스트

| 위협 | 대응 방안 | 검증 방법 |
|------|----------|----------|
| **A01 - Broken Access Control** | 역할 기반 권한 검증 | 권한 없는 사용자로 API 호출 시 403 확인 |
| **A02 - Cryptographic Failures** | HTTPS 강제, JWT HS256 서명 | SSL Labs 테스트, 토큰 서명 검증 |
| **A03 - Injection** | Django ORM 사용, 입력 검증 | SQL injection 테스트 |
| **A05 - Security Misconfiguration** | DEBUG=False, SECRET_KEY 환경 변수 | `.env` 파일 확인 |
| **A07 - Identification Failures** | 비밀번호 강도 검증, Brute Force 방지 | 5회 실패 후 잠금 확인 |

---

### 5.2 보안 스캔 도구

**OWASP ZAP 스캔**:
```bash
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t http://localhost:8000/api/ \
  -r zap_report.html
```

**수동 보안 테스트**:
1. JWT 시크릿 키 추측 시도 → 실패 확인
2. Refresh Token 재사용 시도 (블랙리스트 후) → 401 확인
3. CORS 우회 시도 → 차단 확인
4. XSS 공격 시도 (로그인 폼) → 이스케이프 확인

---

## 6. 사용자 시나리오

### 6.1 시나리오 1: 대학교 관리자 일상 업무

**사용자**: 김관리자 (Admin 역할)
**목표**: 새로운 학기 등록 데이터 업로드 및 통계 확인

**단계**:
1. ✅ 오전 9시 로그인 (자동 로그인 유지 체크)
2. ✅ 데이터셋 업로드 (Excel 파일)
3. ✅ 점심시간 후 돌아옴 → Access Token 만료 → 자동 갱신 → 업무 계속
4. ✅ 오후 5시 로그아웃

**검증**:
- 로그인 상태 유지 (7일 Refresh Token)
- 토큰 자동 갱신으로 중단 없음
- 로그아웃 시 모든 토큰 무효화

---

### 6.2 시나리오 2: 교수 (Viewer 역할) 성적 조회

**사용자**: 박교수 (Viewer 역할)
**목표**: 학생 성적 분포 차트 확인

**단계**:
1. ✅ 로그인
2. ✅ 성적 데이터셋 조회
3. ✅ 차트 시각화 확인
4. ❌ 데이터 수정 시도 → 403 에러 → "권한이 없습니다" 메시지

**검증**:
- 읽기 권한만 허용
- 수정/삭제 UI 요소 미표시
- API 레벨 권한 검증

---

### 6.3 시나리오 3: 보안 담당자 감사 로그 확인

**사용자**: 이보안 (Admin 역할)
**목표**: 지난 주 로그인 시도 이력 확인

**단계**:
1. ✅ 로그인
2. ✅ `/admin/auth-logs/` 페이지 방문
3. ✅ 필터: 지난 7일, 이벤트 타입=로그인 실패
4. ✅ 의심스러운 IP 주소 확인 → 해당 계정 잠금

**검증**:
- AuthLog 테이블에 모든 이벤트 기록
- Admin만 감사 로그 접근 가능
- IP 주소, User-Agent 저장

---

## 7. 체크리스트

### 7.1 기능 체크리스트

- [ ] **REQ-AUTH-001**: JWT 토큰 발급 (Access + Refresh)
- [ ] **REQ-AUTH-002**: 토큰 기반 API 인증
- [ ] **REQ-AUTH-003**: Access Token 자동 갱신
- [ ] **REQ-AUTH-004**: Refresh Token 갱신
- [ ] **REQ-AUTH-005**: 역할 기반 접근 제어 (Admin, Manager, Viewer)
- [ ] **REQ-AUTH-006**: 엔드포인트별 권한 검증
- [ ] **REQ-AUTH-007**: 로그아웃 및 토큰 무효화
- [ ] **REQ-AUTH-008**: 전체 기기 로그아웃
- [ ] **REQ-AUTH-009**: 비밀번호 변경
- [ ] **REQ-AUTH-010**: 비밀번호 재설정 (이메일)

---

### 7.2 비기능 체크리스트

- [ ] **NFR-AUTH-001**: JWT HS256 서명, SECRET_KEY 환경 변수
- [ ] **NFR-AUTH-002**: PBKDF2 비밀번호 해싱 (600,000 iterations)
- [ ] **NFR-AUTH-003**: Brute Force 방지 (5회 실패 → 15분 잠금)
- [ ] **NFR-AUTH-004**: 토큰 검증 ≤ 10ms
- [ ] **NFR-AUTH-005**: 수평 확장 지원 (Stateless 인증)
- [ ] **NFR-AUTH-006**: 자동 로그인 유지 (최대 30일 옵션)
- [ ] **NFR-AUTH-007**: 명확한 한글 에러 메시지
- [ ] **NFR-AUTH-008**: 감사 로그 기록 (모든 인증 이벤트)

---

### 7.3 테스트 체크리스트

- [ ] **Backend pytest**: 커버리지 ≥ 90%
- [ ] **Frontend Vitest**: 모든 테스트 통과
- [ ] **E2E 테스트**: 로그인 → API 요청 → 토큰 갱신 → 로그아웃
- [ ] **성능 테스트**: 벤치마크 목표 달성
- [ ] **보안 스캔**: OWASP ZAP 통과

---

### 7.4 배포 체크리스트

- [ ] **Railway 환경 변수 설정**: SECRET_KEY, CORS_ALLOWED_ORIGINS
- [ ] **Vercel 환경 변수 설정**: NEXT_PUBLIC_API_URL
- [ ] **마이그레이션 실행**: User 모델, BlacklistedToken, AuthLog
- [ ] **기본 역할 할당**: 기존 사용자에게 역할 부여
- [ ] **HTTPS 강제**: Railway SSL 인증서 확인
- [ ] **프로덕션 테스트**: 실제 환경에서 전체 플로우 검증

---

### 7.5 문서화 체크리스트

- [ ] **API 문서**: Swagger/Redoc 자동 생성 및 배포
- [ ] **사용자 가이드**: 로그인, 권한, 비밀번호 변경 안내
- [ ] **관리자 가이드**: 사용자 관리, 역할 변경, 감사 로그
- [ ] **개발자 가이드**: JWT 구조, 토큰 갱신 로직, 권한 클래스 사용법
- [ ] **배포 가이드**: Railway 설정, 환경 변수, 마이그레이션

---

## 8. 최종 승인 기준

SPEC-AUTH-001은 다음 조건을 **모두** 만족할 때 완료로 승인됩니다:

✅ **모든 기능 체크리스트 항목 완료** (REQ-AUTH-001 ~ REQ-AUTH-010)
✅ **모든 비기능 체크리스트 항목 완료** (NFR-AUTH-001 ~ NFR-AUTH-008)
✅ **pytest 커버리지 ≥ 90%**
✅ **Vitest 테스트 100% 통과**
✅ **보안 감사 통과** (OWASP Top 10 기준)
✅ **성능 벤치마크 달성**
✅ **Railway 프로덕션 환경 배포 성공**
✅ **문서화 완료** (API 문서, 사용자 가이드, 배포 가이드)
✅ **Product Owner 승인** (@Sam 또는 Tech Lead)

---

## 9. 테스트 실행 명령어

### Backend 테스트
```bash
# 모든 테스트 실행
pytest

# 커버리지 측정
pytest --cov=dashboard --cov-report=html

# 특정 테스트만 실행
pytest tests/test_auth_api.py -v

# 성능 벤치마크
pytest tests/test_performance.py --benchmark-only
```

### Frontend 테스트
```bash
# 모든 테스트 실행
npm run test

# 특정 테스트만 실행
npm run test -- auth.test.ts

# 커버리지 측정
npm run test:coverage
```

### E2E 테스트
```bash
# Playwright E2E 테스트
npm run test:e2e
```

---

_이 문서는 MoAI-ADK 표준을 따릅니다._
_작성일: 2025-11-03 by @Sam_
_@TAG: @TEST:AUTH-001_

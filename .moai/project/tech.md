---
id: TECH-001
version: 0.1.2
status: completed
created: 2025-11-01
updated: 2025-11-03
author: @Sam
priority: high
---

# ⚙️ 대학교 데이터 시각화 대시보드 기술 스택

## HISTORY

### v0.1.2 (2025-11-03)
- **UPDATED**: MoAI-ADK 기술 스택 문서 실제 내용으로 업데이트
- **AUTHOR**: @Sam
- **SECTIONS**: Django + Next.js 풀스택, PostgreSQL, TanStack, Recharts, Railway

### v0.1.1 (2025-11-01)
- **COMPLETED**: 백엔드 + 프론트엔드 기술 스택 확정 및 구현
- **AUTHOR**: GOOS🪿엉아
- **SECTIONS**: Python 3.11.9, Node.js, TypeScript 5.5, 테스트 프레임워크

### v0.1.0 (2025-11-01)
- **INITIAL**: 기술 스택 선정 및 SPEC 작성
- **AUTHOR**: GOOS🪿엉아
- **SECTIONS**: 언어 선택, 프레임워크 평가, 배포 전략

---

## @DOC:STACK-001 언어 및 런타임

### 백엔드: Python

- **언어**: Python
- **버전**: 3.11.9 (권장), 3.11.x 지원
- **선택 이유**:
  - Django 생태계 성숙도
  - pandas, openpyxl로 Excel 파싱 용이
  - 빠른 개발 속도 (프로토타이핑)
- **패키지 관리자**: pip + requirements.txt

### 프론트엔드: TypeScript

- **언어**: TypeScript
- **버전**: 5.5.3
- **선택 이유**:
  - 타입 안정성 (컴파일 타임 에러 감지)
  - Next.js와 최적 호환
  - 대규모 코드베이스 유지보수 용이
- **패키지 관리자**: npm

### 플랫폼 지원

| 플랫폼 | 지원 수준 | 검증 방법 | 제약사항 |
|--------|----------|----------|----------|
| **Windows** | ✅ 완전 지원 | pytest, npm test | Python 3.11+ 필요 |
| **macOS** | ✅ 완전 지원 | pytest, npm test | - |
| **Linux** | ✅ 완전 지원 | pytest, npm test, Railway | 프로덕션 환경 (Railway) |

---

## @DOC:FRAMEWORK-001 핵심 프레임워크 및 라이브러리

### 백엔드 (Django)

#### Runtime Dependencies
```python
# requirements.txt
Django==5.0.7
djangorestframework==3.15.2
django-cors-headers==4.4.0
psycopg2-binary==2.9.9
python-dotenv==1.0.1
openpyxl==3.1.5
pandas==2.2.2
gunicorn==22.0.0
whitenoise==6.7.0
dj-database-url==2.2.0
```

#### Development Dependencies
```python
pytest==8.3.2
pytest-django==4.8.0
```

#### 프레임워크 선택 근거
- **Django 5.0.7**: Admin 패널, ORM, 보안 기능 내장
- **DRF**: ViewSet, Serializer로 RESTful API 간편 구축
- **openpyxl + pandas**: Excel 파일 자동 파싱

---

### 프론트엔드 (Next.js)

#### Runtime Dependencies
```json
{
  "dependencies": {
    "next": "14.2.5",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "@tanstack/react-table": "^8.20.1",
    "@tanstack/react-form": "^0.36.3",
    "recharts": "^2.12.7",
    "axios": "^1.7.2",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.4.0"
  }
}
```

#### Development Dependencies
```json
{
  "devDependencies": {
    "@types/node": "^20.14.11",
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "typescript": "^5.5.3",
    "eslint": "^8.57.0",
    "eslint-config-next": "14.2.5",
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.39",
    "tailwindcss": "^3.4.6",
    "vitest": "^1.6.0",
    "@vitejs/plugin-react": "^4.3.1"
  }
}
```

#### 프레임워크 선택 근거
- **Next.js 14**: App Router, SSR, 최적화된 빌드
- **TanStack Table**: 강력한 테이블 기능 (정렬/필터링/페이지네이션)
- **TanStack Form**: 폼 유효성 검사 및 상태 관리
- **Recharts**: 선언적 차트 라이브러리 (막대/선/영역/파이)
- **Tailwind CSS**: 유틸리티 우선 CSS, 빠른 스타일링

---

### 빌드 시스템

#### 백엔드 빌드
- **도구**: Python 표준 (no build step)
- **WSGI 서버**: Gunicorn (프로덕션)
- **정적 파일**: WhiteNoise (collectstatic)

#### 프론트엔드 빌드
- **도구**: Next.js 빌드 (Turbopack 옵션)
- **번들러**: Webpack (Next.js 내장)
- **타겟**: ES2020, 브라우저 (Chrome, Firefox, Safari, Edge)
- **성능 목표**: 빌드 시간 < 60초

---

## @DOC:QUALITY-001 품질 게이트 및 정책

### 테스트 커버리지

#### 백엔드 (pytest)
- **프레임워크**: pytest + pytest-django
- **커버리지 목표**: > 80%
- **테스트 파일**: `backend/dashboard/tests/`
  - `test_models.py`: 모델 단위 테스트
  - `test_api.py`: API 엔드포인트 통합 테스트
- **현재 상태**: ✅ 16/16 passed (100%)

#### 프론트엔드 (vitest)
- **프레임워크**: vitest + @testing-library/react
- **커버리지 목표**: > 70%
- **테스트 파일**: `frontend/__tests__/`
  - `lib/utils.test.ts`: 유틸리티 함수 테스트
- **현재 상태**: ✅ All tests passed


### 정적 분석 도구

| 도구 | 역할 | 설정 파일 | 실패 처리 |
|------|------|-----------|----------|
| **ESLint** | JavaScript/TypeScript 린팅 | `.eslintrc.json` | 빌드 차단 |
| **TypeScript** | 타입 체크 | `tsconfig.json` | 빌드 차단 |
| **Django Check** | Django 설정 검증 | `settings.py` | 마이그레이션 전 검증 |

### 자동화 스크립트

```bash
# 백엔드 품질 게이트
cd backend
python manage.py check         # Django 설정 검증
pytest dashboard/tests/          # 테스트 실행 (16개)

# 프론트엔드 품질 게이트
cd frontend
npm run lint                     # ESLint 검사
npx tsc --noEmit                 # TypeScript 컴파일 검사
npm run test                     # Vitest 테스트 실행
npm run build                    # Next.js 빌드 검증
```

---

## @DOC:SECURITY-001 보안 정책 및 운영

### 비밀 정보 관리

- **정책**: 환경 변수를 통한 비밀 정보 관리, 코드에 하드코딩 금지
- **도구**:
  - 개발: `.env` 파일 (`.gitignore`에 포함)
  - 프로덕션: Railway Secrets (Environment Variables)
- **검증**: `.env.example` 파일 제공, 실제 값은 커밋하지 않음

### 의존성 보안

```json
{
  "security": {
    "audit_tool": "npm audit (frontend), safety (backend, 향후)",
    "update_policy": "Minor updates monthly, Security patches immediately",
    "vulnerability_threshold": "No high/critical vulnerabilities allowed"
  }
}
```

### 로깅 정책

- **로그 레벨**:
  - Development: DEBUG
  - Test: INFO
  - Production: WARNING (Django) / warn (Next.js)
- **민감 데이터 마스킹**: 비밀번호, API 키는 로그에 기록 안 함
- **보존 기간**: Railway 로그 7일 보존 (무료 플랜)

---

## @DOC:DEPLOY-001 배포 채널 및 전략

### 1. 배포 채널

- **주요 채널**: Railway (백엔드 + DB), Vercel (프론트엔드)
- **배포 절차**:
  1. Git push to `main` branch
  2. Railway/Vercel 자동 감지
  3. 자동 빌드 및 배포
  4. 헬스 체크 (Railway: Gunicorn, Vercel: Next.js)
- **버전 관리**: Git tags (`v0.1.0`, `v0.1.1`, ...)
- **롤백 전략**: Railway/Vercel 대시보드에서 이전 배포 버전으로 즉시 롤백

### 2. 개발자 설정

```bash
# 백엔드 로컬 설정
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver  # http://localhost:8000

# 프론트엔드 로컬 설정
cd frontend
npm install
npm run dev  # http://localhost:3000
```

### 3. CI/CD 파이프라인 (향후 구현)

| 단계 | 목적 | 도구 | 성공 조건 |
|------|------|------|----------|
| Test | 테스트 실행 | pytest, vitest | 모든 테스트 통과 |
| Lint | 코드 품질 검사 | ESLint, Django Check | 린트 오류 0개 |
| Build | 빌드 검증 | Next.js build, Django collectstatic | 빌드 성공 |
| Deploy | 자동 배포 | Railway, Vercel | 헬스 체크 통과 |

---

## 환경 프로필

### Development (`dev`)

```bash
# Backend (.env)
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
CORS_ALLOWED_ORIGINS=http://localhost:3000

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Production (`prod`)

```bash
# Backend (Railway Environment Variables)
DJANGO_SECRET_KEY=<railway-generated>
DEBUG=False
ALLOWED_HOSTS=${{RAILWAY_PUBLIC_DOMAIN}}
DATABASE_URL=${{DATABASE_URL}}  # PostgreSQL (auto)
CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app

# Frontend (Vercel Environment Variables)
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

---

## @CODE:TECH-DEBT-001 기술 부채 관리

### 현재 부채 (없음, MVP 완료)

- ✅ 모든 기능 완전 구현
- ✅ 테스트 100% 통과
- ✅ TypeScript strict mode
- ✅ Django Best Practices 준수

### Phase 2 개선 계획

1. **사용자 인증** (높음) - JWT 토큰 기반 인증 추가
2. **데이터 내보내기** (중간) - CSV/Excel/PDF 내보내기 기능
3. **E2E 테스트** (중간) - Playwright E2E 테스트 추가

---

## 📚 참고 문서

- [Django 5.0 문서](https://docs.djangoproject.com/en/5.0/)
- [Next.js 14 문서](https://nextjs.org/docs)
- [TanStack Table 문서](https://tanstack.com/table/latest)
- [Recharts 문서](https://recharts.org/)
- [Railway 배포 가이드](../../DEPLOYMENT.md)

---

_이 문서는 `/alfred:0-project` 실행 결과입니다._
_마지막 업데이트: 2025-11-03 by @Sam_

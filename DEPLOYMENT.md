# 배포 가이드 (Deployment Guide)

대학교 데이터 시각화 대시보드를 Railway(백엔드)와 Vercel(프론트엔드)에 배포하는 가이드입니다.

## 목차

1. [사전 준비](#사전-준비)
2. [백엔드 배포 (Railway)](#백엔드-배포-railway)
3. [프론트엔드 배포 (Vercel)](#프론트엔드-배포-vercel)
4. [환경 변수 설정](#환경-변수-설정)
5. [배포 후 확인](#배포-후-확인)
6. [문제 해결](#문제-해결)

---

## 사전 준비

### 필요한 계정

1. **Railway** 계정 ([railway.app](https://railway.app))
   - GitHub 연동 권장
   - 무료 플랜: $5 크레딧/월

2. **Vercel** 계정 ([vercel.com](https://vercel.com))
   - GitHub 연동 권장
   - Hobby 플랜: 무료

3. **GitHub** 계정
   - 코드 저장소

### Git 저장소 준비

```bash
# 현재 브랜치 확인
git branch

# 메인 브랜치로 병합 (옵션)
git checkout main
git merge feature/university-dashboard-init

# 또는 현재 브랜치 그대로 배포
git push origin feature/university-dashboard-init
```

---

## 백엔드 배포 (Railway)

### 1단계: Railway 프로젝트 생성

1. [Railway 대시보드](https://railway.app/dashboard) 접속
2. "New Project" 클릭
3. "Deploy from GitHub repo" 선택
4. 저장소 선택: `your-username/university-dashboard`
5. "Add variables" 클릭하여 환경 변수 추가

### 2단계: 환경 변수 설정

Railway 프로젝트 → Variables 탭에서 다음 변수 추가:

```bash
# Django 설정
DJANGO_SECRET_KEY=랜덤-시크릿-키-50자-이상
DEBUG=False
ALLOWED_HOSTS=${{RAILWAY_PUBLIC_DOMAIN}}

# CORS 설정 (프론트엔드 도메인)
CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app

# Static 파일
STATIC_ROOT=staticfiles
STATIC_URL=/static/
```

**시크릿 키 생성 방법:**
```python
# Python으로 시크릿 키 생성
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3단계: PostgreSQL 데이터베이스 추가

1. Railway 프로젝트에서 "New" → "Database" → "Add PostgreSQL" 클릭
2. 자동으로 `DATABASE_URL` 환경 변수가 설정됩니다
3. 데이터베이스 연결 확인

### 4단계: 배포 설정

Railway는 자동으로 다음 파일들을 인식합니다:

- `Procfile`: Gunicorn 서버 실행 명령
- `runtime.txt`: Python 버전
- `railway.json`: 빌드 및 배포 설정
- `requirements.txt`: Python 패키지

**자동 배포:**
- Git push 시 자동으로 재배포됩니다

### 5단계: 배포 확인

```bash
# Railway 로그 확인
# Dashboard → Deployments → View Logs

# 예상 로그:
# ✓ Installing dependencies
# ✓ Running collectstatic
# ✓ Running migrations
# ✓ Starting gunicorn
```

### 6단계: 도메인 확인

1. Railway 프로젝트 → Settings → Domains
2. 자동 생성된 도메인: `https://your-app.railway.app`
3. (선택) 커스텀 도메인 연결 가능

---

## 프론트엔드 배포 (Vercel)

### 1단계: Vercel 프로젝트 생성

1. [Vercel 대시보드](https://vercel.com/dashboard) 접속
2. "Add New" → "Project" 클릭
3. GitHub 저장소 import
4. 프로젝트 설정:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

### 2단계: 환경 변수 설정

Vercel 프로젝트 → Settings → Environment Variables:

```bash
# API URL (Railway 백엔드 도메인)
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

### 3단계: 배포

1. "Deploy" 버튼 클릭
2. 자동으로 빌드 및 배포 시작
3. 완료 후 도메인 확인: `https://your-project.vercel.app`

### 4단계: Railway에서 CORS 업데이트

프론트엔드 도메인이 확정되면 Railway의 `CORS_ALLOWED_ORIGINS` 업데이트:

```bash
CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app
```

---

## 환경 변수 설정

### 백엔드 (Railway)

| 변수명 | 설명 | 예시 |
|--------|------|------|
| `DJANGO_SECRET_KEY` | Django 보안 키 (필수) | `django-insecure-...` |
| `DEBUG` | 디버그 모드 (프로덕션: False) | `False` |
| `ALLOWED_HOSTS` | 허용된 호스트 | `${{RAILWAY_PUBLIC_DOMAIN}}` |
| `DATABASE_URL` | PostgreSQL 연결 (자동) | `postgresql://...` |
| `CORS_ALLOWED_ORIGINS` | CORS 허용 도메인 | `https://your-app.vercel.app` |

### 프론트엔드 (Vercel)

| 변수명 | 설명 | 예시 |
|--------|------|------|
| `NEXT_PUBLIC_API_URL` | 백엔드 API URL | `https://your-backend.railway.app` |

---

## 배포 후 확인

### 백엔드 확인

1. **헬스 체크:**
   ```bash
   curl https://your-backend.railway.app/admin/
   # 200 OK 응답 확인
   ```

2. **API 엔드포인트:**
   ```bash
   curl https://your-backend.railway.app/api/datasets/
   # JSON 응답 확인
   ```

3. **Django Admin 접속:**
   - URL: `https://your-backend.railway.app/admin/`
   - 슈퍼유저 생성 필요 (아래 참조)

### 프론트엔드 확인

1. **홈페이지 접속:**
   - URL: `https://your-frontend.vercel.app`
   - 대시보드 로딩 확인

2. **API 연결 확인:**
   - 통계 카드에 데이터 표시 확인
   - 브라우저 콘솔에서 CORS 에러 없는지 확인

---

## 슈퍼유저 생성 (Django Admin)

Railway에서 Django 슈퍼유저 생성:

### 방법 1: Railway CLI 사용

```bash
# Railway CLI 설치
npm i -g @railway/cli

# 로그인
railway login

# 프로젝트 연결
railway link

# 슈퍼유저 생성 명령
railway run python manage.py createsuperuser
```

### 방법 2: Dockerfile에서 실행

또는 일회성 Job으로 실행:

```bash
# Railway 프로젝트에서 "Add Service" → "Empty Service"
# Command: python manage.py createsuperuser --noinput
# 환경 변수로 DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_PASSWORD, DJANGO_SUPERUSER_EMAIL 설정
```

---

## 문제 해결

### 1. 데이터베이스 마이그레이션 실패

**증상:** "no such table" 에러

**해결:**
```bash
# Railway에서 수동 마이그레이션 실행
railway run python manage.py migrate
```

### 2. Static 파일 로딩 안 됨

**증상:** CSS/JS 파일 404 에러

**해결:**
```bash
# collectstatic 재실행
railway run python manage.py collectstatic --noinput

# settings.py 확인
STATIC_ROOT = 'staticfiles'
STATIC_URL = '/static/'
```

### 3. CORS 에러

**증상:** 프론트엔드에서 "CORS policy" 에러

**해결:**
```bash
# Railway 환경 변수 업데이트
CORS_ALLOWED_ORIGINS=https://정확한-프론트엔드-도메인.vercel.app

# settings.py에서 django-cors-headers 설정 확인
```

### 4. 500 Internal Server Error

**증상:** 서버 에러

**해결:**
```bash
# Railway 로그 확인
railway logs

# DEBUG=True로 임시 설정하여 에러 확인 (프로덕션에서는 즉시 False로 복원)
```

### 5. 환경 변수 미적용

**증상:** 설정이 반영 안 됨

**해결:**
1. Railway/Vercel에서 환경 변수 재확인
2. 재배포 (Redeploy) 실행
3. 변수명 오타 확인 (대소문자 구분)

---

## 배포 체크리스트

### 배포 전

- [ ] Git 저장소에 모든 변경사항 커밋
- [ ] 테스트 모두 통과 확인 (`pytest`, `npm test`)
- [ ] `.env` 파일이 `.gitignore`에 포함되어 있는지 확인
- [ ] `DEBUG=False` 설정 확인
- [ ] 시크릿 키 생성 준비

### Railway 배포

- [ ] PostgreSQL 데이터베이스 추가
- [ ] 환경 변수 모두 설정
- [ ] 배포 성공 확인
- [ ] 마이그레이션 자동 실행 확인
- [ ] 슈퍼유저 생성
- [ ] Admin 페이지 접속 확인

### Vercel 배포

- [ ] `NEXT_PUBLIC_API_URL` 설정
- [ ] 빌드 성공 확인
- [ ] 프론트엔드 접속 확인
- [ ] API 연결 확인

### 배포 후

- [ ] Railway CORS 설정에 Vercel 도메인 추가
- [ ] 홈페이지에서 데이터 로딩 확인
- [ ] 데이터셋 업로드 테스트
- [ ] 차트 렌더링 확인
- [ ] 모든 페이지 동작 확인

---

## 자동 배포 설정

### Git Push 시 자동 배포

**Railway & Vercel 모두 자동 지원:**

1. GitHub에 push
   ```bash
   git add .
   git commit -m "feat: 새로운 기능 추가"
   git push origin main
   ```

2. 자동으로 Railway와 Vercel이 감지하여 재배포

3. 배포 상태 확인
   - Railway: Dashboard → Deployments
   - Vercel: Dashboard → Deployments

---

## 모니터링

### Railway 모니터링

- **로그:** Dashboard → Logs (실시간)
- **메트릭:** Dashboard → Metrics (CPU, 메모리, 네트워크)
- **알림:** Settings → Notifications

### Vercel 모니터링

- **Analytics:** Dashboard → Analytics
- **로그:** Dashboard → Deployments → View Function Logs
- **성능:** Web Vitals 자동 추적

---

## 비용

### Railway (백엔드)

- **무료 크레딧:** $5/월
- **예상 사용량:** 소규모 프로젝트는 무료 범위 내
- **유료 플랜:** $5/월부터 (필요 시)

### Vercel (프론트엔드)

- **Hobby 플랜:** 무료
- **제한:** 대역폭 100GB/월, 빌드 100시간/월
- **Pro 플랜:** $20/월 (상용 서비스 시)

---

## 보안 권장사항

1. ✅ `DEBUG=False` 설정 (프로덕션)
2. ✅ 강력한 `SECRET_KEY` 사용 (50자 이상)
3. ✅ `ALLOWED_HOSTS` 정확히 설정
4. ✅ CORS 출처 제한 (와일드카드 사용 금지)
5. ✅ 환경 변수에 민감한 정보 저장 (코드에 하드코딩 금지)
6. ✅ HTTPS 사용 (Railway, Vercel 자동 지원)
7. ✅ 정기적인 의존성 업데이트

---

## 추가 리소스

- [Railway 문서](https://docs.railway.app)
- [Vercel 문서](https://vercel.com/docs)
- [Django 배포 체크리스트](https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/)
- [Next.js 배포 가이드](https://nextjs.org/docs/deployment)

---

## 지원

문제가 발생하면:

1. Railway/Vercel 로그 확인
2. 환경 변수 재확인
3. GitHub Issues에 문의
4. Railway/Vercel 커뮤니티 포럼 활용

**배포 성공하세요! 🚀**

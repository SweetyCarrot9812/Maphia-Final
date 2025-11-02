---
id: STRUCTURE-001
version: 0.1.2
status: completed
created: 2025-11-01
updated: 2025-11-03
author: @Sam
priority: high
---

# 🏗️ 대학교 데이터 시각화 대시보드 시스템 구조

## HISTORY

### v0.1.2 (2025-11-03)
- **UPDATED**: MoAI-ADK 프로젝트 구조 문서 실제 내용으로 업데이트
- **AUTHOR**: @Sam
- **SECTIONS**: University Dashboard 아키텍처, 백엔드/프론트엔드 모듈, API 통합

### v0.1.1 (2025-11-01)
- **COMPLETED**: Django + Next.js 풀스택 구조 구현 완료
- **AUTHOR**: GOOS🪿엉아
- **SECTIONS**: 백엔드 (Django DRF), 프론트엔드 (Next.js 14), PostgreSQL DB

### v0.1.0 (2025-11-01)
- **INITIAL**: 프로젝트 구조 설계 및 SPEC 작성
- **AUTHOR**: GOOS🪿엉아
- **SECTIONS**: 아키텍처 패턴, 디렉토리 구조, 데이터 흐름

---

## @DOC:ARCHITECTURE-001 시스템 아키텍처

### 아키텍처 전략

**풀스택 웹 애플리케이션 (Django REST API + Next.js SSR)**

```
┌─────────────────────────────────────────────┐
│  Presentation Layer (Next.js 14 App Router) │
│  - React Server Components                  │
│  - Client Components (TanStack)             │
│  - Tailwind CSS Styling                     │
└─────────────┬───────────────────────────────┘
              │ REST API (HTTP/JSON)
              ↓
┌─────────────────────────────────────────────┐
│  API Layer (Django REST Framework)          │
│  - ViewSets (Dataset, DataRecord)           │
│  - Serializers (DRF)                        │
│  - Authentication & CORS                    │
└─────────────┬───────────────────────────────┘
              │ ORM (Django Models)
              ↓
┌─────────────────────────────────────────────┐
│  Business Logic (Django App)                │
│  - Models (Dataset, DataRecord)             │
│  - Excel Parsing (openpyxl + pandas)        │
│  - File Upload Validation                   │
└─────────────┬───────────────────────────────┘
              │ Database Queries
              ↓
┌─────────────────────────────────────────────┐
│  Persistence Layer (PostgreSQL)             │
│  - Tables: dashboard_dataset                │
│  - Tables: dashboard_datarecord             │
│  - Indexes: upload_date, category, user     │
└─────────────────────────────────────────────┘
```

**설계 원칙**:
1. **관심사의 분리**: 프론트엔드/백엔드/DB 명확히 분리
2. **RESTful API**: 표준 HTTP 메서드 (GET/POST/PUT/DELETE)
3. **타입 안정성**: TypeScript (프론트) + Type Hints (백엔드)
4. **확장 가능성**: Railway 클라우드 배포, 수평 확장 지원

**트레이드오프**:
- ✅ **선택한 방식**: Django + Next.js 분리 → 독립적 배포, 기술 스택 유연성
- ❌ **포기한 방식**: Next.js API Routes 단독 → Django ORM 및 Admin 활용 가능

---

## @DOC:MODULES-001 모듈 책임

### 1. 백엔드 모듈 (Django REST Framework)

#### 디렉토리 구조
```
backend/
├── config/                 # Django 설정
│   ├── settings.py         # DATABASES, CORS, ALLOWED_HOSTS
│   ├── urls.py             # URL routing
│   └── wsgi.py             # Gunicorn entry point
├── dashboard/              # 메인 앱
│   ├── models.py           # Dataset, DataRecord
│   ├── serializers.py      # DRF Serializers
│   ├── views.py            # ViewSets (CRUD + 통계)
│   ├── urls.py             # API 엔드포인트
│   ├── admin.py            # Django Admin 설정
│   └── tests/              # pytest 테스트
│       ├── test_models.py
│       ├── test_api.py
│       └── test_upload.py
├── manage.py
└── requirements.txt
```

#### 핵심 책임
- **Excel 파일 처리**: openpyxl + pandas를 통한 자동 파싱
- **데이터 저장**: Dataset (메타데이터) + DataRecord (JSONField)
- **REST API 제공**: ViewSet 기반 CRUD 엔드포인트
- **통계 집계**: Django ORM aggregation (Count, Sum)

#### 입력/출력
- **입력**:
  - Excel 파일 (.xlsx, .xls) via MultiPartParser
  - JSON 요청 (CRUD 연산)
- **처리**:
  - 파일 유효성 검사 (형식, 크기)
  - Excel → pandas DataFrame → JSONField
  - ORM을 통한 DB 저장
- **출력**:
  - JSON 응답 (DRF Serializer)
  - 페이지네이션 메타데이터
  - 통계 집계 결과

---

### 2. 프론트엔드 모듈 (Next.js 14)

#### 디렉토리 구조
```
frontend/
├── app/                    # App Router pages
│   ├── page.tsx            # 대시보드 홈
│   ├── datasets/
│   │   ├── page.tsx        # 데이터셋 목록
│   │   └── [id]/page.tsx   # 데이터셋 상세
│   ├── analytics/page.tsx  # 차트 분석
│   ├── upload/page.tsx     # 파일 업로드
│   └── layout.tsx          # 공통 레이아웃
├── components/             # 재사용 컴포넌트
│   ├── Layout.tsx
│   ├── DataTable.tsx       # TanStack Table
│   ├── ChartPanel.tsx      # Recharts wrapper
│   └── UploadForm.tsx      # TanStack Form
├── lib/                    # 유틸리티
│   ├── api.ts              # Axios API client
│   ├── utils.ts            # Helper functions
│   └── types.ts            # TypeScript types
├── public/
└── package.json
```

#### 핵심 책임
- **UI 렌더링**: React Server/Client Components
- **상태 관리**: React hooks (useState, useEffect)
- **데이터 페칭**: Axios → Django API
- **차트 시각화**: Recharts (막대/선/영역/파이)
- **테이블 관리**: TanStack Table v8
- **폼 처리**: TanStack Form v0.36

#### 입력/출력
- **입력**:
  - 사용자 액션 (클릭, 업로드, 폼 제출)
  - API 응답 (JSON)
- **처리**:
  - Next.js SSR/CSR
  - TanStack Table: 정렬/필터링/페이지네이션
  - Recharts: 데이터 → 차트 렌더링
- **출력**:
  - HTML (Tailwind CSS 스타일링)
  - 인터랙티브 UI (hover, focus, loading)

---

### 3. 데이터 모델

#### Dataset (데이터셋)
```python
class Dataset(models.Model):
    id = AutoField(primary_key=True)
    title = CharField(max_length=200)
    description = TextField(blank=True)
    filename = CharField(max_length=255)
    file_size = IntegerField()
    upload_date = DateTimeField(auto_now_add=True)
    record_count = IntegerField(default=0)
    category = CharField(max_length=100)
    uploaded_by = ForeignKey(User, on_delete=CASCADE)
```

**인덱스**:
- `upload_date` (DESC) - 최근 업로드 조회
- `category` - 카테고리별 필터링
- `uploaded_by` - 사용자별 데이터셋 조회

#### DataRecord (데이터 레코드)
```python
class DataRecord(models.Model):
    id = AutoField(primary_key=True)
    dataset = ForeignKey(Dataset, on_delete=CASCADE, related_name='records')
    data = JSONField()  # 유연한 스키마
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

**JSON 스키마 예시**:
```json
{
  "학과": "컴퓨터공학과",
  "학년": 3,
  "성적": 3.8,
  "수강과목수": 5
}
```

---

## @DOC:INTEGRATION-001 API 통합

### REST API 엔드포인트

#### 데이터셋 API
- **GET** `/api/datasets/` - 데이터셋 목록 (페이지네이션)
- **POST** `/api/datasets/` - 데이터셋 생성 (파일 업로드)
- **GET** `/api/datasets/{id}/` - 데이터셋 상세
- **PUT** `/api/datasets/{id}/` - 데이터셋 수정
- **DELETE** `/api/datasets/{id}/` - 데이터셋 삭제
- **GET** `/api/datasets/{id}/records/` - 레코드 조회

#### 통계 API
- **GET** `/api/statistics/overview/` - 대시보드 통계
  - 응답: `{ total_datasets, total_records, total_size, categories, recent_uploads }`

#### 인증
- **현재 (MVP)**: Django Session Auth
- **향후 (Phase 2)**: JWT Token Auth

#### CORS 설정
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Next.js dev
    "https://your-domain.vercel.app"  # Production
]
```

---

## @DOC:DATAFLOW-001 데이터 흐름

### 파일 업로드 플로우
```
1. 사용자 → 파일 선택 (드래그 앤 드롭)
   ↓
2. 프론트엔드 → FormData 생성, POST /api/datasets/
   ↓
3. 백엔드 → 파일 유효성 검사
   ↓
4. openpyxl → Excel 파싱 (헤더 + 데이터 rows)
   ↓
5. pandas → DataFrame 변환
   ↓
6. Django ORM → Dataset + DataRecords 저장
   ↓
7. 응답 → { id, title, record_count }
   ↓
8. 프론트엔드 → 성공 알림, 목록 페이지 이동
```

### 차트 렌더링 플로우
```
1. 프론트엔드 → GET /api/datasets/{id}/records/
   ↓
2. 백엔드 → ORM 쿼리, JSON 직렬화
   ↓
3. 프론트엔드 → useState로 데이터 저장
   ↓
4. Recharts → 데이터 매핑 (X축/Y축/그룹)
   ↓
5. SVG 렌더링 → 인터랙티브 차트 표시
```

---

## @DOC:DEPLOYMENT-001 배포 구조

### Railway (백엔드 + DB)
```
┌──────────────────────────────────┐
│  Railway Service: Django Backend │
│  - Gunicorn WSGI Server          │
│  - Python 3.11.9                 │
│  - Environment Variables         │
└────────┬─────────────────────────┘
         │
         ↓
┌──────────────────────────────────┐
│  Railway PostgreSQL Database     │
│  - Tables: dashboard_*           │
│  - Auto backup enabled           │
└──────────────────────────────────┘
```

### Vercel (프론트엔드, 권장)
```
┌──────────────────────────────────┐
│  Vercel Deployment               │
│  - Next.js 14 SSR/SSG            │
│  - Edge Functions                │
│  - NEXT_PUBLIC_API_URL env       │
└──────────────────────────────────┘
```

### 환경 변수
**Backend (Railway)**:
- `DJANGO_SECRET_KEY`: Django 보안 키
- `DEBUG`: False (프로덕션)
- `DATABASE_URL`: PostgreSQL 연결 (자동)
- `ALLOWED_HOSTS`: Railway 도메인
- `CORS_ALLOWED_ORIGINS`: Vercel 도메인

**Frontend (Vercel)**:
- `NEXT_PUBLIC_API_URL`: Railway 백엔드 URL

---

## @DOC:TRACEABILITY-001 추적 가능성

### SPEC → CODE 매핑

| SPEC ID | 기능 | 구현 위치 |
|---------|------|----------|
| REQ-DASH-001 | 파일 업로드 | `backend/dashboard/views.py:_process_excel_file` |
| REQ-DASH-002 | 데이터 저장 | `backend/dashboard/models.py:Dataset, DataRecord` |
| REQ-DASH-004 | 인터랙티브 테이블 | `frontend/components/DataTable.tsx` (TanStack Table) |
| REQ-DASH-005 | 차트 시각화 | `frontend/app/analytics/page.tsx` (Recharts) |
| REQ-DASH-006 | 대시보드 레이아웃 | `frontend/app/page.tsx` |

### 테스트 커버리지

**Backend (pytest)**:
- `tests/test_models.py`: Dataset/DataRecord 모델 테스트
- `tests/test_api.py`: ViewSet API 엔드포인트 테스트
- **결과**: 16/16 passed (100%)

**Frontend (vitest)**:
- `__tests__/lib/utils.test.ts`: 유틸리티 함수 테스트
- **결과**: All tests passed

---

## 🚀 확장 계획

### Phase 2: 향상 기능
1. **사용자 인증**: JWT 기반 인증, 권한 관리
2. **데이터 내보내기**: CSV/Excel/PDF 내보내기
3. **고급 필터링**: 복합 조건 필터, 저장된 필터

### Phase 3: 확장 기능
1. **AI 인사이트**: 데이터 패턴 자동 탐지, 추천
2. **커스텀 대시보드**: 드래그 앤 드롭 대시보드 빌더
3. **실시간 협업**: WebSocket 기반 동시 편집

---

## 📚 참고 문서

- [SPEC-DASH-001](../.moai/specs/SPEC-DASH-001/spec.md): 상세 요구사항
- [README.md](../../README.md): 프로젝트 개요
- [DEPLOYMENT.md](../../DEPLOYMENT.md): 배포 가이드

---

_이 문서는 `/alfred:0-project` 실행 결과입니다._
_마지막 업데이트: 2025-11-03 by @Sam_

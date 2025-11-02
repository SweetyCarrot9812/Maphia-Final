---
id: ANALYSIS-PHASE2-001
version: 1.0.0
created: 2025-11-03
author: @Sam
language: ko
status: draft
---

# Phase 2 SPEC 후보 분석 결과

## 📋 실행 요약

**프로젝트**: University Data Visualization Dashboard
**현재 상태**: Phase 1 MVP 완료 ✅
**분석 목적**: Phase 2 구현을 위한 SPEC 후보 우선순위 선정
**분석 일시**: 2025-11-03

---

## 🎯 우선순위 추천 순서

### 1. [SPEC-AUTH-001] JWT 기반 사용자 인증 시스템 (우선순위: **Critical**)
- **이유**: 현재 Django 세션 인증만 존재, 프로덕션 환경에서 다중 사용자 지원 필수
- **복잡도**: 3/5
- **비즈니스 가치**: 매우 높음 (보안 + 확장성)

### 2. [SPEC-EXPORT-001] 데이터 내보내기 시스템 (우선순위: **High**)
- **이유**: 사용자가 분석 결과를 공유/보고서 작성에 활용 필요
- **복잡도**: 2/5
- **비즈니스 가치**: 높음 (사용성 개선)

### 3. [SPEC-FILTER-001] 고급 필터링 및 전체 텍스트 검색 (우선순위: **High**)
- **이유**: 대용량 데이터셋에서 특정 정보 빠르게 찾기 위한 필수 기능
- **복잡도**: 3/5
- **비즈니스 가치**: 높음 (생산성 향상)

---

## 📊 상세 분석

### SPEC 후보 1: SPEC-AUTH-001 - JWT 기반 사용자 인증 시스템

#### 1. SPEC ID 및 제목
**SPEC-AUTH-001**: JWT 기반 사용자 인증 및 권한 관리 시스템

#### 2. Priority
**Critical** - 프로덕션 환경에서 다중 사용자 지원을 위한 필수 기능

#### 3. Estimated Complexity
**3/5** (중간)
- JWT 토큰 발급/검증 로직 구현
- 프론트엔드 토큰 저장 및 자동 갱신
- 권한 기반 API 접근 제어
- 기존 Django User 모델 확장

#### 4. Dependencies
- **선행 조건**: 없음 (독립적 구현 가능)
- **연관 SPEC**:
  - SPEC-DASH-001 (기존 인증 시스템 개선)
  - 향후 SPEC-ROLE-001 (역할 기반 접근 제어) 기반이 됨

#### 5. Key Requirements (EARS 형식)

**REQ-AUTH-001**: JWT 토큰 발급
- **WHEN** 사용자가 유효한 아이디/비밀번호로 로그인 요청을 하면
- **THE SYSTEM SHALL** 사용자 정보를 검증하고
- **AND** Access Token (15분 유효) 및 Refresh Token (7일 유효)을 발급하며
- **AND** HTTP-only 쿠키 또는 응답 본문에 토큰을 반환한다

**REQ-AUTH-002**: 토큰 기반 API 인증
- **WHEN** 클라이언트가 API 요청 시 Authorization 헤더에 JWT 토큰을 포함하면
- **THE SYSTEM SHALL** 토큰의 유효성을 검증하고
- **AND** 유효한 경우 요청을 처리하며
- **AND** 만료되거나 유효하지 않은 경우 401 Unauthorized를 반환한다

**REQ-AUTH-003**: 토큰 자동 갱신
- **WHEN** Access Token이 만료되고 유효한 Refresh Token이 존재하면
- **THE SYSTEM SHALL** 새로운 Access Token을 자동으로 발급하며
- **AND** 프론트엔드에서 사용자 경험 중단 없이 토큰을 갱신한다

**REQ-AUTH-004**: 사용자 권한 관리
- **THE SYSTEM SHALL** 사용자 역할을 정의하고 (Admin, Manager, Viewer)
- **AND** 역할별로 API 엔드포인트 접근 권한을 제어하며
- **AND** 권한 없는 요청에 대해 403 Forbidden을 반환한다

**REQ-AUTH-005**: 로그아웃 및 토큰 무효화
- **WHEN** 사용자가 로그아웃을 요청하면
- **THE SYSTEM SHALL** 해당 사용자의 Refresh Token을 블랙리스트에 추가하고
- **AND** 클라이언트 측 토큰을 삭제하며
- **AND** 로그인 페이지로 리디렉션한다

#### 6. Business Value
- **보안 강화**: Stateless 인증으로 세션 하이재킹 위험 감소
- **확장성**: 마이크로서비스 아키텍처 전환 시 토큰 기반 인증 활용 가능
- **사용자 경험**: 자동 토큰 갱신으로 로그인 유지 시간 연장
- **다중 사용자 지원**: 역할 기반 접근 제어로 조직 내 여러 사용자 관리 가능

#### 7. Technical Challenges
- **토큰 저장 위치**: localStorage (XSS 취약) vs HTTP-only 쿠키 (CSRF 고려) 결정
- **Refresh Token 관리**: 블랙리스트 저장소 (Redis 추가 필요 여부)
- **프론트엔드 토큰 갱신**: Axios interceptor 구현 및 동시 요청 처리
- **기존 인증 마이그레이션**: Django 세션 인증에서 JWT로 점진적 전환

#### 8. Acceptance Criteria
1. ✅ 사용자가 로그인 시 Access Token 및 Refresh Token 정상 발급
2. ✅ 모든 보호된 API 엔드포인트에서 JWT 토큰 검증 통과
3. ✅ Access Token 만료 시 Refresh Token으로 자동 갱신 성공
4. ✅ Admin 역할만 데이터셋 삭제 가능, Viewer는 조회만 가능
5. ✅ 로그아웃 시 Refresh Token 무효화 및 재사용 불가
6. ✅ pytest 테스트 커버리지 ≥ 90%

---

### SPEC 후보 2: SPEC-EXPORT-001 - 데이터 내보내기 시스템

#### 1. SPEC ID 및 제목
**SPEC-EXPORT-001**: 다중 형식 데이터 내보내기 시스템 (CSV, Excel, PDF)

#### 2. Priority
**High** - 사용자 요청 빈도가 높고 업무 효율성 직접 개선

#### 3. Estimated Complexity
**2/5** (낮음-중간)
- CSV: 간단 (Python csv 모듈)
- Excel: 중간 (openpyxl 활용, 이미 설치됨)
- PDF: 중간-높음 (reportlab 또는 WeasyPrint 필요)

#### 4. Dependencies
- **선행 조건**: SPEC-DASH-001 완료 (데이터 조회 API 존재)
- **연관 SPEC**:
  - SPEC-FILTER-001 (필터링된 데이터만 내보내기)
  - SPEC-AUTH-001 (권한별 내보내기 제한)

#### 5. Key Requirements (EARS 형식)

**REQ-EXPORT-001**: CSV 형식 내보내기
- **WHEN** 사용자가 데이터셋 또는 필터링된 데이터를 CSV로 내보내기 요청하면
- **THE SYSTEM SHALL** 현재 표시된 데이터를 CSV 형식으로 변환하고
- **AND** UTF-8 인코딩으로 파일을 생성하며
- **AND** 브라우저 다운로드를 트리거한다

**REQ-EXPORT-002**: Excel 형식 내보내기
- **WHEN** 사용자가 Excel 형식 내보내기를 요청하면
- **THE SYSTEM SHALL** openpyxl을 사용하여 .xlsx 파일을 생성하고
- **AND** 헤더 스타일링 (볼드, 배경색) 및 자동 열 너비 조정을 적용하며
- **AND** 여러 시트 지원 (데이터 + 요약 통계)을 제공한다

**REQ-EXPORT-003**: PDF 보고서 생성
- **WHEN** 사용자가 PDF 보고서 생성을 요청하면
- **THE SYSTEM SHALL** 데이터 테이블과 차트를 포함한 PDF를 생성하고
- **AND** 대학교 로고 및 생성 일시를 헤더에 포함하며
- **AND** 페이지네이션 및 목차를 자동 생성한다

**REQ-EXPORT-004**: 내보내기 진행 상태 표시
- **THE SYSTEM SHALL** 대용량 데이터 내보내기 시 진행률을 표시하고
- **AND** 비동기 작업으로 처리하여 UI 블로킹을 방지하며
- **AND** 완료 시 다운로드 링크를 제공한다

**REQ-EXPORT-005**: 내보내기 이력 관리
- **THE SYSTEM SHALL** 내보내기 작업 이력을 저장하고 (파일명, 형식, 일시, 사용자)
- **AND** 최근 내보낸 파일을 7일간 서버에 캐시하며
- **AND** 재다운로드 기능을 제공한다

#### 6. Business Value
- **업무 효율성**: 분석 결과를 즉시 보고서로 변환 가능
- **협업 강화**: 비기술직 팀원에게 Excel/PDF 공유 용이
- **데이터 활용도**: 외부 시스템 연동을 위한 CSV 내보내기
- **전문성**: PDF 보고서 자동 생성으로 시간 절약

#### 7. Technical Challenges
- **대용량 데이터 처리**: 10,000+ 레코드 내보내기 시 메모리 관리 (스트리밍 필요)
- **PDF 차트 렌더링**: Recharts를 이미지로 변환하여 PDF 삽입 (Puppeteer 또는 Canvas)
- **파일 저장소**: 임시 파일 저장 위치 (Railway 임시 디렉토리 vs S3)
- **비동기 작업 큐**: Celery + Redis 또는 Django-Q 도입 고려

#### 8. Acceptance Criteria
1. ✅ CSV 내보내기: 1,000개 레코드를 3초 이내 다운로드
2. ✅ Excel 내보내기: 스타일링 적용된 .xlsx 파일 생성
3. ✅ PDF 보고서: 차트 이미지 포함, 페이지네이션 적용
4. ✅ 진행 상태: 5,000개 이상 레코드 내보내기 시 진행률 표시
5. ✅ 이력 관리: 최근 7일 내보내기 이력 조회 및 재다운로드 가능
6. ✅ pytest 테스트: 각 형식별 내보내기 성공 검증

---

### SPEC 후보 3: SPEC-FILTER-001 - 고급 필터링 및 전체 텍스트 검색

#### 1. SPEC ID 및 제목
**SPEC-FILTER-001**: 고급 필터링, 전체 텍스트 검색, 저장된 필터 프리셋

#### 2. Priority
**High** - 대용량 데이터셋 활용도 개선을 위한 핵심 기능

#### 3. Estimated Complexity
**3/5** (중간)
- 기본 필터링: 낮음 (TanStack Table 기능 활용)
- 전체 텍스트 검색: 중간 (PostgreSQL Full-Text Search)
- 복합 필터: 중간-높음 (AND/OR 조건, 범위 검색)
- 필터 프리셋: 중간 (저장/불러오기 UI)

#### 4. Dependencies
- **선행 조건**: SPEC-DASH-001 완료
- **연관 SPEC**:
  - SPEC-EXPORT-001 (필터링된 데이터 내보내기)
  - SPEC-AUTH-001 (사용자별 저장된 필터)

#### 5. Key Requirements (EARS 형식)

**REQ-FILTER-001**: 컬럼별 고급 필터링
- **WHEN** 사용자가 특정 컬럼에 필터를 적용하면
- **THE SYSTEM SHALL** 다음 필터 타입을 지원하고
  - 텍스트: 포함, 시작, 끝, 정확히 일치
  - 숫자: 같음, 크다, 작다, 범위
  - 날짜: 특정일, 이전, 이후, 범위
- **AND** 여러 컬럼 필터를 AND/OR 조건으로 결합하며
- **AND** 실시간으로 결과를 업데이트한다

**REQ-FILTER-002**: 전체 텍스트 검색
- **WHEN** 사용자가 검색어를 입력하면
- **THE SYSTEM SHALL** PostgreSQL Full-Text Search를 사용하여
- **AND** 모든 텍스트 필드에서 검색을 수행하고
- **AND** 관련도 순으로 결과를 정렬하며
- **AND** 검색어 하이라이팅을 제공한다

**REQ-FILTER-003**: 필터 프리셋 저장
- **WHEN** 사용자가 현재 필터 조합을 저장 요청하면
- **THE SYSTEM SHALL** 프리셋 이름과 함께 필터 설정을 DB에 저장하고
- **AND** 사용자별 프리셋 목록을 제공하며
- **AND** 원클릭으로 저장된 프리셋을 불러올 수 있다

**REQ-FILTER-004**: URL 쿼리 기반 필터링
- **THE SYSTEM SHALL** 필터 상태를 URL 쿼리 파라미터로 인코딩하고
- **AND** URL 공유 시 동일한 필터가 적용되도록 하며
- **AND** 브라우저 뒤로/앞으로 버튼으로 필터 상태 이동을 지원한다

**REQ-FILTER-005**: 필터 성능 최적화
- **THE SYSTEM SHALL** 데이터베이스 인덱스를 활용하여 필터링 성능을 최적화하고
- **AND** 1,000개 레코드 필터링을 500ms 이내 완료하며
- **AND** 10,000개 이상 레코드는 페이지네이션과 결합하여 처리한다

#### 6. Business Value
- **생산성 향상**: 특정 데이터를 빠르게 찾아 분석 시간 단축
- **사용자 경험**: 직관적인 필터 UI로 학습 곡선 감소
- **협업 강화**: URL 또는 프리셋 공유로 팀원 간 동일한 뷰 공유
- **데이터 인사이트**: 복합 필터로 숨겨진 패턴 발견

#### 7. Technical Challenges
- **PostgreSQL Full-Text Search**: 한글 형태소 분석기 설정 (pg_trgm 확장)
- **프론트엔드 상태 관리**: TanStack Query + URL 동기화
- **복합 필터 쿼리 생성**: Django ORM Q 객체로 동적 쿼리 빌딩
- **성능 최적화**: 대용량 데이터셋에서 인덱스 전략 및 쿼리 최적화

#### 8. Acceptance Criteria
1. ✅ 컬럼별 필터: 텍스트/숫자/날짜 모든 타입 필터링 성공
2. ✅ 전체 텍스트 검색: 한글 검색 정확도 ≥ 95%
3. ✅ 필터 프리셋: 저장, 불러오기, 수정, 삭제 CRUD 완료
4. ✅ URL 필터링: URL 복사/공유 시 동일한 필터 적용
5. ✅ 성능: 5,000개 레코드 필터링을 1초 이내 완료
6. ✅ pytest + Vitest 테스트: 필터링 로직 및 UI 컴포넌트 검증

---

## 🚀 구현 순서 제안

### 권장 구현 순서 및 이유

#### 1단계: SPEC-AUTH-001 (JWT 인증) - 2주
**이유**:
- 다른 기능의 **기반**이 되는 보안 인프라
- 내보내기 권한 제어, 필터 프리셋 사용자 연결에 필수
- 프로덕션 배포 전 **필수 보안 요구사항**

**주요 작업**:
- Django REST Framework Simple JWT 설치
- 토큰 발급/검증 API 구현
- 프론트엔드 Axios interceptor 토큰 자동 갱신
- 역할 기반 권한 모델 설계 (Admin, Manager, Viewer)

#### 2단계: SPEC-EXPORT-001 (데이터 내보내기) - 1.5주
**이유**:
- **독립적** 기능으로 인증 시스템과 병렬 개발 가능 (단, 최종 권한 연결은 1단계 후)
- 사용자 요청 빈도 높고 **즉시 가치 제공**
- 기술적 난이도가 상대적으로 낮아 빠른 성과 확인

**주요 작업**:
- CSV 내보내기 API 구현 (간단)
- Excel 내보내기 (openpyxl 활용)
- PDF 보고서 생성 (reportlab 또는 WeasyPrint)
- 프론트엔드 다운로드 버튼 및 진행 상태 UI

#### 3단계: SPEC-FILTER-001 (고급 필터링) - 2주
**이유**:
- 인증 및 내보내기 완료 후 **전체 시스템 사용성 극대화**
- 내보내기 기능과 **시너지** (필터링된 데이터만 내보내기)
- PostgreSQL FTS 설정 필요로 인프라 작업 포함

**주요 작업**:
- PostgreSQL Full-Text Search 인덱스 생성
- Django ORM 복합 필터 쿼리 빌더
- TanStack Table 고급 필터 UI
- 필터 프리셋 저장/관리 기능

### 대안적 접근: 애자일 스프린트

만약 **애자일 방식**으로 진행한다면:
- **Sprint 1 (2주)**: AUTH-001 기본 JWT 인증 (역할 제외)
- **Sprint 2 (2주)**: EXPORT-001 CSV/Excel 내보내기
- **Sprint 3 (2주)**: FILTER-001 기본 필터링 + 전체 텍스트 검색
- **Sprint 4 (1주)**: AUTH-001 역할 기반 권한 + EXPORT-001 PDF + FILTER-001 프리셋

---

## 🛠️ 기술 스택 추가 고려사항

### Backend 추가 라이브러리

#### 인증 (SPEC-AUTH-001)
```python
# requirements.txt 추가
djangorestframework-simplejwt==5.3.1  # JWT 토큰 관리
django-cors-headers==4.4.0  # 이미 설치됨
```

#### 내보내기 (SPEC-EXPORT-001)
```python
# requirements.txt 추가
reportlab==4.2.2  # PDF 생성 (Option 1)
weasyprint==62.3  # PDF 생성 (Option 2, HTML→PDF)
pillow==10.4.0  # 이미지 처리 (차트 임베딩)

# 대안: openpyxl 이미 설치됨 (Excel)
# 대안: csv는 Python 표준 라이브러리
```

#### 필터링 (SPEC-FILTER-001)
```bash
# PostgreSQL 확장 (Railway에서 실행)
CREATE EXTENSION IF NOT EXISTS pg_trgm;  # 한글 검색 최적화
CREATE EXTENSION IF NOT EXISTS btree_gin;  # 복합 인덱스 성능 향상
```

### Frontend 추가 라이브러리

#### 인증 (SPEC-AUTH-001)
```json
{
  "dependencies": {
    "axios": "^1.7.2",  // 이미 설치됨
    "js-cookie": "^3.0.5",  // 쿠키 관리 (옵션)
    "zustand": "^4.5.2"  // 전역 상태 관리 (사용자 정보)
  }
}
```

#### 내보내기 (SPEC-EXPORT-001)
```json
{
  "dependencies": {
    "file-saver": "^2.0.5",  // 파일 다운로드 헬퍼
    "html2canvas": "^1.4.1"  // 차트 → 이미지 변환 (PDF용)
  }
}
```

#### 필터링 (SPEC-FILTER-001)
```json
{
  "dependencies": {
    "@tanstack/react-table": "^8.20.1",  // 이미 설치됨
    "react-select": "^5.8.0",  // 멀티 셀렉트 필터
    "date-fns": "^3.6.0"  // 날짜 범위 필터
  }
}
```

### 인프라 추가 고려사항

#### 비동기 작업 큐 (대용량 내보내기)
```python
# Option 1: Django-Q (가벼움)
django-q==1.6.1

# Option 2: Celery + Redis (강력함, 별도 Redis 필요)
celery==5.4.0
redis==5.0.8
```

#### 파일 스토리지 (내보낸 파일 캐싱)
```python
# Option 1: Railway 로컬 스토리지 (7일 후 삭제)
# Option 2: AWS S3 / Supabase Storage
django-storages==1.14.4
boto3==1.35.0  # S3용
```

---

## 📝 다음 단계 (alfred:1-plan 워크플로우)

### 사용자 선택 필요

다음 중 하나를 선택하여 진행해주세요:

**옵션 1**: SPEC-AUTH-001 (JWT 인증) 상세 문서 작성
- `.moai/specs/SPEC-AUTH-001/` 디렉토리 생성
- `spec.md`, `plan.md`, `acceptance.md` 작성
- Git 커밋 및 브랜치 생성

**옵션 2**: SPEC-EXPORT-001 (데이터 내보내기) 상세 문서 작성

**옵션 3**: SPEC-FILTER-001 (고급 필터링) 상세 문서 작성

**옵션 4**: 3개 모두 동시에 개요 문서 작성 (간략 버전)

**옵션 5**: 분석 결과만 확인하고 나중에 선택

---

## 🎓 MoAI-ADK 메타데이터

- **프레임워크**: MoAI-ADK v2.0
- **Alfred 단계**: alfred:1-plan (SPEC 계획)
- **다음 단계**: alfred:2-run (TDD 구현) - 사용자 선택 후
- **품질 기준**: TRUST (Traceability, Readability, Usability, Security, Testability)
- **문서화 원칙**: @TAG 시스템 (@SPEC → @TEST → @CODE → @DOC)

---

_분석 완료: 2025-11-03 by @Sam via alfred:1-plan_

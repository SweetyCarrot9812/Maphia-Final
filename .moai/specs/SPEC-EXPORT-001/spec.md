# SPEC-EXPORT-001: 다중 형식 데이터 내보내기 시스템

**Status**: Draft
**Created**: 2025-11-03
**Author**: @Sam
**Tech Lead**: 🎩 Alfred@[MoAI](https://adk.mo.ai.kr)
**Priority**: High
**Complexity**: 2/5
**Estimated Duration**: 1.5 weeks

---

## 1. Overview

### 1.1 Purpose
University Dashboard에서 분석한 데이터를 다양한 형식(CSV, Excel, PDF)으로 내보내기하여 보고서 작성, 외부 시스템 연동, 팀 협업을 지원합니다. 대용량 데이터 처리를 위한 비동기 작업 및 진행 상태 표시를 포함합니다.

### 1.2 Business Value
- **업무 효율성**: 분석 결과를 즉시 보고서로 변환 가능
- **협업 강화**: 비기술직 팀원에게 Excel/PDF 공유 용이
- **데이터 활용도**: CSV 내보내기로 외부 시스템 연동
- **전문성**: PDF 보고서 자동 생성으로 시간 절약 (수작업 대비 80% 단축)

### 1.3 Dependencies
- **선행 조건**:
  - SPEC-DASH-001 완료 (데이터 조회 API 존재)
  - openpyxl 라이브러리 설치 완료
- **연관 SPEC**:
  - SPEC-FILTER-001: 필터링된 데이터만 선택적 내보내기
  - SPEC-AUTH-001: 역할별 내보내기 권한 제어 (Viewer는 내보내기 불가)

### 1.4 Tech Stack
- **Backend**:
  - CSV: Python `csv` 모듈 (표준 라이브러리)
  - Excel: `openpyxl==3.1.5` (이미 설치됨)
  - PDF: `reportlab==4.2.2` 또는 `WeasyPrint==62.3`
  - 이미지 처리: `Pillow==10.4.0`
  - 비동기 작업: `django-q==1.6.1` (옵션) 또는 `Celery + Redis`
- **Frontend**:
  - 파일 다운로드: `file-saver==2.0.5`
  - 차트 → 이미지: `html2canvas==1.4.1` (PDF 차트 삽입용)
  - 진행 상태: 커스텀 Progress Bar 컴포넌트

### 1.5 Success Criteria
- ✅ CSV 내보내기: 1,000개 레코드를 3초 이내 완료
- ✅ Excel 내보내기: 스타일링 적용된 .xlsx 파일 생성
- ✅ PDF 보고서: 차트 이미지 포함, 페이지네이션 적용
- ✅ 진행 상태: 5,000개 이상 레코드 내보내기 시 진행률 표시
- ✅ 이력 관리: 최근 7일 내보내기 이력 조회 및 재다운로드 가능
- ✅ pytest 테스트 커버리지 ≥ 85%

---

## 2. Functional Requirements (EARS Format)

### 2.1 CSV 형식 내보내기

**@SPEC:REQ-EXPORT-001** - CSV 내보내기 기본 기능
- **WHEN** 사용자가 데이터셋 또는 필터링된 데이터를 CSV로 내보내기 요청하면
- **THE SYSTEM SHALL** 현재 표시된 데이터를 CSV 형식으로 변환하고
- **AND** UTF-8 인코딩(BOM 포함)으로 파일을 생성하며
- **AND** 헤더 행에 컬럼명을 포함하고
- **AND** HTTP Content-Disposition 헤더로 브라우저 다운로드를 트리거한다
```
Content-Type: text/csv; charset=utf-8
Content-Disposition: attachment; filename="dataset_2025-11-03.csv"
```

**@SPEC:REQ-EXPORT-002** - CSV 특수문자 처리
- **WHEN** 데이터에 쉼표(,), 따옴표("), 줄바꿈이 포함된 경우
- **THE SYSTEM SHALL** RFC 4180 표준에 따라 이스케이프 처리하고
- **AND** 필드를 큰따옴표로 감싸며
- **AND** 큰따옴표는 이중 큰따옴표("")로 이스케이프한다

예시:
```csv
id,name,description
1,"John Doe","Works at ""ABC Corp"""
2,"Jane, Smith","Product
Manager"
```

---

### 2.2 Excel 형식 내보내기

**@SPEC:REQ-EXPORT-003** - Excel 기본 내보내기
- **WHEN** 사용자가 Excel 형식(.xlsx) 내보내기를 요청하면
- **THE SYSTEM SHALL** openpyxl을 사용하여 워크북을 생성하고
- **AND** 첫 번째 시트에 데이터를 작성하며
- **AND** 헤더 행에 스타일링을 적용한다 (볼드, 배경색 #4472C4, 흰색 글씨)
- **AND** 자동 열 너비 조정을 적용하고
- **AND** 데이터 행에 교차 줄무늬(zebra striping)를 적용한다

**@SPEC:REQ-EXPORT-004** - Excel 다중 시트
- **WHEN** 사용자가 "상세 보고서" 옵션을 선택하면
- **THE SYSTEM SHALL** 다음 시트를 포함한 워크북을 생성하고
  - **Sheet 1 "데이터"**: 전체 데이터 테이블
  - **Sheet 2 "요약 통계"**: 카테고리별 집계, 평균, 합계
  - **Sheet 3 "차트"**: 막대/파이 차트 임베딩
- **AND** 각 시트에 적절한 제목과 설명을 추가하며
- **AND** 시트 간 내부 하이퍼링크를 생성한다

**@SPEC:REQ-EXPORT-005** - Excel 수식 및 서식
- **THE SYSTEM SHALL** 숫자 데이터에 천 단위 구분 기호를 적용하고
- **AND** 날짜 데이터에 "YYYY-MM-DD" 형식을 적용하며
- **AND** 마지막 행에 합계 수식을 추가한다 (해당하는 경우)
```python
# 예시: 마지막 행에 합계
ws[f'C{last_row}'] = f'=SUM(C2:C{last_row-1})'
```

---

### 2.3 PDF 보고서 생성

**@SPEC:REQ-EXPORT-006** - PDF 기본 보고서
- **WHEN** 사용자가 PDF 보고서 생성을 요청하면
- **THE SYSTEM SHALL** reportlab 또는 WeasyPrint를 사용하여 PDF를 생성하고
- **AND** 다음 요소를 포함하며
  - **헤더**: 대학교 로고, 보고서 제목, 생성 일시
  - **요약 섹션**: 주요 통계 (총 레코드 수, 카테고리 분포 등)
  - **데이터 테이블**: 페이지네이션 적용
  - **차트**: 막대/선/파이 차트 이미지 삽입
  - **푸터**: 페이지 번호 (예: "Page 1 of 5")
- **AND** A4 페이지 크기 및 여백(top: 2cm, bottom: 2cm, left: 2.5cm, right: 2.5cm)을 적용한다

**@SPEC:REQ-EXPORT-007** - PDF 차트 이미지 삽입
- **WHEN** PDF에 차트를 포함해야 할 때
- **THE SYSTEM SHALL** 프론트엔드에서 html2canvas로 차트를 이미지로 변환하고
- **AND** Base64 인코딩된 이미지를 백엔드로 전송하며
- **AND** Pillow로 이미지 디코딩 및 크기 조정을 수행하고
- **AND** reportlab에서 이미지를 PDF에 임베딩한다

**@SPEC:REQ-EXPORT-008** - PDF 목차 및 책갈피
- **WHEN** PDF 페이지가 5페이지 이상인 경우
- **THE SYSTEM SHALL** 첫 페이지에 목차를 자동 생성하고
- **AND** 각 섹션에 PDF 책갈피(bookmark)를 추가하며
- **AND** 목차에서 클릭 시 해당 페이지로 이동 가능하게 한다

---

### 2.4 진행 상태 표시

**@SPEC:REQ-EXPORT-009** - 비동기 작업 처리
- **WHEN** 내보내기 레코드 수가 5,000개 이상이면
- **THE SYSTEM SHALL** 비동기 작업 큐(Django-Q 또는 Celery)에 작업을 추가하고
- **AND** 작업 ID를 즉시 반환하며
- **AND** 프론트엔드에서 작업 상태를 폴링(polling) 또는 WebSocket으로 조회할 수 있게 한다

**@SPEC:REQ-EXPORT-010** - 진행률 표시
- **WHEN** 비동기 작업이 진행 중일 때
- **THE SYSTEM SHALL** 작업 테이블에 진행률(0-100%)을 저장하고
- **AND** API 엔드포인트 GET `/api/export/jobs/{job_id}/` 로 상태 조회를 제공하며
- **AND** 프론트엔드에서 Progress Bar를 표시하고
- **AND** 완료 시 다운로드 링크를 제공한다

응답 예시:
```json
{
  "job_id": "abc123",
  "status": "processing",
  "progress": 65,
  "message": "Generating PDF... (6,500 / 10,000 records)",
  "download_url": null
}
```

완료 시:
```json
{
  "job_id": "abc123",
  "status": "completed",
  "progress": 100,
  "message": "PDF ready for download",
  "download_url": "/media/exports/dataset_2025-11-03.pdf"
}
```

**@SPEC:REQ-EXPORT-011** - 작업 취소
- **WHEN** 사용자가 진행 중인 내보내기 작업을 취소하면
- **THE SYSTEM SHALL** 작업 상태를 "cancelled"로 변경하고
- **AND** 비동기 작업을 중단하며
- **AND** 임시 파일을 삭제한다

---

### 2.5 내보내기 이력 관리

**@SPEC:REQ-EXPORT-012** - 이력 저장
- **WHEN** 내보내기 작업이 완료되면
- **THE SYSTEM SHALL** ExportHistory 테이블에 다음 정보를 저장하고
  - 사용자 ID
  - 파일 형식 (csv, excel, pdf)
  - 원본 데이터셋 ID
  - 레코드 수
  - 파일 크기
  - 파일 경로 (서버 저장 경로)
  - 생성 일시
  - 필터 조건 (JSON)
- **AND** 파일을 7일간 서버에 캐시한다

**@SPEC:REQ-EXPORT-013** - 이력 조회 및 재다운로드
- **WHEN** 사용자가 내보내기 이력 페이지를 방문하면
- **THE SYSTEM SHALL** 최근 30일 이력을 날짜 역순으로 표시하고
- **AND** 각 항목에 "재다운로드" 버튼을 제공하며
- **AND** 7일 이내 파일은 즉시 다운로드 가능하고
- **AND** 7일 초과 파일은 "만료됨" 상태로 표시한다

**@SPEC:REQ-EXPORT-014** - 이력 삭제
- **WHEN** 사용자가 이력 항목 삭제를 요청하면
- **THE SYSTEM SHALL** 데이터베이스 레코드와 파일을 모두 삭제하고
- **AND** 삭제 이벤트를 감사 로그에 기록한다

---

### 2.6 권한 기반 내보내기

**@SPEC:REQ-EXPORT-015** - 역할별 권한 제어
- **THE SYSTEM SHALL** SPEC-AUTH-001의 역할을 기반으로 내보내기 권한을 제어하고
  - **Admin**: 모든 형식 내보내기 가능, 이력 조회 가능
  - **Manager**: 모든 형식 내보내기 가능, 자신의 이력만 조회
  - **Viewer**: 내보내기 불가 (HTTP 403 반환)
- **AND** 프론트엔드에서 권한 없는 역할에게 내보내기 버튼을 표시하지 않는다

---

## 3. Non-Functional Requirements

### 3.1 성능 (Performance)

**@SPEC:NFR-EXPORT-001** - 처리 속도
- **THE SYSTEM SHALL** 다음 성능 기준을 충족하고
  - **CSV 내보내기**: 1,000개 레코드를 3초 이내
  - **Excel 내보내기**: 1,000개 레코드를 5초 이내
  - **PDF 보고서**: 100개 레코드(차트 포함)를 10초 이내
- **AND** 5,000개 이상 레코드는 비동기 작업으로 처리하며
- **AND** 10,000개 이상 레코드는 스트리밍 방식으로 메모리 사용을 최적화한다

**@SPEC:NFR-EXPORT-002** - 메모리 관리
- **THE SYSTEM SHALL** 대용량 데이터 내보내기 시 메모리 사용량을 최대 500MB로 제한하고
- **AND** Django ORM의 `iterator(chunk_size=1000)` 사용으로 청크 단위 처리를 적용하며
- **AND** CSV/Excel 스트리밍 출력을 사용하여 전체 데이터를 메모리에 로드하지 않는다

예시:
```python
# 스트리밍 CSV 출력
import csv
from django.http import StreamingHttpResponse

class Echo:
    def write(self, value):
        return value

def stream_csv(queryset):
    writer = csv.writer(Echo())
    yield writer.writerow(['id', 'name', 'value'])
    for obj in queryset.iterator(chunk_size=1000):
        yield writer.writerow([obj.id, obj.name, obj.value])

response = StreamingHttpResponse(
    stream_csv(DataRecord.objects.all()),
    content_type='text/csv'
)
```

---

### 3.2 확장성 (Scalability)

**@SPEC:NFR-EXPORT-003** - 동시 작업 처리
- **THE SYSTEM SHALL** 최대 10개의 동시 내보내기 작업을 처리하고
- **AND** 작업 큐가 가득 차면 HTTP 503 Service Unavailable을 반환하며
- **AND** 대기 중인 작업 수를 프론트엔드에 표시한다

**@SPEC:NFR-EXPORT-004** - 파일 저장소
- **THE SYSTEM SHALL** 내보낸 파일을 다음 위치에 저장하고
  - **개발 환경**: Railway 로컬 스토리지 (`/tmp/exports/`)
  - **프로덕션 환경**: AWS S3 또는 Supabase Storage (옵션)
- **AND** 7일 후 자동 삭제 정책을 적용하며
- **AND** 스토리지 용량이 80% 초과 시 경고를 로그에 기록한다

---

### 3.3 사용성 (Usability)

**@SPEC:NFR-EXPORT-005** - 명확한 피드백
- **THE SYSTEM SHALL** 내보내기 시작 시 "내보내기 중..." 메시지를 표시하고
- **AND** 진행 중인 작업은 Progress Bar로 진행률을 표시하며
- **AND** 완료 시 "다운로드 준비 완료" 알림을 표시하고
- **AND** 에러 발생 시 구체적인 에러 메시지를 제공한다 (예: "파일 크기가 100MB를 초과하여 내보내기할 수 없습니다.")

**@SPEC:NFR-EXPORT-006** - 사용자 친화적 UI
- **THE SYSTEM SHALL** 내보내기 버튼에 아이콘과 레이블을 함께 표시하고
  - CSV: 📄 "CSV 내보내기"
  - Excel: 📊 "Excel 내보내기"
  - PDF: 📑 "PDF 보고서"
- **AND** 각 형식의 예상 파일 크기를 표시하며
- **AND** 대용량 데이터(>5,000개) 시 "시간이 걸릴 수 있습니다" 경고를 표시한다

---

### 3.4 신뢰성 (Reliability)

**@SPEC:NFR-EXPORT-007** - 에러 처리
- **WHEN** 내보내기 작업 중 에러가 발생하면
- **THE SYSTEM SHALL** 작업 상태를 "failed"로 변경하고
- **AND** 에러 메시지를 작업 테이블에 저장하며
- **AND** 임시 파일을 정리하고
- **AND** 프론트엔드에 재시도 옵션을 제공한다

**@SPEC:NFR-EXPORT-008** - 파일 무결성
- **THE SYSTEM SHALL** 생성된 파일의 MD5 해시를 계산하여 저장하고
- **AND** 다운로드 시 파일 크기를 검증하며
- **AND** 손상된 파일 발견 시 자동으로 재생성을 시도한다

---

## 4. Data Model

### 4.1 ExportJob 모델

```python
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ExportJob(models.Model):
    """비동기 내보내기 작업 관리"""

    STATUS_CHOICES = [
        ('pending', '대기 중'),
        ('processing', '처리 중'),
        ('completed', '완료'),
        ('failed', '실패'),
        ('cancelled', '취소됨'),
    ]

    FORMAT_CHOICES = [
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('pdf', 'PDF'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='export_jobs')
    dataset = models.ForeignKey('Dataset', on_delete=models.CASCADE, null=True, blank=True)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress = models.IntegerField(default=0)  # 0-100
    record_count = models.IntegerField(default=0)
    file_size = models.BigIntegerField(null=True, blank=True)  # bytes
    file_path = models.CharField(max_length=500, blank=True)
    download_url = models.URLField(blank=True)
    filter_conditions = models.JSONField(default=dict)  # 필터 조건 저장
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'export_jobs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f"{self.get_format_display()} export by {self.user.username} ({self.get_status_display()})"
```

---

### 4.2 ExportHistory 모델

```python
class ExportHistory(models.Model):
    """내보내기 이력 (완료된 작업만 저장)"""

    id = models.AutoField(primary_key=True)
    job = models.OneToOneField(ExportJob, on_delete=models.CASCADE, related_name='history')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='export_history')
    dataset = models.ForeignKey('Dataset', on_delete=models.SET_NULL, null=True, blank=True)
    format = models.CharField(max_length=10)
    filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField()
    record_count = models.IntegerField()
    file_path = models.CharField(max_length=500)
    download_url = models.URLField()
    filter_conditions = models.JSONField(default=dict)
    file_hash = models.CharField(max_length=32, blank=True)  # MD5 hash
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # 7일 후
    download_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'export_history'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"{self.filename} by {self.user.username}"

    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at
```

---

## 5. API Endpoints

### 5.1 내보내기 요청

#### POST /api/export/csv/
**설명**: CSV 형식 내보내기

**Request**:
```json
{
  "dataset_id": 1,
  "filters": {
    "category": "enrollment",
    "date_range": ["2025-01-01", "2025-12-31"]
  },
  "columns": ["id", "name", "value"]  // 선택적, 없으면 전체 컬럼
}
```

**Response (200 OK - 소량 데이터, 즉시 반환)**:
```
Content-Type: text/csv; charset=utf-8
Content-Disposition: attachment; filename="dataset_2025-11-03.csv"

[CSV 데이터]
```

**Response (202 Accepted - 대량 데이터, 비동기 처리)**:
```json
{
  "job_id": "abc123-def456",
  "status": "pending",
  "message": "내보내기 작업이 시작되었습니다. 잠시 후 완료됩니다.",
  "status_url": "/api/export/jobs/abc123-def456/"
}
```

---

#### POST /api/export/excel/
**설명**: Excel 형식 내보내기

**Request**:
```json
{
  "dataset_id": 1,
  "filters": {...},
  "options": {
    "include_summary": true,  // 요약 통계 시트 포함
    "include_charts": true,    // 차트 시트 포함
    "styling": "professional"  // "simple" | "professional"
  }
}
```

**Response**: CSV와 동일 (즉시 반환 또는 202 Accepted)

---

#### POST /api/export/pdf/
**설명**: PDF 보고서 생성

**Request**:
```json
{
  "dataset_id": 1,
  "filters": {...},
  "options": {
    "include_charts": true,
    "chart_images": [
      {
        "type": "bar",
        "data_base64": "iVBORw0KGgoAAAANS..."  // html2canvas로 변환된 이미지
      }
    ],
    "orientation": "portrait",  // "portrait" | "landscape"
    "page_size": "A4"
  }
}
```

**Response**: 항상 202 Accepted (PDF 생성은 시간이 걸림)

---

### 5.2 작업 상태 조회

#### GET /api/export/jobs/{job_id}/
**설명**: 비동기 작업 상태 조회

**Response (Processing)**:
```json
{
  "job_id": "abc123-def456",
  "status": "processing",
  "progress": 65,
  "message": "Generating PDF... (6,500 / 10,000 records)",
  "record_count": 10000,
  "created_at": "2025-11-03T10:30:00Z",
  "download_url": null
}
```

**Response (Completed)**:
```json
{
  "job_id": "abc123-def456",
  "status": "completed",
  "progress": 100,
  "message": "PDF ready for download",
  "record_count": 10000,
  "file_size": 2048576,
  "created_at": "2025-11-03T10:30:00Z",
  "completed_at": "2025-11-03T10:32:15Z",
  "download_url": "/media/exports/dataset_2025-11-03.pdf"
}
```

---

#### DELETE /api/export/jobs/{job_id}/
**설명**: 진행 중인 작업 취소

**Response (200 OK)**:
```json
{
  "message": "작업이 취소되었습니다."
}
```

---

### 5.3 이력 관리

#### GET /api/export/history/
**설명**: 내보내기 이력 조회 (최근 30일)

**Query Parameters**:
- `format`: csv, excel, pdf (옵션)
- `page`: 페이지 번호
- `page_size`: 페이지 크기 (기본 20)

**Response**:
```json
{
  "count": 45,
  "next": "/api/export/history/?page=2",
  "previous": null,
  "results": [
    {
      "id": 123,
      "job_id": "abc123",
      "format": "excel",
      "filename": "dataset_2025-11-03.xlsx",
      "file_size": 1024576,
      "record_count": 5000,
      "created_at": "2025-11-03T10:32:15Z",
      "expires_at": "2025-11-10T10:32:15Z",
      "download_url": "/media/exports/dataset_2025-11-03.xlsx",
      "is_expired": false,
      "download_count": 3
    }
  ]
}
```

---

#### GET /api/export/history/{id}/download/
**설명**: 이력에서 파일 재다운로드

**Response**: 파일 스트리밍 또는 404 (만료됨)

---

#### DELETE /api/export/history/{id}/
**설명**: 이력 및 파일 삭제

**Response (204 No Content)**

---

## 6. User Interface

### 6.1 내보내기 버튼 (데이터 테이블 페이지)

**위치**: 데이터 테이블 상단 우측

**UI 구성**:
```tsx
<div className="flex gap-2">
  <Button onClick={handleExportCSV} icon={<FileTextIcon />}>
    CSV 내보내기
  </Button>
  <Button onClick={handleExportExcel} icon={<FileSpreadsheetIcon />}>
    Excel 내보내기
  </Button>
  <Button onClick={handleExportPDF} icon={<FileIcon />}>
    PDF 보고서
  </Button>
</div>
```

**권한 제어**:
```tsx
<RoleGuard allowedRoles={['admin', 'manager']}>
  <ExportButtons />
</RoleGuard>
```

---

### 6.2 내보내기 옵션 모달

**CSV 내보내기 옵션**:
- 전체 데이터 또는 필터링된 데이터
- 선택된 컬럼만 내보내기 (체크박스)

**Excel 내보내기 옵션**:
- 요약 통계 시트 포함 여부
- 차트 시트 포함 여부
- 스타일링: 간단 / 전문가

**PDF 내보내기 옵션**:
- 차트 포함 여부
- 페이지 방향: 세로(Portrait) / 가로(Landscape)
- 페이지 크기: A4 / Letter

---

### 6.3 진행 상태 모달

```tsx
<Modal open={isExporting}>
  <h2>PDF 보고서 생성 중...</h2>
  <ProgressBar value={progress} max={100} />
  <p>{message}</p>
  <p>예상 소요 시간: {estimatedTime}초</p>
  <Button onClick={handleCancel} variant="secondary">
    취소
  </Button>
</Modal>
```

---

### 6.4 내보내기 이력 페이지

**URL**: `/export-history`

**UI 구성**:
- 테이블: 파일명, 형식, 크기, 레코드 수, 생성일, 만료일, 다운로드 수
- 액션: "다운로드", "삭제"
- 필터: 형식별 필터 (CSV/Excel/PDF)
- 페이지네이션

---

## 7. Testing Strategy

### 7.1 Backend 테스트 (pytest)

**테스트 커버리지 목표**: ≥ 85%

**주요 테스트 케이스**:
```python
# tests/test_export_api.py

@pytest.mark.django_db
def test_csv_export_small_dataset(api_client):
    """소량 데이터(< 5,000개) CSV 내보내기 즉시 반환"""
    dataset = create_test_dataset(record_count=100)
    api_client.force_authenticate(user=create_manager())

    response = api_client.post('/api/export/csv/', {
        'dataset_id': dataset.id
    })

    assert response.status_code == 200
    assert response['Content-Type'] == 'text/csv; charset=utf-8'
    assert 'Content-Disposition' in response

@pytest.mark.django_db
def test_csv_export_large_dataset_async(api_client):
    """대량 데이터(≥ 5,000개) CSV 내보내기 비동기 처리"""
    dataset = create_test_dataset(record_count=10000)
    api_client.force_authenticate(user=create_manager())

    response = api_client.post('/api/export/csv/', {
        'dataset_id': dataset.id
    })

    assert response.status_code == 202  # Accepted
    assert 'job_id' in response.data
    assert response.data['status'] == 'pending'

@pytest.mark.django_db
def test_excel_export_with_styling(api_client):
    """Excel 내보내기 - 스타일링 적용 확인"""
    dataset = create_test_dataset(record_count=100)
    api_client.force_authenticate(user=create_manager())

    response = api_client.post('/api/export/excel/', {
        'dataset_id': dataset.id,
        'options': {'styling': 'professional'}
    })

    # 파일 다운로드 후 openpyxl로 검증
    from openpyxl import load_workbook
    wb = load_workbook(response.content)
    ws = wb.active

    # 헤더 스타일 확인
    header_cell = ws['A1']
    assert header_cell.font.bold == True
    assert header_cell.fill.start_color.rgb == '004472C4'

@pytest.mark.django_db
def test_pdf_export_with_charts(api_client):
    """PDF 보고서 - 차트 이미지 포함 확인"""
    dataset = create_test_dataset(record_count=50)
    api_client.force_authenticate(user=create_manager())

    # Mock chart image
    chart_base64 = "iVBORw0KGgo..."

    response = api_client.post('/api/export/pdf/', {
        'dataset_id': dataset.id,
        'options': {
            'include_charts': True,
            'chart_images': [{'type': 'bar', 'data_base64': chart_base64}]
        }
    })

    assert response.status_code == 202
    job_id = response.data['job_id']

    # 작업 완료 대기 (테스트에서는 동기 실행)
    job = ExportJob.objects.get(id=job_id)
    assert job.status == 'completed'
    assert job.file_path.endswith('.pdf')

@pytest.mark.django_db
def test_export_permission_viewer_denied(api_client):
    """Viewer 역할 - 내보내기 권한 없음"""
    viewer = User.objects.create_user(username='viewer', role='viewer')
    api_client.force_authenticate(user=viewer)

    response = api_client.post('/api/export/csv/', {'dataset_id': 1})
    assert response.status_code == 403

@pytest.mark.django_db
def test_export_history_retrieval(api_client):
    """내보내기 이력 조회"""
    user = create_manager()
    create_export_history(user=user, count=5)
    api_client.force_authenticate(user=user)

    response = api_client.get('/api/export/history/')
    assert response.status_code == 200
    assert response.data['count'] == 5

@pytest.mark.django_db
def test_export_file_expiration(api_client):
    """7일 후 파일 만료 확인"""
    from datetime import timedelta
    from django.utils import timezone

    history = create_export_history(
        expires_at=timezone.now() - timedelta(days=1)
    )

    assert history.is_expired() == True

    api_client.force_authenticate(user=history.user)
    response = api_client.get(f'/api/export/history/{history.id}/download/')
    assert response.status_code == 404
```

---

### 7.2 Frontend 테스트 (Vitest)

**주요 테스트 케이스**:
```typescript
// tests/export.test.ts

describe('Export Functionality', () => {
  it('CSV 내보내기 버튼 클릭 시 파일 다운로드', async () => {
    const mockDownload = vi.fn()
    global.URL.createObjectURL = vi.fn(() => 'blob:http://localhost/abc')

    render(<DataTable />)
    const csvButton = screen.getByText('CSV 내보내기')
    await userEvent.click(csvButton)

    await waitFor(() => {
      expect(mockDownload).toHaveBeenCalled()
    })
  })

  it('대량 데이터 내보내기 시 진행률 모달 표시', async () => {
    const mockApi = {
      post: vi.fn().mockResolvedValue({
        data: { job_id: 'abc123', status: 'pending' }
      }),
      get: vi.fn().mockResolvedValue({
        data: { job_id: 'abc123', status: 'processing', progress: 50 }
      })
    }

    render(<DataTable />)
    const excelButton = screen.getByText('Excel 내보내기')
    await userEvent.click(excelButton)

    // 진행률 모달 확인
    await waitFor(() => {
      expect(screen.getByText(/생성 중.../)).toBeInTheDocument()
      expect(screen.getByRole('progressbar')).toBeInTheDocument()
    })
  })

  it('Viewer 역할 사용자에게 내보내기 버튼 미표시', () => {
    const { queryByText } = render(<DataTable />, {
      initialState: { user: { role: 'viewer' } }
    })

    expect(queryByText('CSV 내보내기')).toBeNull()
  })
})
```

---

## 8. Technical Considerations

### 8.1 대용량 데이터 처리

**문제**: 10,000개 이상 레코드 내보내기 시 메모리 부족 및 타임아웃

**해결책**:
1. **스트리밍 출력** (CSV/Excel)
```python
# CSV 스트리밍
from django.http import StreamingHttpResponse

def stream_csv(queryset):
    import csv
    from io import StringIO

    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(['id', 'name', 'value'])
    yield buffer.getvalue()
    buffer.seek(0)
    buffer.truncate(0)

    for obj in queryset.iterator(chunk_size=1000):
        writer.writerow([obj.id, obj.name, obj.value])
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)
```

2. **비동기 작업 큐** (Django-Q 또는 Celery)
```python
# tasks.py
from django_q.tasks import async_task

def export_large_dataset(job_id, dataset_id, format):
    job = ExportJob.objects.get(id=job_id)
    job.status = 'processing'
    job.started_at = timezone.now()
    job.save()

    try:
        # 내보내기 로직
        file_path = generate_export(dataset_id, format)

        job.status = 'completed'
        job.file_path = file_path
        job.completed_at = timezone.now()
        job.save()
    except Exception as e:
        job.status = 'failed'
        job.error_message = str(e)
        job.save()

# View에서 호출
async_task('export_large_dataset', job.id, dataset_id, format)
```

---

### 8.2 PDF 차트 이미지 처리

**문제**: 프론트엔드 Recharts를 PDF에 포함

**해결책**:
1. **프론트엔드**: html2canvas로 차트 → 이미지 변환
```typescript
import html2canvas from 'html2canvas'

async function captureChart(chartElement: HTMLElement): Promise<string> {
  const canvas = await html2canvas(chartElement)
  return canvas.toDataURL('image/png')  // Base64
}
```

2. **백엔드**: Base64 이미지 → PDF 삽입
```python
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Image
from PIL import Image as PILImage
import base64
import io

def add_chart_to_pdf(canvas, chart_base64):
    # Base64 디코딩
    image_data = base64.b64decode(chart_base64.split(',')[1])
    image = PILImage.open(io.BytesIO(image_data))

    # 크기 조정 (PDF 너비에 맞춤)
    max_width = 400
    ratio = max_width / image.width
    new_height = int(image.height * ratio)

    # PDF에 삽입
    img = Image(io.BytesIO(image_data), width=max_width, height=new_height)
    return img
```

---

### 8.3 파일 저장소 전략

**옵션 1: 로컬 스토리지 (Railway)**
- 경로: `/tmp/exports/`
- 장점: 설정 간단, 추가 비용 없음
- 단점: 재시작 시 파일 손실, 용량 제한

**옵션 2: AWS S3**
```python
# settings.py
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
            "bucket_name": "university-dashboard-exports",
            "location": "exports/",
        },
    },
}
```

**옵션 3: Supabase Storage**
```python
from supabase import create_client

supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def upload_to_supabase(file_path, filename):
    with open(file_path, 'rb') as f:
        res = supabase.storage.from_('exports').upload(filename, f)
    return res['publicURL']
```

**권장**: 개발 환경은 로컬, 프로덕션은 S3 또는 Supabase

---

## 9. Out of Scope (v1.0)

다음 기능은 SPEC-EXPORT-001에 포함되지 않으며, 향후 버전에서 다룹니다:

- **실시간 스트리밍 내보내기** (WebSocket 기반): SPEC-EXPORT-002
- **스케줄된 자동 내보내기** (매주/매월): SPEC-EXPORT-003
- **이메일로 내보낸 파일 전송**: SPEC-NOTIFICATION-001
- **커스텀 템플릿 (Excel/PDF)**: SPEC-EXPORT-004
- **압축 파일 내보내기** (ZIP): SPEC-EXPORT-005
- **Google Drive/Dropbox 직접 업로드**: SPEC-INTEGRATION-001

---

## 10. References

- **openpyxl Documentation**: https://openpyxl.readthedocs.io/
- **reportlab User Guide**: https://www.reportlab.com/docs/reportlab-userguide.pdf
- **WeasyPrint Documentation**: https://doc.courtbouillon.org/weasyprint/
- **Django Streaming Responses**: https://docs.djangoproject.com/en/5.0/ref/request-response/#streaminghttpresponse-objects
- **Django-Q Documentation**: https://django-q.readthedocs.io/
- **html2canvas**: https://html2canvas.hertzen.com/
- **RFC 4180 (CSV)**: https://datatracker.ietf.org/doc/html/rfc4180

---

## 11. Acceptance Criteria Summary

SPEC-EXPORT-001은 다음 조건을 모두 만족할 때 완료로 간주합니다:

- ✅ **REQ-EXPORT-001 ~ REQ-EXPORT-015**: 모든 기능 요구사항 구현 및 검증
- ✅ **NFR-EXPORT-001 ~ NFR-EXPORT-008**: 모든 비기능 요구사항 충족
- ✅ **pytest 테스트 커버리지**: ≥ 85%
- ✅ **Vitest 테스트 통과**: 모든 프론트엔드 테스트 성공
- ✅ **성능 테스트**: CSV 3초, Excel 5초, PDF 10초 이내
- ✅ **대용량 데이터 테스트**: 10,000개 레코드 내보내기 성공
- ✅ **권한 테스트**: Viewer 내보내기 차단 확인
- ✅ **Railway 배포**: 프로덕션 환경에서 내보내기 정상 작동

---

_이 문서는 MoAI-ADK 표준을 따릅니다._
_작성일: 2025-11-03 by @Sam_
_@TAG: @SPEC:EXPORT-001_

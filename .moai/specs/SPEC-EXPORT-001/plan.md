# SPEC-EXPORT-001 구현 계획 (Implementation Plan)

**SPEC ID**: SPEC-EXPORT-001
**작성일**: 2025-11-03
**작성자**: @Sam
**예상 기간**: 1.5주 (7-8 작업일)

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

**점진적 구현 전략**:
- Phase 1: CSV/Excel 기본 내보내기 (동기 처리)
- Phase 2: PDF 보고서 생성
- Phase 3: 비동기 작업 큐 및 진행 상태
- Phase 4: 이력 관리 및 UI 통합

### 1.2 개발 우선순위

**우선순위 1 (Critical)**:
- CSV 내보내기 (REQ-EXPORT-001, REQ-EXPORT-002)
- Excel 기본 내보내기 (REQ-EXPORT-003)
- 권한 기반 내보내기 (REQ-EXPORT-015)

**우선순위 2 (High)**:
- Excel 다중 시트 및 스타일링 (REQ-EXPORT-004, REQ-EXPORT-005)
- PDF 기본 보고서 (REQ-EXPORT-006)
- 비동기 작업 처리 (REQ-EXPORT-009, REQ-EXPORT-010)

**우선순위 3 (Medium)**:
- PDF 차트 이미지 삽입 (REQ-EXPORT-007)
- 이력 관리 (REQ-EXPORT-012, REQ-EXPORT-013)
- 작업 취소 (REQ-EXPORT-011)

---

## 2. 개발 단계

### 2.1 Backend 구현 (Day 1-5)

#### Day 1: 환경 설정 및 CSV 내보내기

**작업 내용**:
1. 라이브러리 설치
```bash
pip install reportlab==4.2.2
pip install Pillow==10.4.0
pip install django-q==1.6.1  # 비동기 작업 큐
pip freeze > requirements.txt
```

2. ExportJob 및 ExportHistory 모델 생성
```python
# backend/dashboard/models.py

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class ExportJob(models.Model):
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
    progress = models.IntegerField(default=0)
    record_count = models.IntegerField(default=0)
    file_size = models.BigIntegerField(null=True, blank=True)
    file_path = models.CharField(max_length=500, blank=True)
    download_url = models.URLField(blank=True)
    filter_conditions = models.JSONField(default=dict)
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

class ExportHistory(models.Model):
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
    file_hash = models.CharField(max_length=32, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    download_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'export_history'
        ordering = ['-created_at']

    def is_expired(self):
        return timezone.now() > self.expires_at

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)
```

3. 마이그레이션 실행
```bash
python manage.py makemigrations
python manage.py migrate
```

4. CSV 내보내기 유틸리티 함수
```python
# backend/dashboard/utils/export.py

import csv
from io import StringIO
from django.http import HttpResponse

def export_csv(queryset, filename='export.csv'):
    """
    QuerySet을 CSV로 내보내기

    Args:
        queryset: Django QuerySet
        filename: 다운로드 파일명

    Returns:
        HttpResponse with CSV file
    """
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # UTF-8 BOM 추가 (Excel 한글 깨짐 방지)
    response.write('\ufeff')

    writer = csv.writer(response)

    # 헤더 작성
    if queryset.exists():
        first_obj = queryset.first()
        if hasattr(first_obj, 'data') and isinstance(first_obj.data, dict):
            # DataRecord의 경우 JSONField 키를 헤더로 사용
            headers = ['id'] + list(first_obj.data.keys())
        else:
            # 일반 모델의 경우 필드명 사용
            headers = [field.name for field in queryset.model._meta.fields]
        writer.writerow(headers)

    # 데이터 작성 (스트리밍)
    for obj in queryset.iterator(chunk_size=1000):
        if hasattr(obj, 'data') and isinstance(obj.data, dict):
            row = [obj.id] + [obj.data.get(key, '') for key in headers[1:]]
        else:
            row = [getattr(obj, field.name) for field in queryset.model._meta.fields]
        writer.writerow(row)

    return response

def escape_csv_value(value):
    """CSV 특수문자 이스케이프 (RFC 4180)"""
    if value is None:
        return ''

    value_str = str(value)

    # 쉼표, 따옴표, 줄바꿈이 포함된 경우 큰따옴표로 감싸기
    if ',' in value_str or '"' in value_str or '\n' in value_str:
        # 큰따옴표는 이중 큰따옴표로 이스케이프
        value_str = value_str.replace('"', '""')
        return f'"{value_str}"'

    return value_str
```

5. CSV 내보내기 API View
```python
# backend/dashboard/views.py

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Dataset, DataRecord, ExportJob
from .permissions import IsManagerOrAdmin
from .utils.export import export_csv

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsManagerOrAdmin])
def export_csv_view(request):
    """CSV 형식 내보내기"""
    dataset_id = request.data.get('dataset_id')
    filters = request.data.get('filters', {})
    columns = request.data.get('columns', [])

    try:
        dataset = Dataset.objects.get(id=dataset_id)
    except Dataset.DoesNotExist:
        return Response({'error': 'Dataset not found'}, status=status.HTTP_404_NOT_FOUND)

    # 권한 확인 (자신의 데이터셋만)
    if request.user.role != 'admin' and dataset.uploaded_by != request.user:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    # QuerySet 생성
    queryset = DataRecord.objects.filter(dataset=dataset)

    # 필터 적용 (향후 SPEC-FILTER-001과 통합)
    if filters:
        # 예시: category 필터
        if 'category' in filters:
            queryset = queryset.filter(data__category=filters['category'])

    # 레코드 수 확인
    record_count = queryset.count()

    # 소량 데이터: 즉시 반환 (< 5,000)
    if record_count < 5000:
        filename = f"{dataset.title}_{timezone.now().strftime('%Y%m%d')}.csv"
        return export_csv(queryset, filename)

    # 대량 데이터: 비동기 작업 생성 (≥ 5,000)
    job = ExportJob.objects.create(
        user=request.user,
        dataset=dataset,
        format='csv',
        record_count=record_count,
        filter_conditions=filters
    )

    # 비동기 작업 큐에 추가 (Day 5에서 구현)
    # from django_q.tasks import async_task
    # async_task('dashboard.tasks.export_large_csv', job.id)

    return Response({
        'job_id': str(job.id),
        'status': 'pending',
        'message': '내보내기 작업이 시작되었습니다. 잠시 후 완료됩니다.',
        'status_url': f'/api/export/jobs/{job.id}/'
    }, status=status.HTTP_202_ACCEPTED)
```

6. URLs 설정
```python
# backend/dashboard/urls.py

urlpatterns = [
    # ... 기존 URL 패턴
    path('export/csv/', views.export_csv_view, name='export_csv'),
]
```

**테스트**:
```python
# tests/test_export_csv.py
@pytest.mark.django_db
def test_csv_export_small_dataset(api_client):
    manager = User.objects.create_user(username='manager', password='test', role='manager')
    dataset = Dataset.objects.create(title='Test', uploaded_by=manager)

    # 100개 레코드 생성
    for i in range(100):
        DataRecord.objects.create(
            dataset=dataset,
            data={'name': f'Record {i}', 'value': i}
        )

    api_client.force_authenticate(user=manager)
    response = api_client.post('/api/export/csv/', {'dataset_id': dataset.id})

    assert response.status_code == 200
    assert response['Content-Type'] == 'text/csv; charset=utf-8-sig'
    assert 'attachment' in response['Content-Disposition']
```

---

#### Day 2: Excel 내보내기

**작업 내용**:
1. Excel 내보내기 유틸리티
```python
# backend/dashboard/utils/export.py

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from django.http import HttpResponse

def export_excel(queryset, filename='export.xlsx', options=None):
    """
    QuerySet을 Excel로 내보내기

    Args:
        queryset: Django QuerySet
        filename: 다운로드 파일명
        options: {
            'include_summary': bool,
            'include_charts': bool,
            'styling': 'simple' | 'professional'
        }

    Returns:
        HttpResponse with Excel file
    """
    options = options or {}
    styling = options.get('styling', 'professional')

    # 워크북 생성
    wb = Workbook()
    ws = wb.active
    ws.title = "데이터"

    # 헤더 작성
    if queryset.exists():
        first_obj = queryset.first()
        if hasattr(first_obj, 'data') and isinstance(first_obj.data, dict):
            headers = ['ID'] + list(first_obj.data.keys())
        else:
            headers = [field.verbose_name or field.name for field in queryset.model._meta.fields]

        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num, value=header)

            if styling == 'professional':
                # 헤더 스타일링
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
                cell.alignment = Alignment(horizontal="center", vertical="center")

    # 데이터 작성
    for row_num, obj in enumerate(queryset.iterator(chunk_size=1000), 2):
        if hasattr(obj, 'data') and isinstance(obj.data, dict):
            row_data = [obj.id] + [obj.data.get(key, '') for key in headers[1:]]
        else:
            row_data = [getattr(obj, field.name) for field in queryset.model._meta.fields]

        for col_num, value in enumerate(row_data, 1):
            cell = ws.cell(row=row_num, column=col_num, value=value)

            if styling == 'professional':
                # 교차 줄무늬 (zebra striping)
                if row_num % 2 == 0:
                    cell.fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")

    # 자동 열 너비 조정
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column].width = adjusted_width

    # 요약 통계 시트 추가 (옵션)
    if options.get('include_summary'):
        ws_summary = wb.create_sheet("요약 통계")
        # ... 요약 통계 로직

    # HttpResponse로 반환
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response
```

2. Excel 내보내기 API View
```python
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsManagerOrAdmin])
def export_excel_view(request):
    """Excel 형식 내보내기"""
    dataset_id = request.data.get('dataset_id')
    filters = request.data.get('filters', {})
    options = request.data.get('options', {})

    # ... (CSV와 유사한 로직)

    queryset = DataRecord.objects.filter(dataset=dataset)
    record_count = queryset.count()

    if record_count < 5000:
        filename = f"{dataset.title}_{timezone.now().strftime('%Y%m%d')}.xlsx"
        return export_excel(queryset, filename, options)

    # 대량 데이터: 비동기 처리
    job = ExportJob.objects.create(
        user=request.user,
        dataset=dataset,
        format='excel',
        record_count=record_count,
        filter_conditions={'filters': filters, 'options': options}
    )

    return Response({
        'job_id': str(job.id),
        'status': 'pending',
        'message': '내보내기 작업이 시작되었습니다.',
        'status_url': f'/api/export/jobs/{job.id}/'
    }, status=status.HTTP_202_ACCEPTED)
```

**테스트**:
```python
@pytest.mark.django_db
def test_excel_export_with_styling(api_client):
    manager = User.objects.create_user(username='manager', password='test', role='manager')
    dataset = Dataset.objects.create(title='Test', uploaded_by=manager)

    for i in range(100):
        DataRecord.objects.create(dataset=dataset, data={'name': f'Record {i}', 'value': i})

    api_client.force_authenticate(user=manager)
    response = api_client.post('/api/export/excel/', {
        'dataset_id': dataset.id,
        'options': {'styling': 'professional'}
    })

    assert response.status_code == 200

    # openpyxl로 파일 검증
    from openpyxl import load_workbook
    from io import BytesIO

    wb = load_workbook(BytesIO(response.content))
    ws = wb.active

    # 헤더 스타일 확인
    header_cell = ws['A1']
    assert header_cell.font.bold == True
    assert header_cell.fill.start_color.rgb == '004472C4'
```

---

#### Day 3-4: PDF 보고서 생성

**작업 내용**:
1. PDF 생성 유틸리티 (reportlab 사용)
```python
# backend/dashboard/utils/export.py

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors
from django.conf import settings
import os

def export_pdf(queryset, dataset_title, filename='export.pdf', options=None):
    """
    QuerySet을 PDF 보고서로 생성

    Args:
        queryset: Django QuerySet
        dataset_title: 데이터셋 제목
        filename: 파일명
        options: {
            'include_charts': bool,
            'chart_images': [{'type': 'bar', 'data_base64': '...'}],
            'orientation': 'portrait' | 'landscape',
            'page_size': 'A4' | 'letter'
        }
    """
    options = options or {}

    # 페이지 크기 및 방향 설정
    page_size = A4 if options.get('page_size') == 'A4' else letter

    # 파일 경로
    file_path = os.path.join(settings.MEDIA_ROOT, 'exports', filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # PDF 생성
    doc = SimpleDocTemplate(
        file_path,
        pagesize=page_size,
        topMargin=2*cm,
        bottomMargin=2*cm,
        leftMargin=2.5*cm,
        rightMargin=2.5*cm
    )

    # 스타일 정의
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=30,
        alignment=TA_CENTER
    )

    # 콘텐츠 구성
    story = []

    # 헤더 (제목 + 생성 일시)
    story.append(Paragraph(f"데이터 보고서: {dataset_title}", title_style))
    story.append(Paragraph(
        f"생성 일시: {timezone.now().strftime('%Y-%m-%d %H:%M')}",
        styles['Normal']
    ))
    story.append(Spacer(1, 1*cm))

    # 요약 통계
    story.append(Paragraph("요약 통계", styles['Heading2']))
    summary_data = [
        ['총 레코드 수', str(queryset.count())],
        ['데이터셋', dataset_title],
    ]
    summary_table = Table(summary_data, colWidths=[8*cm, 8*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ECF0F1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 1*cm))

    # 차트 삽입 (옵션)
    if options.get('include_charts') and options.get('chart_images'):
        story.append(Paragraph("데이터 시각화", styles['Heading2']))
        for chart in options['chart_images']:
            # Base64 이미지 디코딩
            import base64
            from io import BytesIO
            from PIL import Image as PILImage

            image_data = base64.b64decode(chart['data_base64'].split(',')[1])
            pil_image = PILImage.open(BytesIO(image_data))

            # 임시 파일로 저장
            temp_image_path = os.path.join(settings.MEDIA_ROOT, 'exports', 'temp_chart.png')
            pil_image.save(temp_image_path, format='PNG')

            # PDF에 삽입
            img = Image(temp_image_path, width=14*cm, height=8*cm)
            story.append(img)
            story.append(Spacer(1, 0.5*cm))

        story.append(PageBreak())

    # 데이터 테이블
    story.append(Paragraph("상세 데이터", styles['Heading2']))

    # 헤더 준비
    if queryset.exists():
        first_obj = queryset.first()
        if hasattr(first_obj, 'data') and isinstance(first_obj.data, dict):
            headers = ['ID'] + list(first_obj.data.keys())
        else:
            headers = [field.name for field in queryset.model._meta.fields]

    # 데이터 준비 (최대 100개만 표시, 나머지는 "..."로 표시)
    table_data = [headers]
    for i, obj in enumerate(queryset[:100]):
        if hasattr(obj, 'data') and isinstance(obj.data, dict):
            row = [str(obj.id)] + [str(obj.data.get(key, '')) for key in headers[1:]]
        else:
            row = [str(getattr(obj, field.name)) for field in queryset.model._meta.fields]
        table_data.append(row)

    if queryset.count() > 100:
        table_data.append(['...'] * len(headers))
        table_data.append([f'(총 {queryset.count()}개 레코드, 상위 100개만 표시)'] + [''] * (len(headers) - 1))

    # 테이블 생성
    data_table = Table(table_data, repeatRows=1)
    data_table.setStyle(TableStyle([
        # 헤더 스타일
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

        # 데이터 행 스타일
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),

        # 교차 줄무늬
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9F9F9')])
    ]))
    story.append(data_table)

    # 푸터 (페이지 번호)
    def add_page_number(canvas, doc):
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        canvas.drawRightString(page_size[0] - 2*cm, 1*cm, text)

    # PDF 빌드
    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)

    return file_path
```

2. PDF 내보내기 API View
```python
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsManagerOrAdmin])
def export_pdf_view(request):
    """PDF 보고서 생성"""
    dataset_id = request.data.get('dataset_id')
    options = request.data.get('options', {})

    # ... (권한 확인 등)

    queryset = DataRecord.objects.filter(dataset=dataset)

    # PDF는 항상 비동기 처리 (시간이 오래 걸림)
    job = ExportJob.objects.create(
        user=request.user,
        dataset=dataset,
        format='pdf',
        record_count=queryset.count(),
        filter_conditions={'options': options}
    )

    # 비동기 작업 큐에 추가
    # from django_q.tasks import async_task
    # async_task('dashboard.tasks.export_pdf_task', job.id)

    return Response({
        'job_id': str(job.id),
        'status': 'pending',
        'message': 'PDF 보고서 생성이 시작되었습니다.',
        'status_url': f'/api/export/jobs/{job.id}/'
    }, status=status.HTTP_202_ACCEPTED)
```

---

#### Day 5: 비동기 작업 큐 및 진행 상태

**작업 내용**:
1. Django-Q 설정
```python
# backend/config/settings.py

INSTALLED_APPS = [
    # ...
    'django_q',
]

Q_CLUSTER = {
    'name': 'export_queue',
    'workers': 4,
    'recycle': 500,
    'timeout': 600,  # 10분
    'compress': True,
    'save_limit': 250,
    'queue_limit': 50,
    'cpu_affinity': 1,
    'label': 'Django Q',
    'redis': {
        'host': os.environ.get('REDIS_HOST', 'localhost'),
        'port': 6379,
        'db': 0,
    }
}
```

2. 비동기 작업 태스크
```python
# backend/dashboard/tasks.py

from django.utils import timezone
from .models import ExportJob, ExportHistory, DataRecord
from .utils.export import export_csv, export_excel, export_pdf
import os
import hashlib

def export_large_csv(job_id):
    """대용량 CSV 내보내기 비동기 작업"""
    try:
        job = ExportJob.objects.get(id=job_id)
        job.status = 'processing'
        job.started_at = timezone.now()
        job.save()

        # 데이터 조회
        queryset = DataRecord.objects.filter(dataset=job.dataset)

        # 파일명 생성
        filename = f"{job.dataset.title}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path = os.path.join(settings.MEDIA_ROOT, 'exports', filename)

        # CSV 생성 (파일로 저장)
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
            import csv
            writer = csv.writer(f)

            # 헤더
            if queryset.exists():
                first_obj = queryset.first()
                headers = ['id'] + list(first_obj.data.keys())
                writer.writerow(headers)

            # 데이터 (청크 단위 처리)
            total = queryset.count()
            processed = 0

            for obj in queryset.iterator(chunk_size=1000):
                row = [obj.id] + [obj.data.get(key, '') for key in headers[1:]]
                writer.writerow(row)

                processed += 1
                if processed % 1000 == 0:
                    # 진행률 업데이트
                    job.progress = int((processed / total) * 100)
                    job.save()

        # 파일 크기 및 해시 계산
        file_size = os.path.getsize(file_path)
        file_hash = calculate_md5(file_path)

        # 작업 완료
        job.status = 'completed'
        job.progress = 100
        job.file_path = file_path
        job.file_size = file_size
        job.download_url = f'/media/exports/{filename}'
        job.completed_at = timezone.now()
        job.save()

        # 이력 저장
        ExportHistory.objects.create(
            job=job,
            user=job.user,
            dataset=job.dataset,
            format='csv',
            filename=filename,
            file_size=file_size,
            record_count=total,
            file_path=file_path,
            download_url=job.download_url,
            filter_conditions=job.filter_conditions,
            file_hash=file_hash
        )

    except Exception as e:
        job.status = 'failed'
        job.error_message = str(e)
        job.save()

def calculate_md5(file_path):
    """파일 MD5 해시 계산"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()
```

3. 작업 상태 조회 API
```python
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_export_job_status(request, job_id):
    """내보내기 작업 상태 조회"""
    try:
        job = ExportJob.objects.get(id=job_id, user=request.user)
    except ExportJob.DoesNotExist:
        return Response({'error': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)

    data = {
        'job_id': str(job.id),
        'status': job.status,
        'progress': job.progress,
        'message': get_status_message(job),
        'record_count': job.record_count,
        'file_size': job.file_size,
        'created_at': job.created_at,
        'started_at': job.started_at,
        'completed_at': job.completed_at,
        'download_url': job.download_url if job.status == 'completed' else None,
        'error_message': job.error_message if job.status == 'failed' else None
    }

    return Response(data)

def get_status_message(job):
    """작업 상태 메시지 생성"""
    if job.status == 'pending':
        return '대기 중입니다.'
    elif job.status == 'processing':
        processed = int(job.record_count * job.progress / 100)
        return f'처리 중... ({processed:,} / {job.record_count:,} 레코드)'
    elif job.status == 'completed':
        return '완료되었습니다. 다운로드할 수 있습니다.'
    elif job.status == 'failed':
        return '오류가 발생했습니다.'
    elif job.status == 'cancelled':
        return '취소되었습니다.'
```

4. 작업 취소 API
```python
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def cancel_export_job(request, job_id):
    """진행 중인 작업 취소"""
    try:
        job = ExportJob.objects.get(id=job_id, user=request.user)
    except ExportJob.DoesNotExist:
        return Response({'error': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)

    if job.status not in ['pending', 'processing']:
        return Response({'error': 'Job cannot be cancelled'}, status=status.HTTP_400_BAD_REQUEST)

    job.status = 'cancelled'
    job.save()

    # 임시 파일 삭제
    if job.file_path and os.path.exists(job.file_path):
        os.remove(job.file_path)

    return Response({'message': '작업이 취소되었습니다.'})
```

---

### 2.2 Frontend 구현 (Day 6-7)

#### Day 6: 내보내기 버튼 및 옵션 모달

**작업 내용**:
1. 라이브러리 설치
```bash
cd frontend
npm install file-saver@^2.0.5 html2canvas@^1.4.1
```

2. 내보내기 API 클라이언트
```typescript
// frontend/lib/api/export.ts

import apiClient from './client'
import { saveAs } from 'file-saver'

export interface ExportOptions {
  dataset_id: number
  filters?: Record<string, any>
  columns?: string[]
  options?: {
    include_summary?: boolean
    include_charts?: boolean
    chart_images?: Array<{type: string, data_base64: string}>
    styling?: 'simple' | 'professional'
    orientation?: 'portrait' | 'landscape'
    page_size?: 'A4' | 'letter'
  }
}

export const exportApi = {
  // CSV 내보내기
  exportCSV: async (options: ExportOptions) => {
    const response = await apiClient.post('/export/csv/', options, {
      responseType: 'blob'  // 파일 다운로드
    })

    if (response.status === 200) {
      // 즉시 다운로드
      const blob = new Blob([response.data], { type: 'text/csv' })
      const filename = getFilenameFromHeader(response) || 'export.csv'
      saveAs(blob, filename)
      return { immediate: true }
    } else if (response.status === 202) {
      // 비동기 작업
      return response.data  // { job_id, status, message, status_url }
    }
  },

  // Excel 내보내기
  exportExcel: async (options: ExportOptions) => {
    const response = await apiClient.post('/export/excel/', options, {
      responseType: 'blob'
    })

    if (response.status === 200) {
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      })
      const filename = getFilenameFromHeader(response) || 'export.xlsx'
      saveAs(blob, filename)
      return { immediate: true }
    } else if (response.status === 202) {
      return response.data
    }
  },

  // PDF 내보내기 (항상 비동기)
  exportPDF: async (options: ExportOptions) => {
    const response = await apiClient.post('/export/pdf/', options)
    return response.data  // { job_id, status, message, status_url }
  },

  // 작업 상태 조회
  getJobStatus: async (jobId: string) => {
    const response = await apiClient.get(`/export/jobs/${jobId}/`)
    return response.data
  },

  // 작업 취소
  cancelJob: async (jobId: string) => {
    const response = await apiClient.delete(`/export/jobs/${jobId}/`)
    return response.data
  },

  // 이력 조회
  getHistory: async (params?: { format?: string, page?: number, page_size?: number }) => {
    const response = await apiClient.get('/export/history/', { params })
    return response.data
  },

  // 파일 재다운로드
  downloadHistory: async (historyId: number) => {
    const response = await apiClient.get(`/export/history/${historyId}/download/`, {
      responseType: 'blob'
    })
    const blob = new Blob([response.data])
    const filename = getFilenameFromHeader(response) || 'export'
    saveAs(blob, filename)
  }
}

function getFilenameFromHeader(response: any): string | null {
  const disposition = response.headers['content-disposition']
  if (disposition) {
    const match = disposition.match(/filename="(.+)"/)
    return match ? match[1] : null
  }
  return null
}
```

3. 내보내기 버튼 컴포넌트
```typescript
// frontend/components/ExportButtons.tsx

'use client'

import { useState } from 'react'
import { FileTextIcon, FileSpreadsheetIcon, FileIcon } from 'lucide-react'
import { exportApi } from '@/lib/api/export'
import ExportOptionsModal from './ExportOptionsModal'
import ExportProgressModal from './ExportProgressModal'
import RoleGuard from './RoleGuard'

interface ExportButtonsProps {
  datasetId: number
  filters?: Record<string, any>
}

export default function ExportButtons({ datasetId, filters }: ExportButtonsProps) {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedFormat, setSelectedFormat] = useState<'csv' | 'excel' | 'pdf'>('csv')
  const [isExporting, setIsExporting] = useState(false)
  const [jobId, setJobId] = useState<string | null>(null)

  const handleExport = async (format: 'csv' | 'excel' | 'pdf', options: any) => {
    setIsExporting(true)

    try {
      const exportOptions = { dataset_id: datasetId, filters, ...options }

      let result
      if (format === 'csv') {
        result = await exportApi.exportCSV(exportOptions)
      } else if (format === 'excel') {
        result = await exportApi.exportExcel(exportOptions)
      } else {
        result = await exportApi.exportPDF(exportOptions)
      }

      if (result.immediate) {
        // 즉시 다운로드 완료
        setIsExporting(false)
        alert('파일 다운로드가 완료되었습니다.')
      } else {
        // 비동기 작업 시작
        setJobId(result.job_id)
      }
    } catch (error) {
      console.error('Export error:', error)
      alert('내보내기 중 오류가 발생했습니다.')
      setIsExporting(false)
    }
  }

  const handleCSV = () => {
    setSelectedFormat('csv')
    setIsModalOpen(true)
  }

  const handleExcel = () => {
    setSelectedFormat('excel')
    setIsModalOpen(true)
  }

  const handlePDF = () => {
    setSelectedFormat('pdf')
    setIsModalOpen(true)
  }

  return (
    <RoleGuard allowedRoles={['admin', 'manager']}>
      <div className="flex gap-2">
        <button
          onClick={handleCSV}
          className="flex items-center gap-2 px-4 py-2 bg-white border rounded-lg hover:bg-gray-50"
        >
          <FileTextIcon className="w-4 h-4" />
          CSV 내보내기
        </button>

        <button
          onClick={handleExcel}
          className="flex items-center gap-2 px-4 py-2 bg-white border rounded-lg hover:bg-gray-50"
        >
          <FileSpreadsheetIcon className="w-4 h-4" />
          Excel 내보내기
        </button>

        <button
          onClick={handlePDF}
          className="flex items-center gap-2 px-4 py-2 bg-white border rounded-lg hover:bg-gray-50"
        >
          <FileIcon className="w-4 h-4" />
          PDF 보고서
        </button>
      </div>

      {isModalOpen && (
        <ExportOptionsModal
          format={selectedFormat}
          onClose={() => setIsModalOpen(false)}
          onExport={(options) => {
            setIsModalOpen(false)
            handleExport(selectedFormat, options)
          }}
        />
      )}

      {isExporting && jobId && (
        <ExportProgressModal
          jobId={jobId}
          onClose={() => {
            setIsExporting(false)
            setJobId(null)
          }}
        />
      )}
    </RoleGuard>
  )
}
```

4. 진행 상태 모달 컴포넌트
```typescript
// frontend/components/ExportProgressModal.tsx

'use client'

import { useEffect, useState } from 'react'
import { exportApi } from '@/lib/api/export'

interface ExportProgressModalProps {
  jobId: string
  onClose: () => void
}

export default function ExportProgressModal({ jobId, onClose }: ExportProgressModalProps) {
  const [status, setStatus] = useState<any>(null)
  const [polling, setPolling] = useState(true)

  useEffect(() => {
    if (!polling) return

    const interval = setInterval(async () => {
      try {
        const data = await exportApi.getJobStatus(jobId)
        setStatus(data)

        if (data.status === 'completed') {
          setPolling(false)
          // 파일 다운로드
          window.location.href = data.download_url
          setTimeout(() => onClose(), 2000)
        } else if (data.status === 'failed') {
          setPolling(false)
          alert(`내보내기 실패: ${data.error_message}`)
          onClose()
        }
      } catch (error) {
        console.error('Failed to fetch job status:', error)
      }
    }, 2000)  // 2초마다 폴링

    return () => clearInterval(interval)
  }, [jobId, polling, onClose])

  const handleCancel = async () => {
    if (confirm('작업을 취소하시겠습니까?')) {
      await exportApi.cancelJob(jobId)
      onClose()
    }
  }

  if (!status) return <div>Loading...</div>

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full">
        <h2 className="text-xl font-bold mb-4">
          {status.status === 'processing' ? '내보내기 중...' : '내보내기 완료'}
        </h2>

        {/* Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-4 mb-4">
          <div
            className="bg-blue-600 h-4 rounded-full transition-all duration-300"
            style={{ width: `${status.progress}%` }}
          />
        </div>

        <p className="text-gray-700 mb-2">{status.message}</p>
        <p className="text-sm text-gray-500">진행률: {status.progress}%</p>

        {status.status === 'processing' && (
          <div className="mt-4 flex justify-end gap-2">
            <button
              onClick={handleCancel}
              className="px-4 py-2 border rounded-lg hover:bg-gray-50"
            >
              취소
            </button>
          </div>
        )}

        {status.status === 'completed' && (
          <div className="mt-4">
            <p className="text-green-600 font-semibold">
              파일 다운로드가 곧 시작됩니다...
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
```

---

#### Day 7: 이력 관리 페이지

**작업 내용**:
1. 이력 페이지
```typescript
// frontend/app/export-history/page.tsx

'use client'

import { useState, useEffect } from 'react'
import { exportApi } from '@/lib/api/export'
import { DownloadIcon, TrashIcon } from 'lucide-react'

export default function ExportHistoryPage() {
  const [history, setHistory] = useState<any[]>([])
  const [filter, setFilter] = useState<'all' | 'csv' | 'excel' | 'pdf'>('all')
  const [page, setPage] = useState(1)
  const [totalCount, setTotalCount] = useState(0)

  useEffect(() => {
    loadHistory()
  }, [filter, page])

  const loadHistory = async () => {
    const params = filter !== 'all' ? { format: filter, page } : { page }
    const data = await exportApi.getHistory(params)
    setHistory(data.results)
    setTotalCount(data.count)
  }

  const handleDownload = async (historyId: number) => {
    try {
      await exportApi.downloadHistory(historyId)
    } catch (error: any) {
      if (error.response?.status === 404) {
        alert('파일이 만료되었습니다.')
      }
    }
  }

  const handleDelete = async (historyId: number) => {
    if (confirm('이력을 삭제하시겠습니까?')) {
      await exportApi.deleteHistory(historyId)
      loadHistory()
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">내보내기 이력</h1>

      {/* 필터 */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setFilter('all')}
          className={`px-4 py-2 rounded-lg ${filter === 'all' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
        >
          전체
        </button>
        <button
          onClick={() => setFilter('csv')}
          className={`px-4 py-2 rounded-lg ${filter === 'csv' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
        >
          CSV
        </button>
        <button
          onClick={() => setFilter('excel')}
          className={`px-4 py-2 rounded-lg ${filter === 'excel' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
        >
          Excel
        </button>
        <button
          onClick={() => setFilter('pdf')}
          className={`px-4 py-2 rounded-lg ${filter === 'pdf' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
        >
          PDF
        </button>
      </div>

      {/* 테이블 */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                파일명
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                형식
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                크기
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                레코드 수
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                생성일
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                만료일
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                액션
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {history.map((item) => (
              <tr key={item.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {item.filename}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {item.format.toUpperCase()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {formatFileSize(item.file_size)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {item.record_count.toLocaleString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {new Date(item.created_at).toLocaleDateString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {item.is_expired ? (
                    <span className="text-red-600">만료됨</span>
                  ) : (
                    new Date(item.expires_at).toLocaleDateString()
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium flex gap-2">
                  {!item.is_expired && (
                    <button
                      onClick={() => handleDownload(item.id)}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      <DownloadIcon className="w-5 h-5" />
                    </button>
                  )}
                  <button
                    onClick={() => handleDelete(item.id)}
                    className="text-red-600 hover:text-red-900"
                  >
                    <TrashIcon className="w-5 h-5" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 페이지네이션 */}
      <div className="mt-6 flex justify-center gap-2">
        <button
          onClick={() => setPage(p => Math.max(1, p - 1))}
          disabled={page === 1}
          className="px-4 py-2 border rounded-lg disabled:opacity-50"
        >
          이전
        </button>
        <span className="px-4 py-2">
          {page} / {Math.ceil(totalCount / 20)}
        </span>
        <button
          onClick={() => setPage(p => p + 1)}
          disabled={page >= Math.ceil(totalCount / 20)}
          className="px-4 py-2 border rounded-lg disabled:opacity-50"
        >
          다음
        </button>
      </div>
    </div>
  )
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
```

---

### 2.3 통합 테스트 및 배포 (Day 8)

**작업 내용**:
- E2E 테스트 시나리오 실행
- CSV/Excel/PDF 전체 플로우 검증
- 비동기 작업 진행 상태 확인
- 권한 기반 접근 제어 테스트
- Railway 배포 및 프로덕션 테스트

---

## 3. 기술 스택 상세

### 3.1 Backend

| 라이브러리 | 버전 | 용도 |
|-----------|------|------|
| reportlab | 4.2.2 | PDF 생성 |
| Pillow | 10.4.0 | 이미지 처리 |
| openpyxl | 3.1.5 | Excel 읽기/쓰기 (이미 설치됨) |
| django-q | 1.6.1 | 비동기 작업 큐 |

### 3.2 Frontend

| 라이브러리 | 버전 | 용도 |
|-----------|------|------|
| file-saver | 2.0.5 | 파일 다운로드 헬퍼 |
| html2canvas | 1.4.1 | 차트 → 이미지 변환 |

---

## 4. 디렉토리 구조

```
backend/
├── dashboard/
│   ├── models.py (ExportJob, ExportHistory 추가)
│   ├── serializers.py (Export 관련 serializers)
│   ├── views.py (export_csv, export_excel, export_pdf views)
│   ├── tasks.py (비동기 작업 태스크)
│   ├── utils/
│   │   └── export.py (CSV/Excel/PDF 생성 유틸리티)
│   └── urls.py
├── config/
│   ├── settings.py (MEDIA_ROOT, Q_CLUSTER 설정)
│   └── urls.py
└── tests/
    ├── test_export_csv.py
    ├── test_export_excel.py
    └── test_export_pdf.py

frontend/
├── app/
│   ├── export-history/
│   │   └── page.tsx
│   └── data/
│       └── page.tsx (ExportButtons 추가)
├── lib/
│   └── api/
│       └── export.ts
└── components/
    ├── ExportButtons.tsx
    ├── ExportOptionsModal.tsx
    ├── ExportProgressModal.tsx
    └── RoleGuard.tsx
```

---

## 5. 테스트 계획

### 5.1 Backend 테스트 (pytest)

**테스트 커버리지 목표**: ≥ 85%

**주요 테스트 케이스**: spec.md의 Section 7.1 참조

---

## 6. 배포 전략

### 6.1 Railway 배포 설정

1. 환경 변수 추가
```bash
REDIS_HOST=redis.railway.internal
REDIS_PORT=6379
```

2. Django-Q worker 시작
```bash
# Procfile
release: python manage.py migrate
web: gunicorn config.wsgi
worker: python manage.py qcluster
```

---

## 7. 리스크 및 대응 방안

| 리스크 | 영향도 | 대응 방안 |
|-------|--------|----------|
| 대용량 데이터 메모리 부족 | 중간 | 스트리밍 출력, 청크 단위 처리 |
| PDF 생성 시간 과다 | 중간 | 비동기 작업 큐, 진행률 표시 |
| Railway 임시 파일 손실 | 낮음 | S3 또는 Supabase Storage 옵션 제공 |

---

## 8. 타임라인

| 기간 | 작업 내용 | 담당 | 상태 |
|------|----------|------|------|
| Day 1 | Backend 환경 설정, CSV 내보내기 | Backend | Pending |
| Day 2 | Excel 내보내기 | Backend | Pending |
| Day 3-4 | PDF 보고서 생성 | Backend | Pending |
| Day 5 | 비동기 작업 큐 및 진행 상태 | Backend | Pending |
| Day 6 | Frontend 내보내기 버튼 및 모달 | Frontend | Pending |
| Day 7 | Frontend 이력 관리 페이지 | Frontend | Pending |
| Day 8 | 통합 테스트 및 배포 | Full-stack | Pending |

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
_@TAG: @PLAN:EXPORT-001_

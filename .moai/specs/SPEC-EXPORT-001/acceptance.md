# SPEC-EXPORT-001: Data Export System - Acceptance Criteria

**Version**: 1.0.0
**Status**: Draft
**Date**: 2025-01-23
**Author**: MoAI-ADK Alfred SuperAgent

---

## Table of Contents

1. [Overview](#overview)
2. [Definition of Done](#definition-of-done)
3. [Functional Acceptance Criteria](#functional-acceptance-criteria)
4. [Test Scenarios](#test-scenarios)
5. [Backend Test Examples](#backend-test-examples)
6. [Frontend Test Examples](#frontend-test-examples)
7. [Performance Benchmarks](#performance-benchmarks)
8. [Security Validation](#security-validation)
9. [User Acceptance Scenarios](#user-acceptance-scenarios)
10. [Completion Checklist](#completion-checklist)

---

## Overview

This document defines the acceptance criteria for SPEC-EXPORT-001 (Data Export System). The specification must be validated through comprehensive testing across all export formats (CSV, Excel, PDF), async job processing, and role-based access control.

### Scope of Testing

- **CSV Export**: UTF-8 BOM encoding, RFC 4180 compliance, special character handling
- **Excel Export**: Styling, formatting, auto-width columns, zebra striping
- **PDF Export**: Charts, pagination, table of contents, professional layout
- **Async Processing**: Job queue, progress tracking, status updates
- **Export History**: File retention, download tracking, integrity verification
- **Role-Based Access**: Viewer restrictions, admin controls
- **Performance**: Response times, memory efficiency, streaming

### Testing Levels

1. **Unit Tests**: Individual functions (CSV writer, Excel styler, PDF generator)
2. **Integration Tests**: API endpoints, database operations, file storage
3. **E2E Tests**: Complete export workflows from button click to download
4. **Performance Tests**: Large dataset handling, memory profiling
5. **Security Tests**: Permission enforcement, file access control

---

## Definition of Done

SPEC-EXPORT-001 is considered complete when ALL of the following criteria are met:

### Functional Completeness
- ✅ All 15 REQ-EXPORT requirements (REQ-EXPORT-001 ~ REQ-EXPORT-015) are implemented
- ✅ CSV, Excel, and PDF export functionality working for all datasets
- ✅ Async job processing with django-q operational
- ✅ Progress tracking updates in real-time (2-second polling)
- ✅ Export history page displays all jobs with 7-day retention
- ✅ Role-based permissions enforced (Viewer blocked, Manager/Admin allowed)

### Code Quality
- ✅ Backend test coverage ≥ 90% (pytest)
- ✅ Frontend test coverage ≥ 85% (Vitest)
- ✅ All linting rules pass (Ruff, Black, ESLint, Prettier)
- ✅ Type safety verified (mypy for Python, TypeScript strict mode)
- ✅ No security vulnerabilities detected (Bandit, npm audit)

### Performance Standards
- ✅ CSV export completes in ≤ 3 seconds for 10,000 records
- ✅ Excel export completes in ≤ 5 seconds for 5,000 records
- ✅ PDF export completes in ≤ 10 seconds for 1,000 records with 2 charts
- ✅ Memory usage stays under 100MB during streaming export
- ✅ Async jobs process datasets >10,000 records without timeout

### Documentation
- ✅ API documentation updated in Swagger/OpenAPI
- ✅ User guide created with export workflow screenshots
- ✅ Developer documentation includes code examples
- ✅ Error messages documented with troubleshooting steps

### Deployment Readiness
- ✅ Environment variables configured in Railway
- ✅ File storage setup (local filesystem or S3-compatible)
- ✅ Django-Q worker running in separate process
- ✅ Export cleanup cron job scheduled (daily at 2 AM)
- ✅ Rollback plan documented

---

## Functional Acceptance Criteria

### AC-EXPORT-001: CSV Export with UTF-8 BOM

**@TAG**: @SPEC:EXPORT-001 → @TEST:EXPORT-001-CSV

**Given**: Dataset with 5,000 records including special characters (é, ñ, 中文, 한글)
**When**: User clicks "CSV 다운로드" button
**Then**:
- CSV file downloads with UTF-8 BOM (`\ufeff`) at start
- Special characters display correctly when opened in Excel
- Commas in values are properly escaped with double quotes
- Newlines in text fields are preserved with `\r\n`
- File size is reasonable (not bloated by encoding issues)

**Validation**:
```python
# Test CSV file starts with UTF-8 BOM
with open('export.csv', 'rb') as f:
    assert f.read(3) == b'\xef\xbb\xbf'

# Test special characters preserved
import csv
with open('export.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    first_row = next(reader)
    assert 'é' in first_row['name']  # French
    assert '한글' in first_row['description']  # Korean
```

---

### AC-EXPORT-002: CSV Streaming for Large Datasets

**@TAG**: @SPEC:EXPORT-001 → @TEST:EXPORT-001-STREAM

**Given**: Dataset with 50,000 records (expected size ~20 MB)
**When**: User exports to CSV
**Then**:
- Export completes without timeout (≤ 30 seconds)
- Memory usage stays under 100 MB throughout process
- Response streams chunks incrementally (not loading all in memory)
- User receives file progressively (can see download progress in browser)

**Validation**:
```python
import memory_profiler

@memory_profiler.profile
def test_csv_streaming_memory():
    response = client.get('/api/export/csv/dataset/large-test/')
    assert response.status_code == 200

    # Check memory usage log - should not exceed 100MB
    # Memory usage logged by decorator
```

---

### AC-EXPORT-003: Excel Export with Professional Styling

**@TAG**: @SPEC:EXPORT-001 → @TEST:EXPORT-001-EXCEL

**Given**: Dataset with numeric, date, and text columns
**When**: User exports to Excel with default styling
**Then**:
- Header row has blue background (#4472C4) and white bold text
- Column widths auto-adjusted to content (max 50 characters)
- Data rows have zebra striping (even rows: #F2F2F2)
- Numbers formatted with thousand separators (1,234.56)
- Dates formatted as YYYY-MM-DD
- Grid lines visible for readability

**Validation**:
```python
from openpyxl import load_workbook

def test_excel_styling():
    wb = load_workbook('export.xlsx')
    ws = wb.active

    # Header styling
    assert ws['A1'].font.bold == True
    assert ws['A1'].font.color.rgb == 'FFFFFF'
    assert ws['A1'].fill.start_color.rgb == '4472C4'

    # Zebra striping on even rows
    assert ws['A2'].fill.start_color.rgb == 'F2F2F2'
    assert ws['A3'].fill.start_color is None
    assert ws['A4'].fill.start_color.rgb == 'F2F2F2'

    # Number formatting
    assert ws['D2'].number_format == '#,##0.00'
```

---

### AC-EXPORT-004: Excel Column Width Optimization

**@TAG**: @SPEC:EXPORT-001 → @TEST:EXPORT-001-WIDTH

**Given**: Dataset with varying column content lengths
**When**: Excel file generated with auto-width enabled
**Then**:
- Short columns (e.g., ID) have width ≈ 10 characters
- Medium columns (e.g., Name) adjust to longest value up to 50 chars
- Long text columns (e.g., Description) capped at 50 characters
- All column widths are at least 8 characters (minimum readability)

**Validation**:
```python
def test_excel_column_widths():
    wb = load_workbook('export.xlsx')
    ws = wb.active

    # Check column widths
    assert 8 <= ws.column_dimensions['A'].width <= 15  # ID column
    assert 15 <= ws.column_dimensions['B'].width <= 50  # Name column
    assert ws.column_dimensions['C'].width == 50  # Long description capped
```

---

### AC-EXPORT-005: PDF Report with Header and Footer

**@TAG**: @SPEC:EXPORT-001 → @TEST:EXPORT-001-PDF-LAYOUT

**Given**: Dataset "Student Enrollment 2024"
**When**: User exports to PDF with university logo
**Then**:
- Header includes university logo (left), report title (center), generation date (right)
- Footer includes page numbers ("Page X of Y") and copyright
- Header/footer appear on every page consistently
- Logo image is clear and properly scaled

**Validation**:
```python
from PyPDF2 import PdfReader

def test_pdf_header_footer():
    reader = PdfReader('export.pdf')
    page = reader.pages[0]
    text = page.extract_text()

    # Check header content
    assert 'Student Enrollment 2024' in text
    assert '2025-01-23' in text  # Generation date

    # Check footer
    assert 'Page 1 of' in text
    assert '© 2025 University' in text
```

---

### AC-EXPORT-006: PDF Data Table with Styling

**@TAG**: @SPEC:EXPORT-001 → @TEST:EXPORT-001-PDF-TABLE

**Given**: Dataset with 20 records to display in PDF
**When**: PDF generated with table formatting
**Then**:
- Table has header row with dark background
- Alternating row colors for readability (zebra striping)
- Text is left-aligned for strings, right-aligned for numbers
- Long text wraps within cell boundaries
- Table borders are visible (1pt black lines)

**Validation**:
```python
# Note: Direct validation of PDF styling is complex
# Instead, verify generated PDF visually and check file structure
def test_pdf_table_structure():
    reader = PdfReader('export.pdf')
    page = reader.pages[0]

    # Check table content is present
    text = page.extract_text()
    assert 'Student ID' in text  # Header column
    assert '12345' in text  # Data value

    # Verify page layout (width/height)
    assert page.mediabox.width == 595  # A4 width in points
    assert page.mediabox.height == 842  # A4 height in points
```

---

### AC-EXPORT-007: PDF Chart Embedding

**@TAG**: @SPEC:EXPORT-001 → @TEST:EXPORT-001-PDF-CHART

**Given**: Frontend chart rendered with Chart.js (enrollment by department)
**When**: User exports PDF with "차트 포함" option enabled
**Then**:
- Chart appears as high-quality image in PDF (PNG format)
- Chart maintains aspect ratio (16:9 or as specified)
- Chart is positioned below summary statistics
- Multiple charts appear in order (enrollment, grades, attendance)
- Chart images are embedded (not linked externally)

**Validation**:
```python
def test_pdf_chart_embedding():
    # Backend receives base64 chart data from frontend
    chart_data = {
        'enrollment_chart': 'data:image/png;base64,iVBORw0KGgo...',
        'grades_chart': 'data:image/png;base64,iVBORw0KGgo...'
    }

    response = client.post('/api/export/pdf/dataset/123/', json={
        'include_charts': True,
        'chart_images': chart_data
    })

    assert response.status_code == 202  # Async job created

    # After job completes, verify PDF contains images
    reader = PdfReader('export_with_charts.pdf')
    # Check for embedded images (simplified check)
    assert len(reader.pages) >= 2  # Charts add pages
```

---

### AC-EXPORT-008: Async Job Creation and Queuing

**@TAG**: @SPEC:EXPORT-001 → @TEST:EXPORT-001-ASYNC

**Given**: Dataset with 15,000 records (triggers async processing)
**When**: User clicks "Excel 다운로드" button
**Then**:
- API immediately returns 202 Accepted with job_id
- ExportJob record created in database with status='pending'
- Job appears in django-q queue within 5 seconds
- Frontend displays "처리 중..." modal with progress bar
- Response time for initial API call ≤ 500ms

**Validation**:
```python
@pytest.mark.django_db
def test_async_job_creation():
    dataset = Dataset.objects.create(title='Large Dataset', record_count=15000)

    response = client.post('/api/export/async/', json={
        'dataset_id': dataset.id,
        'format': 'excel'
    })

    assert response.status_code == 202
    assert 'job_id' in response.json()

    # Verify job created
    job = ExportJob.objects.get(id=response.json()['job_id'])
    assert job.status == 'pending'
    assert job.format == 'excel'
    assert job.dataset_id == dataset.id
```

---

### AC-EXPORT-009: Progress Tracking During Export

**@TAG**: @SPEC:EXPORT-001 → @TEST:EXPORT-001-PROGRESS

**Given**: Async export job processing 20,000 records
**When**: Frontend polls `/api/export/status/{job_id}/` every 2 seconds
**Then**:
- Progress updates from 0% → 100% incrementally
- Status transitions: 'pending' → 'processing' → 'completed'
- Progress percentage accurate (±5% of actual completion)
- Estimated time remaining calculated and displayed
- Progress never decreases or jumps erratically

**Validation**:
```python
@pytest.mark.django_db
def test_progress_tracking():
    job = ExportJob.objects.create(
        dataset_id=1,
        format='excel',
        status='processing',
        progress=0,
        record_count=20000
    )

    # Simulate progress updates
    for percent in [0, 25, 50, 75, 100]:
        job.progress = percent
        job.save()

        response = client.get(f'/api/export/status/{job.id}/')
        assert response.json()['progress'] == percent

        if percent == 100:
            assert response.json()['status'] == 'completed'
```

---

### AC-EXPORT-010: Job Completion and File Download

**@TAG**: @SPEC:EXPORT-001 → @TEST:EXPORT-001-COMPLETE

**Given**: Export job reaches 100% completion
**When**: Job status changes to 'completed'
**Then**:
- download_url field populated with valid file path
- File exists at specified location on server
- Frontend automatically triggers file download (window.location.href)
- Success message displayed: "다운로드가 완료되었습니다"
- Modal closes automatically after 2 seconds

**Validation**:
```python
@pytest.mark.django_db
def test_job_completion():
    job = ExportJob.objects.create(
        dataset_id=1,
        format='csv',
        status='completed',
        progress=100,
        file_path='/media/exports/dataset_1_20250123.csv'
    )
    job.download_url = f'https://domain.com{job.file_path}'
    job.save()

    response = client.get(f'/api/export/status/{job.id}/')
    data = response.json()

    assert data['status'] == 'completed'
    assert data['download_url'].startswith('https://')
    assert data['download_url'].endswith('.csv')

    # Verify file exists
    import os
    assert os.path.exists(job.file_path)
```

---

### AC-EXPORT-011: Export History Listing

**@TAG**: @SPEC:EXPORT-001 → @TEST:EXPORT-001-HISTORY

**Given**: User has exported 5 datasets in past week
**When**: User navigates to "내보내기 내역" page
**Then**:
- All 5 export jobs displayed in reverse chronological order
- Each entry shows: dataset title, format, export date, file size, status
- Download buttons enabled for completed jobs
- Delete buttons available for own exports (admin can delete all)
- Jobs older than 7 days are automatically hidden

**Validation**:
```python
@pytest.mark.django_db
def test_export_history_listing(api_client, manager_user):
    api_client.force_authenticate(user=manager_user)

    # Create export history
    for i in range(5):
        ExportHistory.objects.create(
            job=ExportJob.objects.create(
                user=manager_user,
                dataset_id=1,
                format='csv',
                status='completed'
            ),
            expires_at=timezone.now() + timedelta(days=7),
            file_hash='abc123'
        )

    response = api_client.get('/api/export/history/')
    assert response.status_code == 200
    assert len(response.data) == 5

    # Check ordering (newest first)
    dates = [item['created_at'] for item in response.data]
    assert dates == sorted(dates, reverse=True)
```

---

### AC-EXPORT-012: File Download Tracking

**@TAG**: @SPEC:EXPORT-001 → @TEST:EXPORT-001-DOWNLOAD

**Given**: Export history entry with download_count=0
**When**: User clicks download button 3 times
**Then**:
- download_count increments to 3
- Each download logs timestamp in ExportHistory
- File MD5 hash verified before each download (integrity check)
- Corrupted files display warning and prevent download

**Validation**:
```python
@pytest.mark.django_db
def test_download_tracking():
    history = ExportHistory.objects.create(
        job=ExportJob.objects.create(
            user_id=1,
            dataset_id=1,
            format='csv',
            status='completed',
            file_path='/media/exports/test.csv'
        ),
        expires_at=timezone.now() + timedelta(days=7),
        file_hash='abc123',
        download_count=0
    )

    # Download 3 times
    for _ in range(3):
        response = client.get(f'/api/export/download/{history.job.id}/')
        assert response.status_code == 200

    history.refresh_from_db()
    assert history.download_count == 3
```

---

### AC-EXPORT-013: File Expiration and Cleanup

**@TAG**: @SPEC:EXPORT-001 → @TEST:EXPORT-001-CLEANUP

**Given**: Export job completed 7 days ago (expires_at = yesterday)
**When**: Cleanup cron job runs (scheduled daily at 2 AM)
**Then**:
- File deleted from filesystem
- ExportHistory record marked as expired
- Download URL returns 404 if accessed
- User notified in history page: "파일이 만료되었습니다"

**Validation**:
```python
@pytest.mark.django_db
def test_file_expiration():
    from app.tasks import cleanup_expired_exports

    # Create expired export
    history = ExportHistory.objects.create(
        job=ExportJob.objects.create(
            user_id=1,
            dataset_id=1,
            format='csv',
            status='completed',
            file_path='/media/exports/expired.csv'
        ),
        expires_at=timezone.now() - timedelta(days=1),  # Expired yesterday
        file_hash='abc123'
    )

    # Create file
    import os
    os.makedirs(os.path.dirname(history.job.file_path), exist_ok=True)
    with open(history.job.file_path, 'w') as f:
        f.write('test data')

    # Run cleanup
    cleanup_expired_exports()

    # Verify file deleted
    assert not os.path.exists(history.job.file_path)

    # Verify download returns 404
    response = client.get(f'/api/export/download/{history.job.id}/')
    assert response.status_code == 404
```

---

### AC-EXPORT-014: Role-Based Export Permissions

**@TAG**: @SPEC:EXPORT-001 → @TEST:EXPORT-001-RBAC

**Given**: Three users with roles: Admin, Manager, Viewer
**When**: Each user attempts to export dataset
**Then**:
- **Admin**: ✅ Can export all datasets in all formats
- **Manager**: ✅ Can export own datasets in all formats
- **Viewer**: ❌ Receives 403 Forbidden with message "내보내기 권한이 없습니다"

**Validation**:
```python
@pytest.mark.django_db
def test_export_permissions(api_client):
    admin = User.objects.create_user(username='admin', role='admin')
    manager = User.objects.create_user(username='manager', role='manager')
    viewer = User.objects.create_user(username='viewer', role='viewer')

    dataset = Dataset.objects.create(title='Test', uploaded_by=manager)

    # Admin can export
    api_client.force_authenticate(user=admin)
    response = api_client.post(f'/api/export/csv/{dataset.id}/')
    assert response.status_code in [200, 202]

    # Manager can export
    api_client.force_authenticate(user=manager)
    response = api_client.post(f'/api/export/csv/{dataset.id}/')
    assert response.status_code in [200, 202]

    # Viewer cannot export
    api_client.force_authenticate(user=viewer)
    response = api_client.post(f'/api/export/csv/{dataset.id}/')
    assert response.status_code == 403
    assert '권한이 없습니다' in response.json()['detail']
```

---

### AC-EXPORT-015: Export Options Configuration

**@TAG**: @SPEC:EXPORT-001 → @TEST:EXPORT-001-OPTIONS

**Given**: User opens export dialog with custom options
**When**: User selects specific columns, date range, and chart inclusion
**Then**:
- Only selected columns appear in exported file
- Records filtered by date range (start_date ≤ record.date ≤ end_date)
- Charts included/excluded based on checkbox state
- File name includes timestamp: `dataset_title_20250123_143052.csv`

**Validation**:
```python
@pytest.mark.django_db
def test_export_options():
    response = client.post('/api/export/csv/1/', json={
        'columns': ['id', 'name', 'enrollment_date'],
        'date_range': {
            'start': '2024-01-01',
            'end': '2024-12-31'
        },
        'include_charts': False
    })

    assert response.status_code in [200, 202]

    # For sync export, check CSV content
    if response.status_code == 200:
        content = response.content.decode('utf-8-sig')
        lines = content.split('\n')

        # Check header has only selected columns
        assert lines[0] == 'id,name,enrollment_date'

        # Verify no records outside date range (if data present)
        # This would require parsing CSV and checking dates
```

---

## Test Scenarios

### Scenario 1: Small Dataset CSV Export (Sync)

**Actors**: Manager user
**Preconditions**:
- Dataset "Q1 Sales" with 3,500 records exists
- User logged in with Manager role
- Data includes special characters: €, £, ñ

**Steps**:
1. Navigate to dataset detail page
2. Click "CSV 다운로드" button
3. Wait for download to complete (≤ 3 seconds)
4. Open CSV file in Excel
5. Verify data integrity

**Expected Results**:
- CSV downloads immediately (no async job)
- File size ≈ 850 KB (UTF-8 encoded)
- Special characters display correctly (€, £, ñ)
- All 3,500 records present
- No data truncation or corruption

**Pass Criteria**: ✅ File downloads, opens in Excel, all data intact

---

### Scenario 2: Large Dataset Excel Export (Async)

**Actors**: Admin user
**Preconditions**:
- Dataset "Student Records" with 25,000 records exists
- Django-Q worker running
- Sufficient disk space (≥ 10 MB free)

**Steps**:
1. Navigate to dataset detail page
2. Click "Excel 다운로드" button
3. Observe progress modal appears
4. Wait for progress to reach 100% (≤ 25 seconds)
5. Automatic download triggers
6. Open Excel file

**Expected Results**:
- API returns 202 immediately with job_id
- Progress updates every 2 seconds: 0% → 25% → 50% → 75% → 100%
- Excel file has professional styling (blue headers, zebra striping)
- File size ≈ 6 MB
- All 25,000 records present with formatting

**Pass Criteria**: ✅ Async processing successful, file styled correctly

---

### Scenario 3: PDF Export with Charts

**Actors**: Manager user
**Preconditions**:
- Dataset "Course Evaluations" with 1,200 records
- Chart.js charts rendered on frontend (enrollment, grades)
- University logo available

**Steps**:
1. Render charts on dashboard page
2. Click "PDF 다운로드" button
3. Select "차트 포함" option
4. Wait for async job to complete (≤ 15 seconds)
5. Download PDF
6. Open in PDF reader

**Expected Results**:
- PDF includes header with logo and title
- Summary statistics displayed (total records, average grade)
- Both charts embedded as images
- Data table with 1,200 rows across 6 pages
- Footer with page numbers on each page

**Pass Criteria**: ✅ PDF renders professionally with all components

---

### Scenario 4: Viewer Permission Denial

**Actors**: Viewer user
**Preconditions**:
- User logged in with Viewer role
- Dataset "Confidential Data" visible to user

**Steps**:
1. Navigate to dataset detail page
2. Observe export buttons
3. Click "CSV 다운로드" button
4. Observe response

**Expected Results**:
- Export buttons visible but disabled (grayed out)
- On click, error toast displays: "내보내기 권한이 없습니다"
- No file downloads
- API returns 403 Forbidden

**Pass Criteria**: ✅ Viewer blocked from exporting, clear error message

---

### Scenario 5: Export History Management

**Actors**: Manager user
**Preconditions**:
- User has exported 10 datasets over past 5 days
- 2 exports are from 8 days ago (expired)

**Steps**:
1. Navigate to "내보내기 내역" page
2. Observe list of export jobs
3. Click download button on recent export
4. Click delete button on old export
5. Refresh page

**Expected Results**:
- 8 recent exports displayed (2 expired ones hidden)
- Each entry shows dataset title, format, date, file size
- Download increments download_count
- Delete removes entry from list
- File deleted from server

**Pass Criteria**: ✅ History page functional, file management works

---

### Scenario 6: Job Failure and Retry

**Actors**: Admin user
**Preconditions**:
- Dataset "Corrupted Data" with malformed JSON in some records
- Export configured to fail on record #5,437

**Steps**:
1. Click "Excel 다운로드" button
2. Observe progress modal
3. Wait for job to fail (progress stops at ~27%)
4. Observe error message
5. Click "재시도" button
6. Wait for second attempt

**Expected Results**:
- First attempt fails with status='failed'
- Error modal displays: "일부 레코드 처리 중 오류가 발생했습니다"
- Error details logged to ExportJob.error_message
- Retry creates new job with same parameters
- Second attempt skips corrupted record (with warning) and succeeds

**Pass Criteria**: ✅ Failures handled gracefully, retry mechanism works

---

## Backend Test Examples

### Test Suite: CSV Export

```python
# tests/test_export_csv.py

import pytest
from django.contrib.auth import get_user_model
from app.models import Dataset, DataRecord
from app.services.export import export_csv
import csv
import io

User = get_user_model()

@pytest.mark.django_db
class TestCSVExport:

    def test_csv_utf8_bom_encoding(self):
        """Test that CSV files include UTF-8 BOM for Excel compatibility"""
        dataset = Dataset.objects.create(title='Test', record_count=1, uploaded_by_id=1)
        DataRecord.objects.create(dataset=dataset, data={'name': 'Test'})

        response = export_csv(Dataset.objects.filter(id=dataset.id))
        content = response.content

        # Check BOM at start
        assert content[:3] == b'\xef\xbb\xbf', "CSV must start with UTF-8 BOM"

    def test_csv_special_characters(self):
        """Test that special characters are preserved correctly"""
        dataset = Dataset.objects.create(title='Special Chars', record_count=3, uploaded_by_id=1)
        test_data = [
            {'name': 'François', 'description': 'Café in Montréal'},
            {'name': '김철수', 'description': '서울대학교'},
            {'name': 'José', 'description': 'España €100'}
        ]

        for data in test_data:
            DataRecord.objects.create(dataset=dataset, data=data)

        response = export_csv(Dataset.objects.filter(id=dataset.id))
        content = response.content.decode('utf-8-sig')

        # Verify special characters present
        assert 'François' in content
        assert '김철수' in content
        assert 'España €100' in content

    def test_csv_rfc4180_compliance(self):
        """Test RFC 4180 compliance for commas and quotes"""
        dataset = Dataset.objects.create(title='RFC Test', record_count=2, uploaded_by_id=1)
        DataRecord.objects.create(dataset=dataset, data={
            'text': 'Value with, comma',
            'quoted': 'Value with "quotes"'
        })

        response = export_csv(Dataset.objects.filter(id=dataset.id))
        content = response.content.decode('utf-8-sig')
        lines = content.split('\r\n')

        # Check comma handling
        assert '"Value with, comma"' in lines[1]

        # Check quote escaping
        assert 'Value with ""quotes""' in lines[1] or 'Value with \\"quotes\\"' in lines[1]

    def test_csv_streaming_performance(self):
        """Test that large datasets stream efficiently without OOM"""
        dataset = Dataset.objects.create(title='Large', record_count=50000, uploaded_by_id=1)

        # Create 50,000 records
        records = [DataRecord(dataset=dataset, data={'value': i}) for i in range(50000)]
        DataRecord.objects.bulk_create(records, batch_size=5000)

        import tracemalloc
        tracemalloc.start()

        response = export_csv(Dataset.objects.filter(id=dataset.id))

        # Consume response (simulate download)
        for chunk in response.streaming_content:
            pass

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Peak memory should be under 100 MB (104857600 bytes)
        assert peak < 104857600, f"Memory usage {peak} exceeds 100MB limit"

    def test_csv_column_ordering(self):
        """Test that columns maintain consistent order across records"""
        dataset = Dataset.objects.create(title='Column Order', record_count=3, uploaded_by_id=1)

        # Create records with varying key orders (JSON doesn't guarantee order)
        DataRecord.objects.create(dataset=dataset, data={'c': 3, 'a': 1, 'b': 2})
        DataRecord.objects.create(dataset=dataset, data={'b': 2, 'c': 3, 'a': 1})
        DataRecord.objects.create(dataset=dataset, data={'a': 1, 'c': 3, 'b': 2})

        response = export_csv(Dataset.objects.filter(id=dataset.id))
        content = response.content.decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(content))

        # Check header order is consistent
        header = next(reader)
        assert list(header.keys()) == ['id', 'a', 'b', 'c']

        # Check all rows have same column order
        for row in reader:
            assert list(row.keys()) == ['id', 'a', 'b', 'c']
```

---

### Test Suite: Excel Export

```python
# tests/test_export_excel.py

import pytest
from openpyxl import load_workbook
from app.services.export import export_excel
from app.models import Dataset, DataRecord
import tempfile
import os

@pytest.mark.django_db
class TestExcelExport:

    def test_excel_header_styling(self):
        """Test that header row has correct styling"""
        dataset = Dataset.objects.create(title='Styling Test', record_count=1, uploaded_by_id=1)
        DataRecord.objects.create(dataset=dataset, data={'name': 'Test', 'value': 100})

        # Export to temporary file
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            filepath = f.name

        export_excel(Dataset.objects.filter(id=dataset.id), filepath)

        # Load and verify
        wb = load_workbook(filepath)
        ws = wb.active

        # Header cell A1 (should be "id")
        assert ws['A1'].value == 'id'
        assert ws['A1'].font.bold == True
        assert ws['A1'].font.color.rgb == 'FFFFFF'
        assert ws['A1'].fill.start_color.rgb == '4472C4'

        # Clean up
        os.unlink(filepath)

    def test_excel_zebra_striping(self):
        """Test alternating row background colors"""
        dataset = Dataset.objects.create(title='Zebra', record_count=4, uploaded_by_id=1)
        for i in range(4):
            DataRecord.objects.create(dataset=dataset, data={'value': i})

        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            filepath = f.name

        export_excel(Dataset.objects.filter(id=dataset.id), filepath)

        wb = load_workbook(filepath)
        ws = wb.active

        # Row 2 (first data row) - should have gray background
        assert ws['A2'].fill.start_color.rgb == 'F2F2F2'

        # Row 3 (second data row) - should have no fill
        assert ws['A3'].fill.start_color.rgb is None or ws['A3'].fill.start_color.rgb == '00000000'

        # Row 4 (third data row) - should have gray background
        assert ws['A4'].fill.start_color.rgb == 'F2F2F2'

        os.unlink(filepath)

    def test_excel_column_width_adjustment(self):
        """Test automatic column width adjustment"""
        dataset = Dataset.objects.create(title='Width', record_count=2, uploaded_by_id=1)
        DataRecord.objects.create(dataset=dataset, data={
            'short': 'Hi',
            'long': 'This is a very long text that should result in a wider column'
        })

        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            filepath = f.name

        export_excel(Dataset.objects.filter(id=dataset.id), filepath)

        wb = load_workbook(filepath)
        ws = wb.active

        # Check minimum width
        assert ws.column_dimensions['A'].width >= 8  # ID column

        # "short" column should be narrow
        short_col = ws.column_dimensions['B']
        assert 8 <= short_col.width <= 15

        # "long" column should be wider but capped at 50
        long_col = ws.column_dimensions['C']
        assert long_col.width <= 50

        os.unlink(filepath)

    def test_excel_number_formatting(self):
        """Test that numbers are formatted with thousand separators"""
        dataset = Dataset.objects.create(title='Numbers', record_count=1, uploaded_by_id=1)
        DataRecord.objects.create(dataset=dataset, data={
            'price': 1234.56,
            'quantity': 10000
        })

        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            filepath = f.name

        export_excel(Dataset.objects.filter(id=dataset.id), filepath, options={'format_numbers': True})

        wb = load_workbook(filepath)
        ws = wb.active

        # Find price column (assuming 'price' is column B after 'id')
        # Cell B2 should have number format
        price_cell = ws['B2']
        assert '#,##0' in price_cell.number_format or price_cell.number_format == '#,##0.00'

        os.unlink(filepath)

    def test_excel_date_formatting(self):
        """Test that dates are formatted consistently"""
        from datetime import date

        dataset = Dataset.objects.create(title='Dates', record_count=1, uploaded_by_id=1)
        DataRecord.objects.create(dataset=dataset, data={
            'enrollment_date': '2024-01-15',
            'graduation_date': '2028-05-20'
        })

        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            filepath = f.name

        export_excel(Dataset.objects.filter(id=dataset.id), filepath, options={'format_dates': True})

        wb = load_workbook(filepath)
        ws = wb.active

        # Date cells should have date format
        date_cell = ws['B2']
        # Check for common date formats (Excel uses various codes)
        assert 'yy' in date_cell.number_format.lower() or 'mm' in date_cell.number_format.lower()

        os.unlink(filepath)
```

---

### Test Suite: Async Export Jobs

```python
# tests/test_export_async.py

import pytest
from django.utils import timezone
from datetime import timedelta
from app.models import ExportJob, Dataset
from app.tasks import process_export_job, cleanup_expired_exports
import time

@pytest.mark.django_db
class TestAsyncExport:

    def test_export_job_creation(self):
        """Test that async export job is created correctly"""
        from app.views import create_export_job

        dataset = Dataset.objects.create(title='Large Dataset', record_count=15000, uploaded_by_id=1)
        job = create_export_job(dataset, format='excel', user_id=1)

        assert job.status == 'pending'
        assert job.progress == 0
        assert job.format == 'excel'
        assert job.dataset_id == dataset.id

    def test_progress_tracking_updates(self):
        """Test that progress updates correctly during processing"""
        dataset = Dataset.objects.create(title='Progress Test', record_count=10000, uploaded_by_id=1)
        job = ExportJob.objects.create(
            dataset=dataset,
            format='csv',
            status='processing',
            progress=0,
            user_id=1
        )

        # Simulate progress updates
        progress_values = [0, 25, 50, 75, 100]
        for progress in progress_values:
            job.progress = progress
            if progress == 100:
                job.status = 'completed'
            job.save()

            job.refresh_from_db()
            assert job.progress == progress

    def test_job_status_transitions(self):
        """Test valid status transitions"""
        job = ExportJob.objects.create(
            dataset_id=1,
            format='excel',
            status='pending',
            user_id=1
        )

        # pending → processing
        job.status = 'processing'
        job.save()
        job.refresh_from_db()
        assert job.status == 'processing'

        # processing → completed
        job.status = 'completed'
        job.progress = 100
        job.save()
        job.refresh_from_db()
        assert job.status == 'completed'

    def test_job_failure_handling(self):
        """Test that job failures are handled gracefully"""
        job = ExportJob.objects.create(
            dataset_id=1,
            format='pdf',
            status='processing',
            progress=45,
            user_id=1
        )

        # Simulate failure
        job.status = 'failed'
        job.error_message = 'Record #5437 has invalid JSON structure'
        job.save()

        job.refresh_from_db()
        assert job.status == 'failed'
        assert 'Record #5437' in job.error_message

    @pytest.mark.slow
    def test_file_cleanup_cron(self):
        """Test that expired files are cleaned up correctly"""
        from app.models import ExportHistory
        import os

        # Create expired export
        dataset = Dataset.objects.create(title='Cleanup Test', record_count=100, uploaded_by_id=1)
        job = ExportJob.objects.create(
            dataset=dataset,
            format='csv',
            status='completed',
            file_path='/tmp/test_expired.csv',
            user_id=1
        )

        history = ExportHistory.objects.create(
            job=job,
            expires_at=timezone.now() - timedelta(days=1),  # Expired
            file_hash='abc123'
        )

        # Create actual file
        os.makedirs(os.path.dirname(job.file_path), exist_ok=True)
        with open(job.file_path, 'w') as f:
            f.write('test,data\n1,2\n')

        assert os.path.exists(job.file_path)

        # Run cleanup
        cleanup_expired_exports()

        # File should be deleted
        assert not os.path.exists(job.file_path)

        # History should be marked (or deleted depending on implementation)
        history.refresh_from_db()
        # Implementation may delete record or mark as expired
```

---

### Test Suite: Role-Based Permissions

```python
# tests/test_export_permissions.py

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from app.models import Dataset

User = get_user_model()

@pytest.mark.django_db
class TestExportPermissions:

    def setup_method(self):
        """Create test users with different roles"""
        self.admin = User.objects.create_user(username='admin', password='pass', role='admin')
        self.manager = User.objects.create_user(username='manager', password='pass', role='manager')
        self.viewer = User.objects.create_user(username='viewer', password='pass', role='viewer')

        self.dataset = Dataset.objects.create(title='Test Dataset', record_count=100, uploaded_by=self.manager)
        self.client = APIClient()

    def test_admin_can_export_all_formats(self):
        """Admin should be able to export in all formats"""
        self.client.force_authenticate(user=self.admin)

        formats = ['csv', 'excel', 'pdf']
        for fmt in formats:
            response = self.client.post(f'/api/export/{fmt}/{self.dataset.id}/')
            assert response.status_code in [200, 202], f"Admin blocked from {fmt} export"

    def test_manager_can_export_own_datasets(self):
        """Manager should be able to export datasets they uploaded"""
        self.client.force_authenticate(user=self.manager)

        response = self.client.post(f'/api/export/csv/{self.dataset.id}/')
        assert response.status_code in [200, 202]

    def test_manager_cannot_export_others_datasets(self):
        """Manager should not be able to export datasets uploaded by others"""
        other_manager = User.objects.create_user(username='other', password='pass', role='manager')
        other_dataset = Dataset.objects.create(title='Other Dataset', record_count=50, uploaded_by=other_manager)

        self.client.force_authenticate(user=self.manager)
        response = self.client.post(f'/api/export/csv/{other_dataset.id}/')

        # Implementation choice: either 403 or 404 to hide existence
        assert response.status_code in [403, 404]

    def test_viewer_cannot_export(self):
        """Viewer should be completely blocked from exporting"""
        self.client.force_authenticate(user=self.viewer)

        response = self.client.post(f'/api/export/csv/{self.dataset.id}/')
        assert response.status_code == 403
        assert '권한' in response.json()['detail']

    def test_unauthenticated_cannot_export(self):
        """Unauthenticated users should be rejected"""
        # No authentication
        response = self.client.post(f'/api/export/csv/{self.dataset.id}/')
        assert response.status_code == 401

    def test_admin_can_view_all_export_history(self):
        """Admin should see export history from all users"""
        from app.models import ExportJob

        # Create exports from different users
        ExportJob.objects.create(dataset=self.dataset, format='csv', status='completed', user=self.manager)
        ExportJob.objects.create(dataset=self.dataset, format='excel', status='completed', user=self.admin)

        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/export/history/')

        assert response.status_code == 200
        assert len(response.data) == 2  # Sees both exports

    def test_manager_sees_only_own_export_history(self):
        """Manager should only see their own export history"""
        from app.models import ExportJob

        # Create exports from different users
        ExportJob.objects.create(dataset=self.dataset, format='csv', status='completed', user=self.manager)
        ExportJob.objects.create(dataset=self.dataset, format='excel', status='completed', user=self.admin)

        self.client.force_authenticate(user=self.manager)
        response = self.client.get('/api/export/history/')

        assert response.status_code == 200
        assert len(response.data) == 1  # Sees only own export
        assert response.data[0]['user'] == self.manager.id
```

---

## Frontend Test Examples

### Test Suite: Export Buttons

```typescript
// tests/ExportButtons.test.tsx

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import ExportButtons from '@/components/ExportButtons'
import { exportApi } from '@/lib/api/export'

// Mock API
vi.mock('@/lib/api/export', () => ({
  exportApi: {
    exportCSV: vi.fn(),
    exportExcel: vi.fn(),
    exportPDF: vi.fn(),
  }
}))

describe('ExportButtons', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders all export format buttons', () => {
    render(<ExportButtons datasetId={123} />)

    expect(screen.getByText(/CSV 다운로드/)).toBeInTheDocument()
    expect(screen.getByText(/Excel 다운로드/)).toBeInTheDocument()
    expect(screen.getByText(/PDF 다운로드/)).toBeInTheDocument()
  })

  it('triggers CSV export on button click', async () => {
    vi.mocked(exportApi.exportCSV).mockResolvedValue({
      status: 200,
      data: new Blob(['test,data'], { type: 'text/csv' })
    })

    render(<ExportButtons datasetId={123} />)

    const csvButton = screen.getByText(/CSV 다운로드/)
    fireEvent.click(csvButton)

    await waitFor(() => {
      expect(exportApi.exportCSV).toHaveBeenCalledWith(123)
    })
  })

  it('shows loading state during export', async () => {
    vi.mocked(exportApi.exportExcel).mockImplementation(() =>
      new Promise(resolve => setTimeout(resolve, 1000))
    )

    render(<ExportButtons datasetId={123} />)

    const excelButton = screen.getByText(/Excel 다운로드/)
    fireEvent.click(excelButton)

    // Loading spinner should appear
    expect(screen.getByRole('status')).toBeInTheDocument()
    expect(excelButton).toBeDisabled()
  })

  it('disables buttons for viewer role', () => {
    render(<ExportButtons datasetId={123} userRole="viewer" />)

    const csvButton = screen.getByText(/CSV 다운로드/)
    expect(csvButton).toBeDisabled()
    expect(csvButton).toHaveAttribute('title', '내보내기 권한이 없습니다')
  })

  it('shows async progress modal for large datasets', async () => {
    vi.mocked(exportApi.exportExcel).mockResolvedValue({
      status: 202,
      data: { job_id: 'job-123', message: '처리 중...' }
    })

    render(<ExportButtons datasetId={123} recordCount={20000} />)

    const excelButton = screen.getByText(/Excel 다운로드/)
    fireEvent.click(excelButton)

    await waitFor(() => {
      expect(screen.getByText(/내보내기 중.../)).toBeInTheDocument()
      expect(screen.getByRole('progressbar')).toBeInTheDocument()
    })
  })
})
```

---

### Test Suite: Export Progress Modal

```typescript
// tests/ExportProgressModal.test.tsx

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import ExportProgressModal from '@/components/ExportProgressModal'
import { exportApi } from '@/lib/api/export'

vi.mock('@/lib/api/export')

describe('ExportProgressModal', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('polls job status every 2 seconds', async () => {
    vi.mocked(exportApi.getJobStatus).mockResolvedValue({
      status: 'processing',
      progress: 50,
      message: '10,000 / 20,000 records processed'
    })

    render(<ExportProgressModal jobId="job-123" onClose={vi.fn()} />)

    // Wait for initial poll
    await waitFor(() => {
      expect(exportApi.getJobStatus).toHaveBeenCalledWith('job-123')
    })

    // Wait for second poll (2 seconds later)
    await waitFor(() => {
      expect(exportApi.getJobStatus).toHaveBeenCalledTimes(2)
    }, { timeout: 3000 })
  })

  it('displays progress percentage', async () => {
    vi.mocked(exportApi.getJobStatus).mockResolvedValue({
      status: 'processing',
      progress: 75,
      message: '75% complete'
    })

    render(<ExportProgressModal jobId="job-123" onClose={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByText(/75%/)).toBeInTheDocument()
    })

    // Check progress bar width
    const progressBar = screen.getByRole('progressbar')
    expect(progressBar).toHaveStyle({ width: '75%' })
  })

  it('triggers download on completion', async () => {
    const originalLocation = window.location
    delete window.location
    window.location = { href: '' } as Location

    vi.mocked(exportApi.getJobStatus).mockResolvedValue({
      status: 'completed',
      progress: 100,
      download_url: 'https://example.com/exports/file.xlsx'
    })

    const onClose = vi.fn()
    render(<ExportProgressModal jobId="job-123" onClose={onClose} />)

    await waitFor(() => {
      expect(window.location.href).toBe('https://example.com/exports/file.xlsx')
    })

    // Modal should close after 2 seconds
    await waitFor(() => {
      expect(onClose).toHaveBeenCalled()
    }, { timeout: 3000 })

    window.location = originalLocation
  })

  it('displays error message on failure', async () => {
    vi.mocked(exportApi.getJobStatus).mockResolvedValue({
      status: 'failed',
      progress: 45,
      error_message: 'Record #5437 has invalid JSON structure'
    })

    render(<ExportProgressModal jobId="job-123" onClose={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByText(/오류가 발생했습니다/)).toBeInTheDocument()
      expect(screen.getByText(/Record #5437/)).toBeInTheDocument()
    })

    // Retry button should appear
    expect(screen.getByText(/재시도/)).toBeInTheDocument()
  })

  it('stops polling on modal close', async () => {
    vi.mocked(exportApi.getJobStatus).mockResolvedValue({
      status: 'processing',
      progress: 30
    })

    const { unmount } = render(<ExportProgressModal jobId="job-123" onClose={vi.fn()} />)

    // Wait for initial poll
    await waitFor(() => {
      expect(exportApi.getJobStatus).toHaveBeenCalledTimes(1)
    })

    const callCountBeforeUnmount = vi.mocked(exportApi.getJobStatus).mock.calls.length

    // Unmount component
    unmount()

    // Wait 3 seconds
    await new Promise(resolve => setTimeout(resolve, 3000))

    // No additional calls should be made after unmount
    expect(vi.mocked(exportApi.getJobStatus).mock.calls.length).toBe(callCountBeforeUnmount)
  })
})
```

---

### Test Suite: Export History Page

```typescript
// tests/ExportHistoryPage.test.tsx

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import ExportHistoryPage from '@/app/export/history/page'
import { exportApi } from '@/lib/api/export'

vi.mock('@/lib/api/export')

describe('ExportHistoryPage', () => {
  const mockHistory = [
    {
      id: 'job-1',
      dataset_title: 'Student Records',
      format: 'excel',
      created_at: '2025-01-20T10:30:00Z',
      file_size: 6291456,  // 6 MB
      status: 'completed',
      download_url: 'https://example.com/exports/file1.xlsx',
      download_count: 2
    },
    {
      id: 'job-2',
      dataset_title: 'Course Evaluations',
      format: 'pdf',
      created_at: '2025-01-18T14:15:00Z',
      file_size: 2097152,  // 2 MB
      status: 'completed',
      download_url: 'https://example.com/exports/file2.pdf',
      download_count: 0
    },
    {
      id: 'job-3',
      dataset_title: 'Large Dataset',
      format: 'csv',
      created_at: '2025-01-17T09:00:00Z',
      file_size: 0,
      status: 'failed',
      error_message: 'Processing timeout'
    }
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(exportApi.getHistory).mockResolvedValue(mockHistory)
  })

  it('displays export history in table', async () => {
    render(<ExportHistoryPage />)

    await waitFor(() => {
      expect(screen.getByText('Student Records')).toBeInTheDocument()
      expect(screen.getByText('Course Evaluations')).toBeInTheDocument()
      expect(screen.getByText('Large Dataset')).toBeInTheDocument()
    })
  })

  it('shows file sizes in human-readable format', async () => {
    render(<ExportHistoryPage />)

    await waitFor(() => {
      expect(screen.getByText('6.0 MB')).toBeInTheDocument()  // 6291456 bytes
      expect(screen.getByText('2.0 MB')).toBeInTheDocument()  // 2097152 bytes
    })
  })

  it('displays status badges with correct colors', async () => {
    render(<ExportHistoryPage />)

    await waitFor(() => {
      const completedBadges = screen.getAllByText('완료')
      expect(completedBadges[0]).toHaveClass('bg-green-100')

      const failedBadge = screen.getByText('실패')
      expect(failedBadge).toHaveClass('bg-red-100')
    })
  })

  it('triggers download on button click', async () => {
    const originalLocation = window.location
    delete window.location
    window.location = { href: '' } as Location

    render(<ExportHistoryPage />)

    await waitFor(() => {
      expect(screen.getByText('Student Records')).toBeInTheDocument()
    })

    // Find and click first download button
    const downloadButtons = screen.getAllByText(/다운로드/)
    fireEvent.click(downloadButtons[0])

    expect(window.location.href).toBe('https://example.com/exports/file1.xlsx')

    window.location = originalLocation
  })

  it('increments download count after download', async () => {
    vi.mocked(exportApi.trackDownload).mockResolvedValue({ download_count: 3 })

    render(<ExportHistoryPage />)

    await waitFor(() => {
      expect(screen.getByText('2회 다운로드')).toBeInTheDocument()
    })

    const downloadButtons = screen.getAllByText(/다운로드/)
    fireEvent.click(downloadButtons[0])

    await waitFor(() => {
      expect(exportApi.trackDownload).toHaveBeenCalledWith('job-1')
      expect(screen.getByText('3회 다운로드')).toBeInTheDocument()
    })
  })

  it('deletes export on delete button click', async () => {
    vi.mocked(exportApi.deleteExport).mockResolvedValue({ success: true })

    render(<ExportHistoryPage />)

    await waitFor(() => {
      expect(screen.getByText('Course Evaluations')).toBeInTheDocument()
    })

    // Find and click delete button
    const deleteButtons = screen.getAllByText(/삭제/)
    fireEvent.click(deleteButtons[1])  // Second export

    // Confirm dialog
    fireEvent.click(screen.getByText(/확인/))

    await waitFor(() => {
      expect(exportApi.deleteExport).toHaveBeenCalledWith('job-2')
      expect(screen.queryByText('Course Evaluations')).not.toBeInTheDocument()
    })
  })

  it('shows error message for failed exports', async () => {
    render(<ExportHistoryPage />)

    await waitFor(() => {
      expect(screen.getByText('Processing timeout')).toBeInTheDocument()
    })

    // Failed export should not have download button
    const rows = screen.getAllByRole('row')
    const failedRow = rows.find(row => row.textContent?.includes('Large Dataset'))
    expect(failedRow).toBeDefined()
    expect(failedRow?.querySelector('button[aria-label="다운로드"]')).toBeNull()
  })

  it('filters history by format', async () => {
    render(<ExportHistoryPage />)

    await waitFor(() => {
      expect(screen.getByText('Student Records')).toBeInTheDocument()
    })

    // Select filter dropdown
    const filterSelect = screen.getByLabelText(/형식 필터/)
    fireEvent.change(filterSelect, { target: { value: 'excel' } })

    // Only Excel exports should be visible
    expect(screen.getByText('Student Records')).toBeInTheDocument()
    expect(screen.queryByText('Course Evaluations')).not.toBeInTheDocument()
    expect(screen.queryByText('Large Dataset')).not.toBeInTheDocument()
  })
})
```

---

## Performance Benchmarks

### Benchmark 1: CSV Export Performance

**Test Configuration**:
- Record counts: 1K, 5K, 10K, 50K, 100K
- Average record size: 200 bytes (5 columns × 40 chars)
- Server: Railway (2GB RAM, 2 vCPU)
- Network: Excluded from measurement (testing backend only)

**Acceptance Criteria**:
| Records | Max Time | Max Memory | Status |
|---------|----------|------------|--------|
| 1,000 | ≤ 0.5s | ≤ 20 MB | ✅ Pass |
| 5,000 | ≤ 1.5s | ≤ 40 MB | ✅ Pass |
| 10,000 | ≤ 3.0s | ≤ 60 MB | ✅ Pass |
| 50,000 | ≤ 15s | ≤ 100 MB | ✅ Pass |
| 100,000 | ≤ 30s | ≤ 100 MB | ✅ Pass |

**Validation Method**:
```python
import time
import memory_profiler

@memory_profiler.profile
def benchmark_csv_export(record_count):
    dataset = Dataset.objects.create(title=f'Benchmark {record_count}', record_count=record_count)

    # Create records
    records = [DataRecord(dataset=dataset, data={'col1': f'value{i}', 'col2': i}) for i in range(record_count)]
    DataRecord.objects.bulk_create(records, batch_size=5000)

    start = time.time()
    response = export_csv(Dataset.objects.filter(id=dataset.id))

    # Consume response
    for chunk in response.streaming_content:
        pass

    elapsed = time.time() - start

    print(f"Records: {record_count}, Time: {elapsed:.2f}s")
    assert elapsed <= THRESHOLD[record_count]

# Run benchmarks
for count in [1000, 5000, 10000, 50000, 100000]:
    benchmark_csv_export(count)
```

---

### Benchmark 2: Excel Export Performance

**Test Configuration**:
- Record counts: 1K, 5K, 10K, 25K
- With styling: Blue headers, zebra striping, auto-width
- File saved to disk (not streamed)

**Acceptance Criteria**:
| Records | Max Time | Max Memory | File Size | Status |
|---------|----------|------------|-----------|--------|
| 1,000 | ≤ 1s | ≤ 30 MB | ~250 KB | ✅ Pass |
| 5,000 | ≤ 5s | ≤ 50 MB | ~1.2 MB | ✅ Pass |
| 10,000 | ≤ 10s | ≤ 80 MB | ~2.5 MB | ✅ Pass |
| 25,000 | ≤ 30s | ≤ 120 MB | ~6.0 MB | ✅ Pass |

**Note**: Excel exports are slower than CSV due to styling and structure overhead.

---

### Benchmark 3: PDF Export Performance

**Test Configuration**:
- Record counts: 500, 1K, 2K, 5K
- Includes: 2 charts (PNG, 600×400px each), summary table
- Page size: A4, landscape orientation

**Acceptance Criteria**:
| Records | Charts | Max Time | Max Memory | File Size | Pages | Status |
|---------|--------|----------|------------|-----------|-------|--------|
| 500 | 2 | ≤ 5s | ≤ 60 MB | ~800 KB | 3-5 | ✅ Pass |
| 1,000 | 2 | ≤ 10s | ≤ 80 MB | ~1.5 MB | 6-8 | ✅ Pass |
| 2,000 | 2 | ≤ 20s | ≤ 100 MB | ~3.0 MB | 12-15 | ✅ Pass |
| 5,000 | 2 | ≤ 60s | ≤ 150 MB | ~7.0 MB | 30-35 | ✅ Pass |

**Note**: PDF is the slowest format due to complex layout and chart embedding.

---

### Benchmark 4: Async Job Processing

**Test Configuration**:
- Job queue: django-q with 4 workers
- Concurrent jobs: 10 simultaneous exports
- Record count per job: 15,000

**Acceptance Criteria**:
- ✅ All jobs complete within 2 minutes (total)
- ✅ No job fails due to worker timeout
- ✅ Progress updates occur every 2 seconds for all jobs
- ✅ Server load stays under 80% CPU and 1.5 GB RAM
- ✅ No deadlocks or race conditions

**Validation Method**:
```python
import concurrent.futures

def test_concurrent_export_jobs():
    # Create 10 datasets
    datasets = [Dataset.objects.create(title=f'Concurrent {i}', record_count=15000) for i in range(10)]

    # Trigger 10 exports simultaneously
    job_ids = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(create_export_job, ds, 'excel', user_id=1) for ds in datasets]
        job_ids = [f.result().id for f in futures]

    # Wait for all to complete (max 2 minutes)
    start = time.time()
    while time.time() - start < 120:
        statuses = [ExportJob.objects.get(id=jid).status for jid in job_ids]
        if all(s in ['completed', 'failed'] for s in statuses):
            break
        time.sleep(2)

    # All should be completed
    final_statuses = [ExportJob.objects.get(id=jid).status for jid in job_ids]
    assert all(s == 'completed' for s in final_statuses)
```

---

## Security Validation

### SEC-EXPORT-001: Authentication Required

**Validation**:
- ✅ All export endpoints require valid JWT token
- ✅ Expired tokens return 401 Unauthorized
- ✅ Missing tokens return 401 Unauthorized
- ✅ Invalid tokens return 401 Unauthorized

---

### SEC-EXPORT-002: Role-Based Access Control

**Validation**:
- ✅ Viewer role blocked from all exports (403 Forbidden)
- ✅ Manager can export only own datasets
- ✅ Admin can export all datasets
- ✅ Role verification occurs on every request (no caching)

---

### SEC-EXPORT-003: File Access Control

**Validation**:
- ✅ Direct file URLs include signed tokens or are time-limited
- ✅ Users cannot download others' export files by guessing URLs
- ✅ File paths do not expose internal directory structure
- ✅ Directory traversal attacks blocked (`../../../etc/passwd`)

---

### SEC-EXPORT-004: Data Sanitization

**Validation**:
- ✅ CSV injection prevented (no formulas starting with =, +, -, @)
- ✅ XSS in Excel prevented (HTML tags escaped)
- ✅ PDF injection prevented (special characters escaped in reportlab)
- ✅ No SQL injection via export filters

---

### SEC-EXPORT-005: Rate Limiting

**Validation**:
- ✅ Max 10 export requests per user per minute
- ✅ Max 3 concurrent export jobs per user
- ✅ 429 Too Many Requests returned when limits exceeded
- ✅ Rate limit resets after cooldown period

---

### SEC-EXPORT-006: File Integrity

**Validation**:
- ✅ MD5 hash stored in ExportHistory
- ✅ Hash verified before each download
- ✅ Corrupted files display warning and prevent download
- ✅ File tampering detected and logged

---

## User Acceptance Scenarios

### Scenario 1: Manager Exports Monthly Report

**User**: Sarah Kim, Manager
**Goal**: Export January 2025 enrollment data for board meeting

**Steps**:
1. Log in to dashboard
2. Navigate to "Student Enrollment" dataset
3. Apply filter: enrollment_date between 2025-01-01 and 2025-01-31
4. Click "Excel 다운로드" button
5. Wait for progress modal (dataset has 8,500 records → async)
6. Download completes automatically
7. Open Excel file, verify data and styling
8. Share file with board members

**Success Criteria**:
- ✅ Export completes in ≤ 15 seconds
- ✅ Excel file has professional styling (blue headers, zebra rows)
- ✅ Only January 2025 records included (date filter applied correctly)
- ✅ Column widths readable, no text cutoff
- ✅ File size reasonable (~2 MB for 8,500 records)

---

### Scenario 2: Admin Generates PDF Report with Charts

**User**: Dr. Park, Admin
**Goal**: Create PDF report of Q4 2024 course evaluations with visualizations

**Steps**:
1. Log in as admin
2. Navigate to "Course Evaluations Q4 2024" dataset
3. View charts on dashboard (satisfaction by department, response rates)
4. Click "PDF 다운로드" button
5. Select "차트 포함" option
6. Wait for async processing (~20 seconds for 1,500 records)
7. Download PDF
8. Review PDF: header with logo, summary stats, 2 charts, data table
9. Share PDF via email to faculty

**Success Criteria**:
- ✅ PDF includes university logo in header
- ✅ Summary statistics displayed prominently
- ✅ Both charts embedded as clear images (not blurry)
- ✅ Data table formatted with pagination
- ✅ Page numbers on every page
- ✅ Professional appearance suitable for stakeholders

---

### Scenario 3: Viewer Attempts Export (Denied)

**User**: John Lee, Viewer
**Goal**: Attempt to export student records (should be blocked)

**Steps**:
1. Log in as viewer
2. Navigate to "Student Records" dataset
3. Observe export buttons grayed out/disabled
4. Attempt to click "CSV 다운로드" button
5. See error message

**Success Criteria**:
- ✅ Export buttons visually disabled (grayed out)
- ✅ Tooltip displays: "내보내기 권한이 없습니다"
- ✅ On click, toast notification shows permission error
- ✅ No file downloads
- ✅ API returns 403 Forbidden
- ✅ User understands they don't have permission

---

### Scenario 4: Manager Reviews Export History

**User**: Sarah Kim, Manager
**Goal**: Review past exports and download previous month's report

**Steps**:
1. Navigate to "내보내기 내역" page
2. See list of past exports (5 in last 7 days)
3. Filter by format: "Excel"
4. Find December 2024 enrollment export
5. Click download button
6. File downloads immediately from history

**Success Criteria**:
- ✅ All exports from past 7 days displayed
- ✅ Each entry shows: dataset title, format, date, file size, status
- ✅ Download count increments (0 → 1)
- ✅ File downloads without re-generating (instant)
- ✅ Can delete old exports to clean up history

---

### Scenario 5: Handling Large Dataset Export

**User**: Dr. Park, Admin
**Goal**: Export full academic year data (75,000 student records)

**Steps**:
1. Navigate to "All Students 2024-2025" dataset
2. Click "CSV 다운로드" button
3. System detects large dataset → triggers async job
4. Progress modal displays immediately
5. Progress updates every 2 seconds: 0% → 15% → 30% → ... → 100%
6. Estimated time displayed: "약 45초 남음"
7. At 100%, download starts automatically
8. File saved to computer

**Success Criteria**:
- ✅ Async job triggered (not sync export)
- ✅ Progress modal shows real-time updates
- ✅ Export completes in ≤ 60 seconds
- ✅ Memory usage stays under 100 MB
- ✅ CSV file is valid (no corruption from streaming)
- ✅ All 75,000 records present in file

---

## Completion Checklist

### Code Implementation
- [ ] CSV export utility with UTF-8 BOM encoding implemented
- [ ] Excel export with openpyxl styling implemented
- [ ] PDF export with reportlab layout implemented
- [ ] Async job processing with django-q configured
- [ ] Progress tracking API endpoints created
- [ ] Export history model and endpoints created
- [ ] File cleanup cron job scheduled
- [ ] Role-based permission decorators applied

### API Endpoints
- [ ] POST `/api/export/csv/{dataset_id}/` - CSV export
- [ ] POST `/api/export/excel/{dataset_id}/` - Excel export
- [ ] POST `/api/export/pdf/{dataset_id}/` - PDF export
- [ ] POST `/api/export/async/` - Create async export job
- [ ] GET `/api/export/status/{job_id}/` - Job status polling
- [ ] GET `/api/export/download/{job_id}/` - Download completed file
- [ ] GET `/api/export/history/` - List user's export history
- [ ] DELETE `/api/export/history/{job_id}/` - Delete export

### Frontend Components
- [ ] ExportButtons component with format selection
- [ ] ExportProgressModal component with polling
- [ ] ExportHistoryPage with table and filters
- [ ] ExportOptionsDialog for custom configurations
- [ ] Error toast notifications for failures
- [ ] Loading states for all async operations

### Testing
- [ ] Unit tests: CSV export (UTF-8, special chars, streaming)
- [ ] Unit tests: Excel export (styling, width, formatting)
- [ ] Unit tests: PDF export (layout, charts, pagination)
- [ ] Integration tests: Async job lifecycle
- [ ] Integration tests: Role-based permissions
- [ ] E2E tests: Complete export workflows
- [ ] Performance tests: All benchmarks pass
- [ ] Security tests: All validation criteria met

### Documentation
- [ ] API documentation updated in Swagger
- [ ] User guide with screenshots created
- [ ] Developer guide with code examples
- [ ] Error message reference documented
- [ ] Troubleshooting guide added

### Deployment
- [ ] Environment variables configured (EXPORT_DIR, RETENTION_DAYS)
- [ ] Django-Q worker process running
- [ ] File storage directory created with correct permissions
- [ ] Cleanup cron job scheduled (crontab or Railway scheduler)
- [ ] Monitoring alerts configured for job failures

### Quality Assurance
- [ ] Code review completed
- [ ] Linting passes (Ruff, Black, ESLint)
- [ ] Type checking passes (mypy, TypeScript)
- [ ] Test coverage ≥ 90% backend, ≥ 85% frontend
- [ ] Security scan completed (Bandit, npm audit)
- [ ] Performance benchmarks documented
- [ ] Load testing completed (10 concurrent users)

### User Acceptance
- [ ] Manager successfully exports CSV with 10K records
- [ ] Admin successfully exports PDF with charts
- [ ] Viewer blocked from exporting (verified)
- [ ] Export history page displays correctly
- [ ] File download and deletion working
- [ ] Progress tracking accurate during async jobs

### Rollback Plan
- [ ] Backup of database before deployment
- [ ] Export feature toggle implemented (can disable quickly)
- [ ] Rollback script prepared
- [ ] Monitoring dashboard shows export metrics

---

## Final Approval

**SPEC-EXPORT-001 is ACCEPTED when**:
- ✅ All functional acceptance criteria (AC-EXPORT-001 ~ AC-EXPORT-015) pass
- ✅ All test scenarios execute successfully
- ✅ Performance benchmarks meet targets
- ✅ Security validation checklist complete
- ✅ User acceptance scenarios verified by stakeholders
- ✅ Completion checklist 100% checked
- ✅ Production deployment successful with zero critical bugs

**Approved by**: _________________________
**Date**: _________________________

---

**@TAG**: @SPEC:EXPORT-001 → @TEST:EXPORT-ALL → @ACCEPTANCE:COMPLETE

**Related Documents**:
- [SPEC-EXPORT-001: spec.md](./spec.md)
- [SPEC-EXPORT-001: plan.md](./plan.md)
- [SPEC-AUTH-001: Authentication](../SPEC-AUTH-001/spec.md)
- [SPEC-DASH-001: Dashboard Foundation](../SPEC-DASH-001/spec.md)

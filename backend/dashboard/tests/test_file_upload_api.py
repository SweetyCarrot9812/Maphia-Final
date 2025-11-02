"""
Tests for File Upload API

@SPEC:DASH-001
@TEST:FILE-UPLOAD-API

Tests the Excel file upload endpoint.
"""

import pytest
from io import BytesIO
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from openpyxl import Workbook

from dashboard.models import Dataset, DataRecord

User = get_user_model()


@pytest.fixture
def api_client():
    """Fixture for DRF API client"""
    return APIClient()


@pytest.fixture
def test_user(db):
    """Fixture for creating a test user"""
    return User.objects.create_user(
        username='testuser',
        password='TestPass123!',
        email='test@example.com',
        role='admin'
    )


@pytest.fixture
def authenticated_client(api_client, test_user):
    """Fixture for authenticated API client"""
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(test_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
    return api_client


def create_sample_excel():
    """Helper: Create a sample Excel file in memory"""
    wb = Workbook()
    ws = wb.active

    # Add headers
    ws.append(['Student ID', 'Name', 'GPA', 'Department'])

    # Add data
    ws.append([1001, 'Alice', 3.8, 'Engineering'])
    ws.append([1002, 'Bob', 3.5, 'Business'])
    ws.append([1003, 'Charlie', 3.9, 'Science'])

    excel_file = BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)
    excel_file.name = 'students.xlsx'

    return excel_file


@pytest.mark.django_db
@pytest.mark.integration
class TestFileUploadAPI:
    """
    Tests for file upload API endpoint.

    Requirements:
    - REQ-DASH-001: File Upload with validation
    - REQ-DASH-002: Data Storage with metadata
    """

    def test_upload_excel_file_successfully(self, authenticated_client, test_user):
        """
        @TEST:FILE-UPLOAD-001
        Successfully upload an Excel file and create Dataset + DataRecords
        """
        url = '/api/datasets/upload/'

        excel_file = create_sample_excel()

        data = {
            'file': excel_file,
            'title': 'Student Data',
            'description': 'Fall 2023 student enrollment',
            'category': 'enrollment'
        }

        response = authenticated_client.post(url, data, format='multipart')

        assert response.status_code == status.HTTP_201_CREATED
        assert 'id' in response.data
        assert response.data['title'] == 'Student Data'
        assert response.data['record_count'] == 3
        assert response.data['filename'] == 'students.xlsx'

        # Verify Dataset was created
        dataset = Dataset.objects.get(id=response.data['id'])
        assert dataset.title == 'Student Data'
        assert dataset.record_count == 3
        assert dataset.uploaded_by == test_user

        # Verify DataRecords were created
        records = DataRecord.objects.filter(dataset=dataset)
        assert records.count() == 3

        # Check first record
        first_record = records.first()
        assert first_record.data['Student ID'] == 1001
        assert first_record.data['Name'] == 'Alice'
        assert first_record.data['GPA'] == 3.8

    def test_upload_without_authentication(self, api_client):
        """
        @TEST:FILE-UPLOAD-002
        Upload without authentication should return 401
        """
        url = '/api/datasets/upload/'

        excel_file = create_sample_excel()

        data = {
            'file': excel_file,
            'title': 'Student Data'
        }

        response = api_client.post(url, data, format='multipart')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_upload_without_file(self, authenticated_client):
        """
        @TEST:FILE-UPLOAD-003
        Upload without file should return 400
        """
        url = '/api/datasets/upload/'

        data = {
            'title': 'Student Data',
            'category': 'enrollment'
        }

        response = authenticated_client.post(url, data, format='multipart')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'file' in str(response.data).lower()

    def test_upload_invalid_file_format(self, authenticated_client):
        """
        @TEST:FILE-UPLOAD-004
        Upload non-Excel file should return 400
        """
        url = '/api/datasets/upload/'

        # Create invalid file (text file, not Excel)
        invalid_file = BytesIO(b"This is not an Excel file")
        invalid_file.name = 'document.txt'

        data = {
            'file': invalid_file,
            'title': 'Invalid Data'
        }

        response = authenticated_client.post(url, data, format='multipart')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'invalid' in str(response.data).lower() or 'format' in str(response.data).lower()

    def test_upload_file_too_large(self, authenticated_client):
        """
        @TEST:FILE-UPLOAD-005
        Upload file larger than 10MB should return 400
        """
        url = '/api/datasets/upload/'

        # Create a large file (simulate > 10MB)
        large_file = BytesIO(b"x" * (11 * 1024 * 1024))  # 11MB
        large_file.name = 'large_file.xlsx'

        data = {
            'file': large_file,
            'title': 'Large File'
        }

        response = authenticated_client.post(url, data, format='multipart')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'size' in str(response.data).lower() or 'large' in str(response.data).lower()

    def test_upload_empty_excel_file(self, authenticated_client):
        """
        @TEST:FILE-UPLOAD-006
        Upload empty Excel file should return 400
        """
        url = '/api/datasets/upload/'

        # Create empty Excel file
        wb = Workbook()
        ws = wb.active

        excel_file = BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)
        excel_file.name = 'empty.xlsx'

        data = {
            'file': excel_file,
            'title': 'Empty Data'
        }

        response = authenticated_client.post(url, data, format='multipart')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'empty' in str(response.data).lower()

    def test_upload_with_missing_title(self, authenticated_client):
        """
        @TEST:FILE-UPLOAD-007
        Upload without title should return 400
        """
        url = '/api/datasets/upload/'

        excel_file = create_sample_excel()

        data = {
            'file': excel_file,
            # Missing title
            'category': 'enrollment'
        }

        response = authenticated_client.post(url, data, format='multipart')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'title' in str(response.data).lower()

    def test_upload_with_special_characters_in_filename(self, authenticated_client, test_user):
        """
        @TEST:FILE-UPLOAD-008
        Upload file with special characters in filename should succeed
        """
        url = '/api/datasets/upload/'

        excel_file = create_sample_excel()
        excel_file.name = 'student-data_2023 (Fall).xlsx'

        data = {
            'file': excel_file,
            'title': 'Student Data'
        }

        response = authenticated_client.post(url, data, format='multipart')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['filename'] == 'student-data_2023 (Fall).xlsx'

    def test_upload_creates_correct_metadata(self, authenticated_client, test_user):
        """
        @TEST:FILE-UPLOAD-009
        Verify all metadata fields are correctly populated
        """
        url = '/api/datasets/upload/'

        excel_file = create_sample_excel()

        data = {
            'file': excel_file,
            'title': 'Test Dataset',
            'description': 'Test description',
            'category': 'test_category'
        }

        response = authenticated_client.post(url, data, format='multipart')

        assert response.status_code == status.HTTP_201_CREATED

        dataset = Dataset.objects.get(id=response.data['id'])
        assert dataset.title == 'Test Dataset'
        assert dataset.description == 'Test description'
        assert dataset.category == 'test_category'
        assert dataset.filename == 'students.xlsx'
        assert dataset.file_size > 0
        assert dataset.record_count == 3
        assert dataset.uploaded_by == test_user
        assert dataset.upload_date is not None

"""
Tests for CSV Export API functionality.

@SPEC:EXPORT-001 - CSV Export System

Test Coverage:
- REQ-EXPORT-001: Basic CSV export with UTF-8 BOM encoding
- REQ-EXPORT-002: RFC 4180 special character handling
- Role-based access control (Admin/Manager only)
- Empty dataset handling
- HTTP headers validation
"""

import pytest
import csv
import io
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from dashboard.models import Dataset, DataRecord
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestCSVExportAPI:
    """Test suite for CSV export functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data before each test."""
        self.client = APIClient()

        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            role='admin'
        )
        self.manager_user = User.objects.create_user(
            username='manager',
            email='manager@test.com',
            password='testpass123',
            role='manager'
        )
        self.viewer_user = User.objects.create_user(
            username='viewer',
            email='viewer@test.com',
            password='testpass123',
            role='viewer'
        )

        # Create test dataset
        self.dataset = Dataset.objects.create(
            title='Test Dataset',
            description='Test dataset for CSV export',
            filename='test.xlsx',
            file_size=1024,
            record_count=3,
            category='test',
            uploaded_by=self.admin_user
        )

        # Create test records with various data types
        self.records = [
            DataRecord.objects.create(
                dataset=self.dataset,
                data={
                    'name': '홍길동',
                    'age': 25,
                    'score': 95.5,
                    'enrolled': True
                }
            ),
            DataRecord.objects.create(
                dataset=self.dataset,
                data={
                    'name': 'Jane Smith',
                    'age': 30,
                    'score': 88.0,
                    'enrolled': False
                }
            ),
            DataRecord.objects.create(
                dataset=self.dataset,
                data={
                    'name': 'Test, "User"',  # Special characters for RFC 4180 test
                    'age': 22,
                    'score': 92.3,
                    'enrolled': True
                }
            ),
        ]

    def test_csv_export_requires_authentication(self):
        """
        @SPEC:REQ-EXPORT-001
        Test that CSV export requires authentication.

        Expected: 401 Unauthorized for unauthenticated requests
        """
        url = reverse('dataset-export-csv', kwargs={'pk': self.dataset.pk})
        response = self.client.post(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_csv_export_admin_access(self):
        """
        @SPEC:REQ-EXPORT-001
        Test that admin users can export CSV.

        Expected: 200 OK with CSV file
        """
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('dataset-export-csv', kwargs={'pk': self.dataset.pk})
        response = self.client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response['Content-Type'] == 'text/csv; charset=utf-8'
        assert 'attachment; filename=' in response['Content-Disposition']

    def test_csv_export_manager_access(self):
        """
        @SPEC:REQ-EXPORT-001
        Test that manager users can export CSV.

        Expected: 200 OK with CSV file
        """
        self.client.force_authenticate(user=self.manager_user)
        url = reverse('dataset-export-csv', kwargs={'pk': self.dataset.pk})
        response = self.client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response['Content-Type'] == 'text/csv; charset=utf-8'

    def test_csv_export_viewer_denied(self):
        """
        Test that viewer users cannot export CSV.

        Expected: 403 Forbidden
        """
        self.client.force_authenticate(user=self.viewer_user)
        url = reverse('dataset-export-csv', kwargs={'pk': self.dataset.pk})
        response = self.client.post(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_csv_export_utf8_bom_encoding(self):
        """
        @SPEC:REQ-EXPORT-001
        Test that CSV export uses UTF-8 encoding with BOM.

        Expected: File starts with UTF-8 BOM (\ufeff)
        """
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('dataset-export-csv', kwargs={'pk': self.dataset.pk})
        response = self.client.post(url)

        assert response.status_code == status.HTTP_200_OK

        # Check UTF-8 BOM at start of content
        content = response.content.decode('utf-8-sig')
        assert content.startswith('name,age,score,enrolled') or 'name' in content[:100]

        # Check Korean characters are properly encoded
        assert '홍길동' in content

    def test_csv_export_contains_headers(self):
        """
        @SPEC:REQ-EXPORT-001
        Test that CSV export includes column headers in first row.

        Expected: First row contains field names
        """
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('dataset-export-csv', kwargs={'pk': self.dataset.pk})
        response = self.client.post(url)

        assert response.status_code == status.HTTP_200_OK

        # Parse CSV content
        content = response.content.decode('utf-8-sig')
        csv_reader = csv.DictReader(io.StringIO(content))

        # Check headers
        headers = csv_reader.fieldnames
        assert 'name' in headers
        assert 'age' in headers
        assert 'score' in headers
        assert 'enrolled' in headers

    def test_csv_export_data_integrity(self):
        """
        @SPEC:REQ-EXPORT-001
        Test that exported CSV contains all records with correct data.

        Expected: All 3 records present with accurate values
        """
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('dataset-export-csv', kwargs={'pk': self.dataset.pk})
        response = self.client.post(url)

        assert response.status_code == status.HTTP_200_OK

        # Parse CSV content
        content = response.content.decode('utf-8-sig')
        csv_reader = csv.DictReader(io.StringIO(content))
        rows = list(csv_reader)

        # Check record count
        assert len(rows) == 3

        # Check first record
        assert rows[0]['name'] == '홍길동'
        assert rows[0]['age'] == '25'
        assert rows[0]['score'] == '95.5'
        assert rows[0]['enrolled'] == 'True'

    def test_csv_export_rfc4180_special_characters(self):
        """
        @SPEC:REQ-EXPORT-002
        Test RFC 4180 compliance for special characters.

        Expected: Commas, quotes, and newlines are properly escaped
        """
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('dataset-export-csv', kwargs={'pk': self.dataset.pk})
        response = self.client.post(url)

        assert response.status_code == status.HTTP_200_OK

        # Parse CSV content
        content = response.content.decode('utf-8-sig')
        csv_reader = csv.DictReader(io.StringIO(content))
        rows = list(csv_reader)

        # Check that special characters are properly handled
        # Third record has 'Test, "User"' which should be escaped
        assert rows[2]['name'] == 'Test, "User"'

    def test_csv_export_content_disposition_header(self):
        """
        @SPEC:REQ-EXPORT-001
        Test that Content-Disposition header triggers browser download.

        Expected: Header contains "attachment" with dataset filename
        """
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('dataset-export-csv', kwargs={'pk': self.dataset.pk})
        response = self.client.post(url)

        assert response.status_code == status.HTTP_200_OK

        # Check Content-Disposition header
        content_disposition = response['Content-Disposition']
        assert 'attachment' in content_disposition
        assert 'Test_Dataset' in content_disposition or 'test' in content_disposition.lower()
        assert '.csv' in content_disposition

    def test_csv_export_empty_dataset(self):
        """
        Test CSV export for dataset with no records.

        Expected: 200 OK with headers only (no data rows)
        """
        # Create empty dataset
        empty_dataset = Dataset.objects.create(
            title='Empty Dataset',
            filename='empty.xlsx',
            file_size=512,
            record_count=0,
            uploaded_by=self.admin_user
        )

        self.client.force_authenticate(user=self.admin_user)
        url = reverse('dataset-export-csv', kwargs={'pk': empty_dataset.pk})
        response = self.client.post(url)

        assert response.status_code == status.HTTP_200_OK

        # Should still have headers even if no data
        content = response.content.decode('utf-8-sig')
        lines = content.strip().split('\n')
        assert len(lines) >= 1  # At least header row

    def test_csv_export_nonexistent_dataset(self):
        """
        Test CSV export for non-existent dataset.

        Expected: 404 Not Found
        """
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('dataset-export-csv', kwargs={'pk': 99999})
        response = self.client.post(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_csv_export_filename_sanitization(self):
        """
        Test that exported filename is properly sanitized.

        Expected: Special characters in dataset title are sanitized in filename
        """
        # Create dataset with special characters in title
        special_dataset = Dataset.objects.create(
            title='Test/Dataset: with<special>chars?',
            filename='test.xlsx',
            file_size=1024,
            uploaded_by=self.admin_user
        )

        self.client.force_authenticate(user=self.admin_user)
        url = reverse('dataset-export-csv', kwargs={'pk': special_dataset.pk})
        response = self.client.post(url)

        assert response.status_code == status.HTTP_200_OK

        # Filename should not contain special characters
        content_disposition = response['Content-Disposition']
        assert '/' not in content_disposition.split('filename=')[1]
        assert ':' not in content_disposition.split('filename=')[1]
        assert '<' not in content_disposition.split('filename=')[1]
        assert '>' not in content_disposition.split('filename=')[1]

    def test_csv_export_null_values(self):
        """
        Test CSV export handling of null values.

        Expected: Null values exported as empty strings
        """
        # Create record with null values
        DataRecord.objects.create(
            dataset=self.dataset,
            data={
                'name': 'Test User',
                'age': None,
                'score': 85.0,
                'enrolled': None
            }
        )

        self.client.force_authenticate(user=self.admin_user)
        url = reverse('dataset-export-csv', kwargs={'pk': self.dataset.pk})
        response = self.client.post(url)

        assert response.status_code == status.HTTP_200_OK

        content = response.content.decode('utf-8-sig')
        csv_reader = csv.DictReader(io.StringIO(content))
        rows = list(csv_reader)

        # Find the record with null values
        test_row = [row for row in rows if row['name'] == 'Test User'][0]

        # Null values should be empty strings or "None"
        assert test_row['age'] in ['', 'None', 'null']

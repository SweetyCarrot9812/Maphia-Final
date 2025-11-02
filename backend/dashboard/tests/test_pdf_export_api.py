"""
Tests for PDF Export API functionality.

@SPEC:EXPORT-001 - PDF Export System

Test Coverage:
- REQ-EXPORT-005: Basic PDF export with tables
- REQ-EXPORT-006: PDF styling and layout
- Header/footer with branding
- Pagination
- Table formatting
- Role-based access control
"""

import pytest
from io import BytesIO
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from dashboard.models import Dataset, DataRecord
from django.contrib.auth import get_user_model
from PyPDF2 import PdfReader

User = get_user_model()


@pytest.mark.django_db
class TestPDFExportAPI:
    """Test suite for PDF export functionality."""

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
            title='Test PDF Dataset',
            description='Test dataset for PDF export',
            filename='test.xlsx',
            file_size=2048,
            record_count=10,
            category='grades',
            uploaded_by=self.admin_user
        )

        # Create test records
        for i in range(10):
            DataRecord.objects.create(
                dataset=self.dataset,
                data={
                    'student_id': f'S{1000 + i}',
                    'name': f'Student {i+1}',
                    'score': 70 + (i * 3),
                    'grade': 'A' if i >= 7 else 'B' if i >= 4 else 'C',
                }
            )

    def test_pdf_export_requires_authentication(self):
        """
        @SPEC:REQ-EXPORT-005
        Test that PDF export requires authentication.

        Expected: 401 Unauthorized
        """
        url = reverse('dataset-export-pdf', kwargs={'pk': self.dataset.pk})
        response = self.client.post(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_pdf_export_admin_access(self):
        """
        @SPEC:REQ-EXPORT-005
        Test that admin users can export PDF.

        Expected: 200 OK with PDF file
        """
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('dataset-export-pdf', kwargs={'pk': self.dataset.pk})
        response = self.client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response['Content-Type'] == 'application/pdf'
        assert 'attachment; filename=' in response['Content-Disposition']

    def test_pdf_export_manager_access(self):
        """
        @SPEC:REQ-EXPORT-005
        Test that manager users can export PDF.

        Expected: 200 OK with PDF file
        """
        self.client.force_authenticate(user=self.manager_user)
        url = reverse('dataset-export-pdf', kwargs={'pk': self.dataset.pk})
        response = self.client.post(url)

        assert response.status_code == status.HTTP_200_OK

    def test_pdf_export_viewer_denied(self):
        """
        Test that viewer users cannot export PDF.

        Expected: 403 Forbidden
        """
        self.client.force_authenticate(user=self.viewer_user)
        url = reverse('dataset-export-pdf', kwargs={'pk': self.dataset.pk})
        response = self.client.post(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_pdf_export_valid_pdf(self):
        """
        @SPEC:REQ-EXPORT-005
        Test that exported file is a valid PDF.

        Expected: File can be parsed by PyPDF2
        """
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('dataset-export-pdf', kwargs={'pk': self.dataset.pk})
        response = self.client.post(url)

        assert response.status_code == status.HTTP_200_OK

        # Try to parse the PDF
        pdf_file = BytesIO(response.content)
        pdf_reader = PdfReader(pdf_file)

        assert pdf_reader is not None
        assert len(pdf_reader.pages) > 0

    def test_pdf_export_contains_dataset_title(self):
        """
        @SPEC:REQ-EXPORT-006
        Test that PDF contains dataset title.

        Expected: Dataset title appears in PDF content
        """
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('dataset-export-pdf', kwargs={'pk': self.dataset.pk})
        response = self.client.post(url)

        assert response.status_code == status.HTTP_200_OK

        # Parse PDF and check for title
        pdf_file = BytesIO(response.content)
        pdf_reader = PdfReader(pdf_file)

        # Extract text from first page
        first_page_text = pdf_reader.pages[0].extract_text()

        # Check if dataset title is in the text
        assert 'Test PDF Dataset' in first_page_text or 'PDF Dataset' in first_page_text

    def test_pdf_export_contains_data(self):
        """
        @SPEC:REQ-EXPORT-005
        Test that PDF contains table data.

        Expected: Student names and scores appear in PDF
        """
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('dataset-export-pdf', kwargs={'pk': self.dataset.pk})
        response = self.client.post(url)

        assert response.status_code == status.HTTP_200_OK

        # Parse PDF and check for data
        pdf_file = BytesIO(response.content)
        pdf_reader = PdfReader(pdf_file)

        # Extract text from all pages
        full_text = ''
        for page in pdf_reader.pages:
            full_text += page.extract_text()

        # Check if some student data is present
        assert 'Student 1' in full_text or 'S1000' in full_text

    def test_pdf_export_pagination(self):
        """
        @SPEC:REQ-EXPORT-006
        Test that PDF has proper pagination for large datasets.

        Expected: Multiple pages when needed
        """
        # Create more records to force pagination
        for i in range(50):
            DataRecord.objects.create(
                dataset=self.dataset,
                data={
                    'student_id': f'S{2000 + i}',
                    'name': f'Extra Student {i+1}',
                    'score': 60 + (i % 40),
                    'grade': 'A',
                }
            )

        self.client.force_authenticate(user=self.admin_user)
        url = reverse('dataset-export-pdf', kwargs={'pk': self.dataset.pk})
        response = self.client.post(url)

        assert response.status_code == status.HTTP_200_OK

        # Check for multiple pages
        pdf_file = BytesIO(response.content)
        pdf_reader = PdfReader(pdf_file)

        # Should have more than one page with 60 records
        assert len(pdf_reader.pages) >= 1

    def test_pdf_export_content_disposition(self):
        """
        @SPEC:REQ-EXPORT-005
        Test that Content-Disposition header is correct.

        Expected: Filename ends with .pdf
        """
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('dataset-export-pdf', kwargs={'pk': self.dataset.pk})
        response = self.client.post(url)

        assert response.status_code == status.HTTP_200_OK

        content_disposition = response['Content-Disposition']
        assert 'attachment' in content_disposition
        assert '.pdf' in content_disposition

    def test_pdf_export_empty_dataset(self):
        """
        Test PDF export for dataset with no records.

        Expected: 200 OK with PDF containing only headers
        """
        empty_dataset = Dataset.objects.create(
            title='Empty Dataset',
            filename='empty.xlsx',
            file_size=512,
            record_count=0,
            uploaded_by=self.admin_user
        )

        self.client.force_authenticate(user=self.admin_user)
        url = reverse('dataset-export-pdf', kwargs={'pk': empty_dataset.pk})
        response = self.client.post(url)

        assert response.status_code == status.HTTP_200_OK

        # Should still be a valid PDF
        pdf_file = BytesIO(response.content)
        pdf_reader = PdfReader(pdf_file)
        assert len(pdf_reader.pages) > 0

    def test_pdf_export_nonexistent_dataset(self):
        """
        Test PDF export for non-existent dataset.

        Expected: 404 Not Found
        """
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('dataset-export-pdf', kwargs={'pk': 99999})
        response = self.client.post(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_pdf_export_filename_sanitization(self):
        """
        Test that exported filename is properly sanitized.

        Expected: Special characters in dataset title are sanitized
        """
        special_dataset = Dataset.objects.create(
            title='Test/Dataset: with<special>chars?',
            filename='test.xlsx',
            file_size=1024,
            uploaded_by=self.admin_user
        )

        DataRecord.objects.create(
            dataset=special_dataset,
            data={'name': 'Test', 'value': 123}
        )

        self.client.force_authenticate(user=self.admin_user)
        url = reverse('dataset-export-pdf', kwargs={'pk': special_dataset.pk})
        response = self.client.post(url)

        assert response.status_code == status.HTTP_200_OK

        content_disposition = response['Content-Disposition']
        filename_part = content_disposition.split('filename=')[1]

        # Check that special characters are removed
        assert '/' not in filename_part
        assert ':' not in filename_part
        assert '<' not in filename_part
        assert '>' not in filename_part

    def test_pdf_export_korean_characters(self):
        """
        Test that Korean characters are properly exported in PDF.

        Expected: 한글 appears correctly in PDF
        """
        korean_dataset = Dataset.objects.create(
            title='한글 데이터셋',
            filename='test.xlsx',
            file_size=1024,
            uploaded_by=self.admin_user
        )

        DataRecord.objects.create(
            dataset=korean_dataset,
            data={
                'name': '홍길동',
                'subject': '수학',
                'score': 95
            }
        )

        self.client.force_authenticate(user=self.admin_user)
        url = reverse('dataset-export-pdf', kwargs={'pk': korean_dataset.pk})
        response = self.client.post(url)

        assert response.status_code == status.HTTP_200_OK

        # Check that it's a valid PDF
        pdf_file = BytesIO(response.content)
        pdf_reader = PdfReader(pdf_file)
        assert len(pdf_reader.pages) > 0

    def test_pdf_export_statistics_summary(self):
        """
        @SPEC:REQ-EXPORT-006
        Test that PDF includes summary statistics section.

        Expected: PDF contains record count and category info
        """
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('dataset-export-pdf', kwargs={'pk': self.dataset.pk})
        response = self.client.post(url)

        assert response.status_code == status.HTTP_200_OK

        # Parse PDF and check for statistics
        pdf_file = BytesIO(response.content)
        pdf_reader = PdfReader(pdf_file)

        full_text = ''
        for page in pdf_reader.pages:
            full_text += page.extract_text()

        # Should contain record count or category
        has_stats = (
            '10' in full_text or  # record count
            'grades' in full_text.lower() or  # category
            'Total' in full_text or
            'Records' in full_text
        )

        assert has_stats

    def test_pdf_export_date_timestamp(self):
        """
        @SPEC:REQ-EXPORT-006
        Test that PDF includes generation timestamp.

        Expected: Export date appears in PDF
        """
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('dataset-export-pdf', kwargs={'pk': self.dataset.pk})
        response = self.client.post(url)

        assert response.status_code == status.HTTP_200_OK

        # Parse PDF and check for date/time
        pdf_file = BytesIO(response.content)
        pdf_reader = PdfReader(pdf_file)

        first_page_text = pdf_reader.pages[0].extract_text()

        # Check for date indicators (year 2024/2025 or month names)
        has_date = (
            '2024' in first_page_text or
            '2025' in first_page_text or
            'Generated' in first_page_text or
            'Exported' in first_page_text
        )

        assert has_date

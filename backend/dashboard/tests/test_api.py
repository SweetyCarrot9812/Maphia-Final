"""
Tests for Dashboard API endpoints.

Tests REST API views and serializers.
"""

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from dashboard.models import Dataset, DataRecord
from io import BytesIO
from openpyxl import Workbook


@pytest.fixture
def api_client():
    """Create API client."""
    return APIClient()


@pytest.fixture
def test_user():
    """Create test user."""
    return User.objects.create_user(username='testuser', password='testpass')


@pytest.fixture
def authenticated_client(api_client, test_user):
    """Create authenticated API client."""
    api_client.force_authenticate(user=test_user)
    return api_client


@pytest.fixture
def sample_dataset(test_user):
    """Create sample dataset."""
    return Dataset.objects.create(
        title='Sample Dataset',
        description='Sample description',
        filename='sample.xlsx',
        file_size=1024,
        category='test',
        uploaded_by=test_user,
        record_count=5
    )


@pytest.fixture
def sample_excel_file():
    """Create sample Excel file."""
    workbook = Workbook()
    sheet = workbook.active

    # Add headers
    sheet['A1'] = 'Name'
    sheet['B1'] = 'Age'
    sheet['C1'] = 'Score'

    # Add data
    sheet['A2'] = 'John Doe'
    sheet['B2'] = 30
    sheet['C2'] = 85.5

    sheet['A3'] = 'Jane Smith'
    sheet['B3'] = 25
    sheet['C3'] = 92.0

    # Save to BytesIO
    file_io = BytesIO()
    workbook.save(file_io)
    file_io.seek(0)
    file_io.name = 'test.xlsx'

    return file_io


@pytest.mark.django_db
class TestDatasetAPI:
    """Test Dataset API endpoints."""

    def test_list_datasets(self, authenticated_client, sample_dataset):
        """Test listing datasets."""
        response = authenticated_client.get('/api/datasets/')

        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['title'] == 'Sample Dataset'

    def test_retrieve_dataset(self, authenticated_client, sample_dataset):
        """Test retrieving a single dataset."""
        response = authenticated_client.get(f'/api/datasets/{sample_dataset.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Sample Dataset'
        assert response.data['description'] == 'Sample description'
        assert response.data['category'] == 'test'

    def test_create_dataset_with_file(self, authenticated_client, sample_excel_file):
        """Test creating a dataset with file upload."""
        data = {
            'title': 'New Dataset',
            'description': 'New description',
            'category': 'test',
            'file': sample_excel_file
        }

        response = authenticated_client.post(
            '/api/datasets/',
            data,
            format='multipart'
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'New Dataset'
        assert response.data['record_count'] == 2  # 2 data rows

        # Verify records were created
        dataset = Dataset.objects.get(id=response.data['id'])
        assert dataset.records.count() == 2

    def test_update_dataset(self, authenticated_client, sample_dataset):
        """Test updating a dataset."""
        data = {
            'title': 'Updated Title',
            'description': 'Updated description'
        }

        response = authenticated_client.patch(
            f'/api/datasets/{sample_dataset.id}/',
            data,
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Updated Title'
        assert response.data['description'] == 'Updated description'

    def test_delete_dataset(self, authenticated_client, sample_dataset):
        """Test deleting a dataset."""
        dataset_id = sample_dataset.id

        response = authenticated_client.delete(f'/api/datasets/{dataset_id}/')

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Dataset.objects.filter(id=dataset_id).exists()

    def test_get_dataset_records(self, authenticated_client, sample_dataset, test_user):
        """Test getting records for a dataset."""
        # Create some records
        for i in range(3):
            DataRecord.objects.create(
                dataset=sample_dataset,
                data={'index': i, 'value': i * 10}
            )

        response = authenticated_client.get(
            f'/api/datasets/{sample_dataset.id}/records/'
        )

        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) == 3


@pytest.mark.django_db
class TestDataRecordAPI:
    """Test DataRecord API endpoints."""

    def test_list_records(self, authenticated_client, sample_dataset):
        """Test listing data records."""
        # Create records
        for i in range(5):
            DataRecord.objects.create(
                dataset=sample_dataset,
                data={'index': i}
            )

        response = authenticated_client.get('/api/records/')

        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) == 5

    def test_filter_records_by_dataset(self, authenticated_client, sample_dataset, test_user):
        """Test filtering records by dataset."""
        # Create records for sample dataset
        for i in range(3):
            DataRecord.objects.create(
                dataset=sample_dataset,
                data={'index': i}
            )

        # Create another dataset with records
        other_dataset = Dataset.objects.create(
            title='Other Dataset',
            filename='other.xlsx',
            file_size=2048,
            uploaded_by=test_user
        )
        for i in range(2):
            DataRecord.objects.create(
                dataset=other_dataset,
                data={'index': i}
            )

        response = authenticated_client.get(
            f'/api/records/?dataset_id={sample_dataset.id}'
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3

    def test_create_record(self, authenticated_client, sample_dataset):
        """Test creating a data record."""
        data = {
            'dataset': sample_dataset.id,
            'data': {'name': 'Test', 'value': 100}
        }

        response = authenticated_client.post(
            '/api/records/',
            data,
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['data']['name'] == 'Test'
        assert response.data['data']['value'] == 100


@pytest.mark.django_db
class TestStatisticsAPI:
    """Test Statistics API endpoints."""

    def test_overview_statistics(self, authenticated_client, test_user):
        """Test getting overview statistics."""
        # Create test data
        dataset1 = Dataset.objects.create(
            title='Dataset 1',
            filename='test1.xlsx',
            file_size=1024,
            category='cat1',
            uploaded_by=test_user,
            record_count=10
        )

        dataset2 = Dataset.objects.create(
            title='Dataset 2',
            filename='test2.xlsx',
            file_size=2048,
            category='cat2',
            uploaded_by=test_user,
            record_count=20
        )

        response = authenticated_client.get('/api/statistics/overview/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_datasets'] == 2
        assert response.data['total_records'] == 30
        assert response.data['total_size'] == 3072
        assert len(response.data['categories']) == 2
        assert len(response.data['recent_uploads']) == 2

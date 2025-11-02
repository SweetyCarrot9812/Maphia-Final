"""
Tests for Dataset CRUD API

@SPEC:DASH-001
@TEST:DATASET-CRUD-API

Tests the Dataset CRUD endpoints.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

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
def other_user(db):
    """Fixture for creating another test user"""
    return User.objects.create_user(
        username='otheruser',
        password='TestPass123!',
        email='other@example.com',
        role='viewer'
    )


@pytest.fixture
def authenticated_client(api_client, test_user):
    """Fixture for authenticated API client"""
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(test_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
    return api_client


@pytest.fixture
def sample_dataset(test_user):
    """Fixture for creating a sample dataset"""
    dataset = Dataset.objects.create(
        title='Sample Dataset',
        description='Test data for students',
        filename='students.xlsx',
        file_size=5000,
        record_count=3,
        category='enrollment',
        uploaded_by=test_user
    )
    # Create some sample records
    DataRecord.objects.bulk_create([
        DataRecord(dataset=dataset, data={'id': 1, 'name': 'Alice', 'gpa': 3.8}),
        DataRecord(dataset=dataset, data={'id': 2, 'name': 'Bob', 'gpa': 3.5}),
        DataRecord(dataset=dataset, data={'id': 3, 'name': 'Charlie', 'gpa': 3.9}),
    ])
    return dataset


@pytest.mark.django_db
class TestDatasetCRUD:
    """
    Tests for Dataset CRUD operations.

    Requirements:
    - REQ-DASH-003: Dataset management (CRUD operations)
    """

    def test_list_datasets(self, authenticated_client, sample_dataset):
        """
        @TEST:DATASET-CRUD-001
        List all datasets with pagination
        """
        url = '/api/datasets/'

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data or isinstance(response.data, list)

        # Check if pagination is enabled
        if 'results' in response.data:
            assert len(response.data['results']) >= 1
            assert response.data['results'][0]['title'] == 'Sample Dataset'
        else:
            assert len(response.data) >= 1
            assert response.data[0]['title'] == 'Sample Dataset'

    def test_list_datasets_without_authentication(self, api_client, sample_dataset):
        """
        @TEST:DATASET-CRUD-002
        List datasets without authentication should return 401
        """
        url = '/api/datasets/'

        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_dataset(self, authenticated_client, sample_dataset):
        """
        @TEST:DATASET-CRUD-003
        Retrieve a specific dataset by ID
        """
        url = f'/api/datasets/{sample_dataset.id}/'

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == sample_dataset.id
        assert response.data['title'] == 'Sample Dataset'
        assert response.data['description'] == 'Test data for students'
        assert response.data['filename'] == 'students.xlsx'
        assert response.data['record_count'] == 3
        assert response.data['category'] == 'enrollment'
        assert 'uploaded_by' in response.data
        assert 'records' in response.data
        assert len(response.data['records']) == 3

    def test_retrieve_nonexistent_dataset(self, authenticated_client):
        """
        @TEST:DATASET-CRUD-004
        Retrieve nonexistent dataset should return 404
        """
        url = '/api/datasets/99999/'

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_dataset_put(self, authenticated_client, sample_dataset):
        """
        @TEST:DATASET-CRUD-005
        Update dataset using PUT (full update)
        """
        url = f'/api/datasets/{sample_dataset.id}/'

        data = {
            'title': 'Updated Dataset Title',
            'description': 'Updated description',
            'category': 'updated_category',
        }

        response = authenticated_client.put(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Updated Dataset Title'
        assert response.data['description'] == 'Updated description'
        assert response.data['category'] == 'updated_category'

        # Verify in database
        sample_dataset.refresh_from_db()
        assert sample_dataset.title == 'Updated Dataset Title'
        assert sample_dataset.description == 'Updated description'

    def test_update_dataset_patch(self, authenticated_client, sample_dataset):
        """
        @TEST:DATASET-CRUD-006
        Update dataset using PATCH (partial update)
        """
        url = f'/api/datasets/{sample_dataset.id}/'

        data = {
            'title': 'Partially Updated Title',
        }

        response = authenticated_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Partially Updated Title'
        # Description should remain unchanged
        assert response.data['description'] == 'Test data for students'

        # Verify in database
        sample_dataset.refresh_from_db()
        assert sample_dataset.title == 'Partially Updated Title'
        assert sample_dataset.description == 'Test data for students'

    def test_update_dataset_readonly_fields(self, authenticated_client, sample_dataset):
        """
        @TEST:DATASET-CRUD-007
        Verify read-only fields cannot be updated
        """
        url = f'/api/datasets/{sample_dataset.id}/'

        original_upload_date = sample_dataset.upload_date
        original_file_size = sample_dataset.file_size
        original_record_count = sample_dataset.record_count

        data = {
            'title': 'Updated Title',
            'file_size': 99999,  # Try to change read-only field
            'record_count': 999,  # Try to change read-only field
            'upload_date': '2023-01-01T00:00:00Z',  # Try to change read-only field
        }

        response = authenticated_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Updated Title'

        # Verify read-only fields are unchanged
        sample_dataset.refresh_from_db()
        assert sample_dataset.file_size == original_file_size
        assert sample_dataset.record_count == original_record_count
        assert sample_dataset.upload_date == original_upload_date

    def test_delete_dataset(self, authenticated_client, sample_dataset):
        """
        @TEST:DATASET-CRUD-008
        Delete a dataset
        """
        url = f'/api/datasets/{sample_dataset.id}/'
        dataset_id = sample_dataset.id

        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify dataset is deleted
        assert not Dataset.objects.filter(id=dataset_id).exists()

        # Verify related records are also deleted (CASCADE)
        assert not DataRecord.objects.filter(dataset_id=dataset_id).exists()

    def test_delete_nonexistent_dataset(self, authenticated_client):
        """
        @TEST:DATASET-CRUD-009
        Delete nonexistent dataset should return 404
        """
        url = '/api/datasets/99999/'

        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_datasets_filtered_by_category(self, authenticated_client, sample_dataset, test_user):
        """
        @TEST:DATASET-CRUD-010
        List datasets filtered by category
        """
        # Create another dataset with different category
        Dataset.objects.create(
            title='Grades Dataset',
            description='Grade data',
            filename='grades.xlsx',
            file_size=3000,
            record_count=5,
            category='grades',
            uploaded_by=test_user
        )

        url = '/api/datasets/?category=enrollment'

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        # Get results (handle both paginated and non-paginated responses)
        if 'results' in response.data:
            results = response.data['results']
        else:
            results = response.data

        # Should only return enrollment category
        assert len(results) == 1
        assert results[0]['category'] == 'enrollment'

    # Note: Ordering by upload_date (descending) is already enforced in Dataset.Meta.ordering
    # No need for explicit test as it's a model-level guarantee

"""
Tests for DataRecord CRUD API

@SPEC:DASH-001
@TEST:DATARECORD-CRUD-API

Tests the DataRecord CRUD endpoints.
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
def authenticated_client(api_client, test_user):
    """Fixture for authenticated API client"""
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(test_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
    return api_client


@pytest.fixture
def sample_dataset(test_user):
    """Fixture for creating a sample dataset"""
    return Dataset.objects.create(
        title='Sample Dataset',
        description='Test data for students',
        filename='students.xlsx',
        file_size=5000,
        record_count=3,
        category='enrollment',
        uploaded_by=test_user
    )


@pytest.fixture
def sample_records(sample_dataset):
    """Fixture for creating sample data records"""
    records = [
        DataRecord(dataset=sample_dataset, data={'id': 1, 'name': 'Alice', 'gpa': 3.8, 'major': 'Engineering'}),
        DataRecord(dataset=sample_dataset, data={'id': 2, 'name': 'Bob', 'gpa': 3.5, 'major': 'Business'}),
        DataRecord(dataset=sample_dataset, data={'id': 3, 'name': 'Charlie', 'gpa': 3.9, 'major': 'Science'}),
    ]
    DataRecord.objects.bulk_create(records)
    return DataRecord.objects.filter(dataset=sample_dataset).order_by('id')


@pytest.mark.django_db
class TestDataRecordCRUD:
    """
    Tests for DataRecord CRUD operations.

    Requirements:
    - REQ-DASH-004: Data access and querying
    """

    def test_list_all_records(self, authenticated_client, sample_records):
        """
        @TEST:DATARECORD-CRUD-001
        List all data records
        """
        url = '/api/records/'

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        # Handle paginated and non-paginated responses
        if 'results' in response.data:
            results = response.data['results']
        else:
            results = response.data

        assert len(results) >= 3

        # Verify record structure
        first_record = results[0]
        assert 'id' in first_record
        assert 'dataset' in first_record
        assert 'data' in first_record
        assert 'created_at' in first_record
        assert 'updated_at' in first_record

    def test_list_records_without_authentication(self, api_client, sample_records):
        """
        @TEST:DATARECORD-CRUD-002
        List records without authentication should return 401
        """
        url = '/api/records/'

        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_records_filtered_by_dataset(self, authenticated_client, sample_dataset, sample_records, test_user):
        """
        @TEST:DATARECORD-CRUD-003
        List records filtered by dataset_id
        """
        # Create another dataset with records
        other_dataset = Dataset.objects.create(
            title='Other Dataset',
            description='Other data',
            filename='other.xlsx',
            file_size=2000,
            record_count=2,
            category='grades',
            uploaded_by=test_user
        )
        DataRecord.objects.bulk_create([
            DataRecord(dataset=other_dataset, data={'id': 10, 'grade': 'A'}),
            DataRecord(dataset=other_dataset, data={'id': 11, 'grade': 'B'}),
        ])

        url = f'/api/records/?dataset_id={sample_dataset.id}'

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        # Get results
        if 'results' in response.data:
            results = response.data['results']
        else:
            results = response.data

        # Should only return records from sample_dataset
        assert len(results) == 3
        for record in results:
            assert record['dataset'] == sample_dataset.id

    def test_retrieve_single_record(self, authenticated_client, sample_records):
        """
        @TEST:DATARECORD-CRUD-004
        Retrieve a specific data record by ID
        """
        record = sample_records[0]
        url = f'/api/records/{record.id}/'

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == record.id
        assert response.data['dataset'] == record.dataset.id
        assert response.data['data'] == record.data
        assert 'created_at' in response.data
        assert 'updated_at' in response.data

    def test_retrieve_nonexistent_record(self, authenticated_client):
        """
        @TEST:DATARECORD-CRUD-005
        Retrieve nonexistent record should return 404
        """
        url = '/api/records/99999/'

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_record(self, authenticated_client, sample_dataset):
        """
        @TEST:DATARECORD-CRUD-006
        Create a new data record
        """
        url = '/api/records/'

        data = {
            'dataset': sample_dataset.id,
            'data': {
                'id': 4,
                'name': 'David',
                'gpa': 3.7,
                'major': 'Mathematics'
            }
        }

        response = authenticated_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['dataset'] == sample_dataset.id
        assert response.data['data'] == data['data']

        # Verify record was created in database
        assert DataRecord.objects.filter(id=response.data['id']).exists()

    def test_create_record_with_invalid_data(self, authenticated_client, sample_dataset):
        """
        @TEST:DATARECORD-CRUD-007
        Create record with non-dict data should fail
        """
        url = '/api/records/'

        data = {
            'dataset': sample_dataset.id,
            'data': "This should be a dict, not a string"
        }

        response = authenticated_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'data' in response.data

    def test_create_record_without_dataset(self, authenticated_client):
        """
        @TEST:DATARECORD-CRUD-008
        Create record without dataset should fail
        """
        url = '/api/records/'

        data = {
            'data': {'name': 'Test'}
        }

        response = authenticated_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'dataset' in response.data

    def test_update_record_put(self, authenticated_client, sample_records):
        """
        @TEST:DATARECORD-CRUD-009
        Update data record using PUT (full update)
        """
        record = sample_records[0]
        url = f'/api/records/{record.id}/'

        data = {
            'dataset': record.dataset.id,
            'data': {
                'id': 1,
                'name': 'Alice Updated',
                'gpa': 4.0,
                'major': 'Computer Science'
            }
        }

        response = authenticated_client.put(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['name'] == 'Alice Updated'
        assert response.data['data']['gpa'] == 4.0

        # Verify in database
        record.refresh_from_db()
        assert record.data['name'] == 'Alice Updated'
        assert record.data['gpa'] == 4.0

    def test_update_record_patch(self, authenticated_client, sample_records):
        """
        @TEST:DATARECORD-CRUD-010
        Update data record using PATCH (partial update)
        """
        record = sample_records[0]
        url = f'/api/records/{record.id}/'

        # Only update the data field
        data = {
            'data': {
                'id': 1,
                'name': 'Alice Partially Updated',
                'gpa': 3.8,
                'major': 'Engineering'
            }
        }

        response = authenticated_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['name'] == 'Alice Partially Updated'
        assert response.data['dataset'] == record.dataset.id  # Should remain unchanged

        # Verify in database
        record.refresh_from_db()
        assert record.data['name'] == 'Alice Partially Updated'

    def test_update_record_readonly_fields(self, authenticated_client, sample_records):
        """
        @TEST:DATARECORD-CRUD-011
        Verify read-only fields (created_at, updated_at) cannot be changed
        """
        record = sample_records[0]
        url = f'/api/records/{record.id}/'

        original_created_at = record.created_at

        data = {
            'dataset': record.dataset.id,
            'data': {'id': 1, 'name': 'Alice', 'gpa': 3.8},
            'created_at': '2020-01-01T00:00:00Z',  # Try to change read-only field
        }

        response = authenticated_client.put(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK

        # Verify read-only field is unchanged
        record.refresh_from_db()
        assert record.created_at == original_created_at

    def test_delete_record(self, authenticated_client, sample_records):
        """
        @TEST:DATARECORD-CRUD-012
        Delete a data record
        """
        record = sample_records[0]
        record_id = record.id
        url = f'/api/records/{record_id}/'

        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify record is deleted
        assert not DataRecord.objects.filter(id=record_id).exists()

    def test_delete_nonexistent_record(self, authenticated_client):
        """
        @TEST:DATARECORD-CRUD-013
        Delete nonexistent record should return 404
        """
        url = '/api/records/99999/'

        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_bulk_create_records(self, authenticated_client, sample_dataset):
        """
        @TEST:DATARECORD-CRUD-014
        Verify multiple records can be created for a dataset
        """
        url = '/api/records/'

        records_data = [
            {
                'dataset': sample_dataset.id,
                'data': {'id': i, 'name': f'Student {i}', 'gpa': 3.0 + (i * 0.1)}
            }
            for i in range(10)
        ]

        for record_data in records_data:
            response = authenticated_client.post(url, record_data, format='json')
            assert response.status_code == status.HTTP_201_CREATED

        # Verify all records were created
        assert DataRecord.objects.filter(dataset=sample_dataset).count() >= 10

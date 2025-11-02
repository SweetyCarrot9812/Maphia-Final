"""
Tests for Analytics/Statistics API

@SPEC:DASH-001
@TEST:ANALYTICS-API

Tests the Statistics API endpoints for dashboard analytics.
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
def sample_datasets_with_records(test_user):
    """Fixture for creating multiple datasets with records for statistics"""
    # Create datasets in different categories
    datasets = []

    # Enrollment datasets
    for i in range(3):
        dataset = Dataset.objects.create(
            title=f'Enrollment Dataset {i+1}',
            description='Enrollment data',
            filename=f'enrollment_{i+1}.xlsx',
            file_size=5000 + (i * 1000),
            record_count=10 + (i * 5),
            category='enrollment',
            uploaded_by=test_user
        )
        datasets.append(dataset)

        # Create records for this dataset
        records = [
            DataRecord(dataset=dataset, data={'id': j, 'name': f'Student {j}'})
            for j in range(dataset.record_count)
        ]
        DataRecord.objects.bulk_create(records)

    # Grades datasets
    for i in range(2):
        dataset = Dataset.objects.create(
            title=f'Grades Dataset {i+1}',
            description='Grades data',
            filename=f'grades_{i+1}.xlsx',
            file_size=3000 + (i * 500),
            record_count=8 + (i * 3),
            category='grades',
            uploaded_by=test_user
        )
        datasets.append(dataset)

        # Create records for this dataset
        records = [
            DataRecord(dataset=dataset, data={'id': j, 'grade': 'A'})
            for j in range(dataset.record_count)
        ]
        DataRecord.objects.bulk_create(records)

    # Faculty dataset
    dataset = Dataset.objects.create(
        title='Faculty Dataset',
        description='Faculty data',
        filename='faculty.xlsx',
        file_size=2000,
        record_count=5,
        category='faculty',
        uploaded_by=test_user
    )
    datasets.append(dataset)

    # Create records for faculty dataset
    records = [
        DataRecord(dataset=dataset, data={'id': j, 'name': f'Professor {j}'})
        for j in range(dataset.record_count)
    ]
    DataRecord.objects.bulk_create(records)

    return datasets


@pytest.mark.django_db
class TestAnalyticsAPI:
    """
    Tests for Analytics/Statistics API endpoints.

    Requirements:
    - REQ-DASH-005: Dashboard overview and statistics
    """

    def test_get_overview_statistics(self, authenticated_client, sample_datasets_with_records):
        """
        @TEST:ANALYTICS-001
        Get dashboard overview statistics with aggregated data
        """
        url = '/api/statistics/overview/'

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        data = response.data

        # Verify structure
        assert 'total_datasets' in data
        assert 'total_records' in data
        assert 'total_size' in data
        assert 'categories' in data
        assert 'recent_uploads' in data

        # Verify aggregated values
        # 6 datasets total (3 enrollment + 2 grades + 1 faculty)
        assert data['total_datasets'] == 6

        # Total records: (10+15+20) + (8+11) + 5 = 69
        assert data['total_records'] == 69

        # Total size: (5000+6000+7000) + (3000+3500) + 2000 = 26500
        assert data['total_size'] == 26500

        # Categories should have 3 entries
        assert len(data['categories']) == 3

        # Recent uploads should have max 5 items
        assert len(data['recent_uploads']) <= 5

    def test_overview_statistics_category_breakdown(self, authenticated_client, sample_datasets_with_records):
        """
        @TEST:ANALYTICS-002
        Verify category breakdown in overview statistics
        """
        url = '/api/statistics/overview/'

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        categories = response.data['categories']

        # Should have 3 categories
        assert len(categories) == 3

        # Find category counts
        category_dict = {cat['category']: cat['count'] for cat in categories}

        assert 'enrollment' in category_dict
        assert 'grades' in category_dict
        assert 'faculty' in category_dict

        # Verify counts
        assert category_dict['enrollment'] == 3
        assert category_dict['grades'] == 2
        assert category_dict['faculty'] == 1

    def test_overview_statistics_recent_uploads(self, authenticated_client, sample_datasets_with_records):
        """
        @TEST:ANALYTICS-003
        Verify recent uploads list in overview statistics
        """
        url = '/api/statistics/overview/'

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        recent_uploads = response.data['recent_uploads']

        # Should return max 5 recent uploads
        assert len(recent_uploads) == 5

        # Each upload should have required fields
        for upload in recent_uploads:
            assert 'id' in upload
            assert 'title' in upload
            assert 'filename' in upload
            assert 'file_size' in upload
            assert 'record_count' in upload
            assert 'category' in upload
            assert 'upload_date' in upload
            assert 'uploaded_by' in upload

    def test_overview_statistics_without_authentication(self, api_client, sample_datasets_with_records):
        """
        @TEST:ANALYTICS-004
        Get overview statistics without authentication should return 401
        """
        url = '/api/statistics/overview/'

        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_overview_statistics_empty_database(self, authenticated_client):
        """
        @TEST:ANALYTICS-005
        Get overview statistics when database is empty
        """
        url = '/api/statistics/overview/'

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        data = response.data

        # All counts should be zero
        assert data['total_datasets'] == 0
        assert data['total_records'] == 0
        assert data['total_size'] == 0
        assert len(data['categories']) == 0
        assert len(data['recent_uploads']) == 0

    def test_overview_statistics_single_dataset(self, authenticated_client, test_user):
        """
        @TEST:ANALYTICS-006
        Get overview statistics with single dataset
        """
        # Create single dataset
        dataset = Dataset.objects.create(
            title='Single Dataset',
            description='Test data',
            filename='test.xlsx',
            file_size=1000,
            record_count=5,
            category='test',
            uploaded_by=test_user
        )

        # Create records
        records = [
            DataRecord(dataset=dataset, data={'id': i})
            for i in range(5)
        ]
        DataRecord.objects.bulk_create(records)

        url = '/api/statistics/overview/'

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        data = response.data

        assert data['total_datasets'] == 1
        assert data['total_records'] == 5
        assert data['total_size'] == 1000
        assert len(data['categories']) == 1
        assert data['categories'][0]['category'] == 'test'
        assert data['categories'][0]['count'] == 1

    def test_overview_statistics_ordering(self, authenticated_client, sample_datasets_with_records):
        """
        @TEST:ANALYTICS-007
        Verify categories are ordered by count (descending)
        """
        url = '/api/statistics/overview/'

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        categories = response.data['categories']

        # Categories should be ordered by count descending
        # enrollment (3) > grades (2) > faculty (1)
        assert categories[0]['category'] == 'enrollment'
        assert categories[0]['count'] == 3
        assert categories[1]['category'] == 'grades'
        assert categories[1]['count'] == 2
        assert categories[2]['category'] == 'faculty'
        assert categories[2]['count'] == 1

    def test_overview_statistics_data_types(self, authenticated_client, sample_datasets_with_records):
        """
        @TEST:ANALYTICS-008
        Verify correct data types in response
        """
        url = '/api/statistics/overview/'

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        data = response.data

        # Verify integer types
        assert isinstance(data['total_datasets'], int)
        assert isinstance(data['total_records'], int)
        assert isinstance(data['total_size'], int)

        # Verify list types
        assert isinstance(data['categories'], list)
        assert isinstance(data['recent_uploads'], list)

        # Verify category structure
        if len(data['categories']) > 0:
            category = data['categories'][0]
            assert isinstance(category['count'], int)
            assert isinstance(category['category'], str)

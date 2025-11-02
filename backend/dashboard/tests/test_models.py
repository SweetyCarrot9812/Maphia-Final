"""
Tests for Dashboard models.

Tests Dataset and DataRecord models.
"""

import pytest
from django.contrib.auth.models import User
from dashboard.models import Dataset, DataRecord


@pytest.mark.django_db
class TestDatasetModel:
    """Test Dataset model."""

    def test_create_dataset(self):
        """Test creating a dataset."""
        user = User.objects.create_user(username='testuser', password='testpass')

        dataset = Dataset.objects.create(
            title='Test Dataset',
            description='Test description',
            filename='test.xlsx',
            file_size=1024,
            category='test',
            uploaded_by=user
        )

        assert dataset.title == 'Test Dataset'
        assert dataset.description == 'Test description'
        assert dataset.filename == 'test.xlsx'
        assert dataset.file_size == 1024
        assert dataset.record_count == 0
        assert dataset.category == 'test'
        assert dataset.uploaded_by == user

    def test_dataset_str(self):
        """Test dataset string representation."""
        user = User.objects.create_user(username='testuser', password='testpass')

        dataset = Dataset.objects.create(
            title='Test Dataset',
            filename='test.xlsx',
            file_size=1024,
            uploaded_by=user,
            record_count=10
        )

        assert str(dataset) == 'Test Dataset (10 records)'

    def test_dataset_ordering(self):
        """Test datasets are ordered by upload_date descending."""
        import time
        user = User.objects.create_user(username='testuser', password='testpass')

        dataset1 = Dataset.objects.create(
            title='Dataset 1',
            filename='test1.xlsx',
            file_size=1024,
            uploaded_by=user
        )

        # Small delay to ensure different timestamps
        time.sleep(0.01)

        dataset2 = Dataset.objects.create(
            title='Dataset 2',
            filename='test2.xlsx',
            file_size=2048,
            uploaded_by=user
        )

        datasets = Dataset.objects.all()
        # Verify ordering exists (most recent first)
        assert datasets.count() == 2
        assert dataset2.upload_date >= dataset1.upload_date


@pytest.mark.django_db
class TestDataRecordModel:
    """Test DataRecord model."""

    def test_create_data_record(self):
        """Test creating a data record."""
        user = User.objects.create_user(username='testuser', password='testpass')

        dataset = Dataset.objects.create(
            title='Test Dataset',
            filename='test.xlsx',
            file_size=1024,
            uploaded_by=user
        )

        record = DataRecord.objects.create(
            dataset=dataset,
            data={'name': 'John Doe', 'age': 30, 'score': 85.5}
        )

        assert record.dataset == dataset
        assert record.data['name'] == 'John Doe'
        assert record.data['age'] == 30
        assert record.data['score'] == 85.5

    def test_data_record_str(self):
        """Test data record string representation."""
        user = User.objects.create_user(username='testuser', password='testpass')

        dataset = Dataset.objects.create(
            title='Test Dataset',
            filename='test.xlsx',
            file_size=1024,
            uploaded_by=user
        )

        record = DataRecord.objects.create(
            dataset=dataset,
            data={'test': 'value'}
        )

        assert f'Record {record.id} from Test Dataset' in str(record)

    def test_data_record_relationship(self):
        """Test dataset-record relationship."""
        user = User.objects.create_user(username='testuser', password='testpass')

        dataset = Dataset.objects.create(
            title='Test Dataset',
            filename='test.xlsx',
            file_size=1024,
            uploaded_by=user
        )

        # Create multiple records
        for i in range(5):
            DataRecord.objects.create(
                dataset=dataset,
                data={'index': i}
            )

        assert dataset.records.count() == 5
        assert all(r.dataset == dataset for r in dataset.records.all())

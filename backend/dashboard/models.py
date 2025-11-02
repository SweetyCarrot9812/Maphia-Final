"""
Dashboard models for University Data Visualization Dashboard.

Models:
- Dataset: Represents uploaded Excel files with metadata
- DataRecord: Stores individual records from datasets with flexible JSON schema
"""

from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator


class Dataset(models.Model):
    """
    Represents an uploaded dataset (Excel file) with metadata.

    Attributes:
        title: Human-readable title for the dataset
        description: Optional description of the dataset contents
        filename: Original filename of the uploaded Excel file
        file_size: Size of the file in bytes
        upload_date: Timestamp when the file was uploaded
        record_count: Number of data records in this dataset
        category: Category/type of data (e.g., 'enrollment', 'grades', 'faculty')
        uploaded_by: Reference to the User who uploaded this dataset
    """

    title = models.CharField(
        max_length=200,
        help_text="Dataset title"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description of dataset contents"
    )
    filename = models.CharField(
        max_length=255,
        help_text="Original filename of uploaded Excel file"
    )
    file_size = models.IntegerField(
        help_text="File size in bytes"
    )
    upload_date = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp of upload"
    )
    record_count = models.IntegerField(
        default=0,
        help_text="Number of records in this dataset"
    )
    category = models.CharField(
        max_length=100,
        blank=True,
        help_text="Category/type of data"
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='datasets',
        help_text="User who uploaded this dataset"
    )

    class Meta:
        ordering = ['-upload_date']
        indexes = [
            models.Index(fields=['-upload_date']),
            models.Index(fields=['category']),
            models.Index(fields=['uploaded_by']),
        ]

    def __str__(self):
        return f"{self.title} ({self.record_count} records)"


class DataRecord(models.Model):
    """
    Stores individual data records from uploaded datasets.

    Uses JSONField for flexible schema to accommodate varying Excel structures.

    Attributes:
        dataset: Foreign key to parent Dataset
        data: JSON object containing the actual data fields
        created_at: Timestamp when record was created
        updated_at: Timestamp of last update
    """

    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        related_name='records',
        help_text="Parent dataset"
    )
    data = models.JSONField(
        help_text="JSON object containing data fields"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Record creation timestamp"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last update timestamp"
    )

    class Meta:
        ordering = ['id']
        indexes = [
            models.Index(fields=['dataset', 'created_at']),
        ]

    def __str__(self):
        return f"Record {self.id} from {self.dataset.title}"

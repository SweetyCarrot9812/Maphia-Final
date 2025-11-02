"""
Dashboard serializers for University Data Visualization Dashboard.

Serializers:
- DataRecordSerializer: Serializes individual data records
- DatasetSerializer: Serializes dataset metadata with optional records
- DatasetListSerializer: Lightweight serializer for list views
- DatasetCreateSerializer: Handles dataset creation and file upload
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Dataset, DataRecord

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model (basic info only)."""

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')
        read_only_fields = ('id',)


class DataRecordSerializer(serializers.ModelSerializer):
    """
    Serializer for DataRecord model.

    Fields:
    - id: Record ID
    - dataset: Foreign key to parent dataset
    - data: JSON object with flexible schema
    - created_at: Creation timestamp
    - updated_at: Last update timestamp
    """

    class Meta:
        model = DataRecord
        fields = ('id', 'dataset', 'data', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_data(self, value):
        """Validate that data is a valid JSON object."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Data must be a JSON object (dict)")
        return value


class DatasetListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for Dataset list views.

    Includes basic metadata without related records for performance.
    """

    uploaded_by = UserSerializer(read_only=True)

    class Meta:
        model = Dataset
        fields = (
            'id',
            'title',
            'description',
            'filename',
            'file_size',
            'upload_date',
            'record_count',
            'category',
            'uploaded_by',
        )
        read_only_fields = (
            'id',
            'upload_date',
            'file_size',
            'record_count',
        )


class DatasetSerializer(serializers.ModelSerializer):
    """
    Full serializer for Dataset model.

    Includes all fields and optionally nested DataRecords.
    """

    uploaded_by = UserSerializer(read_only=True)
    records = DataRecordSerializer(many=True, read_only=True)

    class Meta:
        model = Dataset
        fields = (
            'id',
            'title',
            'description',
            'filename',
            'file_size',
            'upload_date',
            'record_count',
            'category',
            'uploaded_by',
            'records',
        )
        read_only_fields = (
            'id',
            'filename',
            'upload_date',
            'file_size',
            'record_count',
            'uploaded_by',
        )

    def validate_title(self, value):
        """Validate that title is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        return value.strip()

    def validate_category(self, value):
        """Validate and normalize category."""
        if value:
            return value.strip().lower()
        return value


class DatasetCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new Dataset instances.

    Handles file upload validation and metadata extraction.
    """

    file = serializers.FileField(write_only=True, required=True)

    class Meta:
        model = Dataset
        fields = (
            'id',
            'title',
            'description',
            'category',
            'file',
            'filename',
            'file_size',
            'upload_date',
            'record_count',
        )
        read_only_fields = (
            'id',
            'filename',
            'file_size',
            'upload_date',
            'record_count',
        )

    def validate_file(self, value):
        """
        Validate uploaded file.

        Checks:
        - File extension (must be .xlsx or .xls)
        - File size (max 10MB)
        """
        # Check file extension
        allowed_extensions = ['.xlsx', '.xls']
        file_ext = value.name.lower().split('.')[-1]
        if f'.{file_ext}' not in allowed_extensions:
            raise serializers.ValidationError(
                f"Invalid file format. Allowed formats: {', '.join(allowed_extensions)}"
            )

        # Check file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File too large. Maximum size: 10MB (current: {value.size / (1024 * 1024):.2f}MB)"
            )

        return value

    def validate_title(self, value):
        """Validate that title is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        return value.strip()

    def create(self, validated_data):
        """
        Create Dataset instance from uploaded file.

        Extracts metadata from file and stores filename/size.
        Actual file processing (parsing Excel) happens in the view.
        """
        uploaded_file = validated_data.pop('file')

        # Extract file metadata
        validated_data['filename'] = uploaded_file.name
        validated_data['file_size'] = uploaded_file.size

        # Create dataset instance
        dataset = Dataset.objects.create(**validated_data)

        return dataset


class DatasetStatisticsSerializer(serializers.Serializer):
    """
    Serializer for dataset statistics.

    Provides aggregated data for dashboard analytics.
    """

    total_datasets = serializers.IntegerField()
    total_records = serializers.IntegerField()
    total_size = serializers.IntegerField()
    categories = serializers.ListField(child=serializers.DictField())
    recent_uploads = serializers.ListField(child=serializers.DictField())

    class Meta:
        fields = (
            'total_datasets',
            'total_records',
            'total_size',
            'categories',
            'recent_uploads',
        )

"""
Dashboard admin configuration for University Data Visualization Dashboard.

Provides customized admin interfaces for Dataset and DataRecord models.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Dataset, DataRecord


class DataRecordInline(admin.TabularInline):
    """Inline admin for DataRecord within Dataset admin."""
    model = DataRecord
    extra = 0
    fields = ('data', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    can_delete = True


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    """
    Admin interface for Dataset model.

    Features:
    - List display with key metadata
    - Filters by upload date, category, uploader
    - Search by title, description, filename
    - Inline DataRecord viewing/editing
    - Custom file size display
    """

    list_display = (
        'title',
        'category',
        'record_count',
        'file_size_display',
        'uploaded_by',
        'upload_date',
    )

    list_filter = (
        'upload_date',
        'category',
        'uploaded_by',
    )

    search_fields = (
        'title',
        'description',
        'filename',
        'category',
    )

    readonly_fields = (
        'upload_date',
        'file_size_display',
    )

    fieldsets = (
        ('기본 정보', {
            'fields': ('title', 'description', 'category')
        }),
        ('파일 정보', {
            'fields': ('filename', 'file_size_display', 'record_count')
        }),
        ('메타데이터', {
            'fields': ('uploaded_by', 'upload_date'),
            'classes': ('collapse',)
        }),
    )

    inlines = [DataRecordInline]

    date_hierarchy = 'upload_date'

    ordering = ('-upload_date',)

    def file_size_display(self, obj):
        """Display file size in human-readable format."""
        size_bytes = obj.file_size

        if size_bytes < 1024:
            return f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

    file_size_display.short_description = '파일 크기'


@admin.register(DataRecord)
class DataRecordAdmin(admin.ModelAdmin):
    """
    Admin interface for DataRecord model.

    Features:
    - List display with dataset reference
    - Filters by dataset and creation date
    - Search by dataset title
    - JSON data viewing
    """

    list_display = (
        'id',
        'dataset_link',
        'created_at',
        'updated_at',
    )

    list_filter = (
        'dataset',
        'created_at',
    )

    search_fields = (
        'dataset__title',
        'data',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'dataset_link',
    )

    fieldsets = (
        ('데이터셋 정보', {
            'fields': ('dataset_link',)
        }),
        ('레코드 데이터', {
            'fields': ('data',)
        }),
        ('타임스탬프', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    date_hierarchy = 'created_at'

    ordering = ('-created_at',)

    def dataset_link(self, obj):
        """Display clickable link to parent dataset."""
        if obj.dataset:
            url = f"/admin/dashboard/dataset/{obj.dataset.id}/change/"
            return format_html(
                '<a href="{}">{}</a>',
                url,
                obj.dataset.title
            )
        return "-"

    dataset_link.short_description = '데이터셋'

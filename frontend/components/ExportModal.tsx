'use client';

/**
 * ExportModal Component
 *
 * Modal dialog for selecting export format and downloading dataset.
 * Supports CSV, Excel (XLSX), and PDF formats with progress indication.
 */

import React, { useState } from 'react';
import { saveAs } from 'file-saver';
import api from '@/lib/api';

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  datasetId: number;
  datasetTitle: string;
}

type ExportFormat = 'csv' | 'excel' | 'pdf';

interface FormatOption {
  value: ExportFormat;
  label: string;
  description: string;
  icon: string;
  extension: string;
}

const formatOptions: FormatOption[] = [
  {
    value: 'csv',
    label: 'CSV',
    description: 'Comma-separated values, compatible with Excel and spreadsheet applications',
    icon: '📄',
    extension: 'csv',
  },
  {
    value: 'excel',
    label: 'Excel (XLSX)',
    description: 'Microsoft Excel format with multiple sheets, styling, and statistics',
    icon: '📊',
    extension: 'xlsx',
  },
  {
    value: 'pdf',
    label: 'PDF',
    description: 'Portable document format with formatted tables and summary',
    icon: '📋',
    extension: 'pdf',
  },
];

const ExportModal: React.FC<ExportModalProps> = ({
  isOpen,
  onClose,
  datasetId,
  datasetTitle,
}) => {
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>('csv');
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleExport = async () => {
    setIsExporting(true);
    setError(null);

    try {
      let blob: Blob;
      let filename: string;

      // Sanitize filename
      const sanitizedTitle = datasetTitle
        .replace(/[^a-zA-Z0-9가-힣\s-]/g, '')
        .replace(/\s+/g, '_');

      switch (selectedFormat) {
        case 'csv':
          blob = await api.datasets.exportCSV(datasetId);
          filename = `${sanitizedTitle}.csv`;
          break;
        case 'excel':
          blob = await api.datasets.exportExcel(datasetId);
          filename = `${sanitizedTitle}.xlsx`;
          break;
        case 'pdf':
          blob = await api.datasets.exportPDF(datasetId);
          filename = `${sanitizedTitle}.pdf`;
          break;
        default:
          throw new Error('Invalid export format');
      }

      // Download file using file-saver
      saveAs(blob, filename);

      // Close modal after successful export
      setTimeout(() => {
        onClose();
        setIsExporting(false);
      }, 500);
    } catch (err: any) {
      console.error('Export error:', err);
      setError(
        err.response?.data?.error ||
        err.message ||
        'Failed to export dataset. Please try again.'
      );
      setIsExporting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-2xl font-bold text-gray-900">Export Dataset</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            aria-label="Close modal"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="p-6">
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {datasetTitle}
            </h3>
            <p className="text-sm text-gray-600">
              Select a format to export this dataset
            </p>
          </div>

          {/* Format Selection */}
          <div className="space-y-3 mb-6">
            {formatOptions.map((option) => (
              <label
                key={option.value}
                className={`
                  flex items-start p-4 border-2 rounded-lg cursor-pointer
                  transition-all duration-200
                  ${
                    selectedFormat === option.value
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300 bg-white'
                  }
                `}
              >
                <input
                  type="radio"
                  name="exportFormat"
                  value={option.value}
                  checked={selectedFormat === option.value}
                  onChange={(e) => setSelectedFormat(e.target.value as ExportFormat)}
                  className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500"
                  disabled={isExporting}
                />
                <div className="ml-3 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{option.icon}</span>
                    <span className="font-semibold text-gray-900">
                      {option.label}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    {option.description}
                  </p>
                </div>
              </label>
            ))}
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-start gap-2">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-5 w-5 text-red-600 mt-0.5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <p className="text-sm text-red-800">{error}</p>
              </div>
            </div>
          )}

          {/* Progress Indicator */}
          {isExporting && (
            <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                <p className="text-sm text-blue-800">
                  Preparing your export... This may take a moment.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t bg-gray-50">
          <button
            onClick={onClose}
            disabled={isExporting}
            className="
              px-4 py-2 text-gray-700 font-medium
              border border-gray-300 rounded-lg
              hover:bg-gray-100 transition-colors
              disabled:opacity-50 disabled:cursor-not-allowed
            "
          >
            Cancel
          </button>
          <button
            onClick={handleExport}
            disabled={isExporting}
            className="
              px-6 py-2 bg-blue-600 text-white font-medium rounded-lg
              hover:bg-blue-700 transition-colors
              disabled:opacity-50 disabled:cursor-not-allowed
              flex items-center gap-2
            "
          >
              {isExporting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Exporting...</span>
                </>
              ) : (
                <>
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-5 w-5"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                    />
                  </svg>
                  <span>Export & Download</span>
                </>
              )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ExportModal;

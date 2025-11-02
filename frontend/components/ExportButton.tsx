'use client';

/**
 * ExportButton Component
 *
 * Provides a button that opens an export modal for downloading dataset in multiple formats.
 * Supports CSV, Excel, and PDF export with progress indication.
 */

import React, { useState } from 'react';
import ExportModal from './ExportModal';

interface ExportButtonProps {
  datasetId: number;
  datasetTitle: string;
  className?: string;
}

const ExportButton: React.FC<ExportButtonProps> = ({
  datasetId,
  datasetTitle,
  className = ''
}) => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleOpenModal = () => {
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
  };

  return (
    <>
      <button
        onClick={handleOpenModal}
        className={`
          inline-flex items-center gap-2 px-4 py-2
          bg-blue-600 hover:bg-blue-700
          text-white font-medium rounded-lg
          transition-colors duration-200
          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
          disabled:opacity-50 disabled:cursor-not-allowed
          ${className}
        `}
        aria-label="Export dataset"
      >
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
        <span>Export Data</span>
      </button>

      <ExportModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        datasetId={datasetId}
        datasetTitle={datasetTitle}
      />
    </>
  );
};

export default ExportButton;

/**
 * Upload Page
 *
 * Excel file upload with TanStack Form.
 * Features: Validation, preview, progress tracking
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from '@tanstack/react-form';
import Layout from '@/components/Layout';
import api from '@/lib/api';
import { formatFileSize } from '@/lib/utils';

interface UploadFormData {
  title: string;
  description: string;
  category: string;
  file: File | null;
}

export default function UploadPage() {
  const router = useRouter();
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);

  const form = useForm<UploadFormData>({
    defaultValues: {
      title: '',
      description: '',
      category: '',
      file: null,
    },
    onSubmit: async ({ value }) => {
      if (!value.file) {
        setUploadError('파일을 선택해주세요.');
        return;
      }

      try {
        setUploading(true);
        setUploadError(null);
        setUploadProgress(0);

        // Simulate progress for better UX
        const progressInterval = setInterval(() => {
          setUploadProgress((prev) => {
            if (prev >= 90) {
              clearInterval(progressInterval);
              return 90;
            }
            return prev + 10;
          });
        }, 200);

        // Upload to backend
        const dataset = await api.datasets.uploadFile({
          file: value.file,
          title: value.title,
          description: value.description || undefined,
          category: value.category || undefined,
        });

        clearInterval(progressInterval);
        setUploadProgress(100);
        setUploadSuccess(true);

        // Redirect to dataset detail page after 1 second
        setTimeout(() => {
          router.push(`/datasets/${dataset.id}`);
        }, 1000);
      } catch (err: any) {
        console.error('Upload failed:', err);
        setUploadError(
          err.response?.data?.error ||
            err.response?.data?.file?.[0] ||
            '업로드에 실패했습니다. 다시 시도해주세요.'
        );
        setUploadProgress(0);
      } finally {
        setUploading(false);
      }
    },
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;

    if (file) {
      // Validate file type
      const validExtensions = ['.xlsx', '.xls'];
      const fileExtension = file.name.toLowerCase().slice(file.name.lastIndexOf('.'));

      if (!validExtensions.includes(fileExtension)) {
        setUploadError('Excel 파일만 업로드 가능합니다 (.xlsx, .xls)');
        form.setFieldValue('file', null);
        e.target.value = '';
        return;
      }

      // Validate file size (max 10MB)
      const maxSize = 10 * 1024 * 1024;
      if (file.size > maxSize) {
        setUploadError(`파일 크기는 10MB를 초과할 수 없습니다 (현재: ${formatFileSize(file.size)})`);
        form.setFieldValue('file', null);
        e.target.value = '';
        return;
      }

      setUploadError(null);
      form.setFieldValue('file', file);
    }
  };

  return (
    <Layout>
      <div className="px-4 sm:px-0 max-w-2xl mx-auto">
        {/* Page header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            데이터셋 업로드
          </h1>
          <p className="mt-2 text-sm text-gray-700">
            Excel 파일을 업로드하여 새로운 데이터셋을 생성하세요
          </p>
        </div>

        {/* Upload form */}
        <div className="bg-white rounded-lg shadow p-6">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              e.stopPropagation();
              form.handleSubmit();
            }}
          >
            <div className="space-y-6">
              {/* Title field */}
              <form.Field name="title">
                {(field) => (
                  <div>
                    <label
                      htmlFor="title"
                      className="block text-sm font-medium text-gray-700 mb-2"
                    >
                      제목 <span className="text-red-500">*</span>
                    </label>
                    <input
                      id="title"
                      type="text"
                      value={field.state.value}
                      onChange={(e) => field.handleChange(e.target.value)}
                      onBlur={field.handleBlur}
                      placeholder="데이터셋 제목을 입력하세요"
                      className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                    {field.state.meta.errors && (
                      <p className="mt-1 text-sm text-red-600">
                        {field.state.meta.errors}
                      </p>
                    )}
                  </div>
                )}
              </form.Field>

              {/* Description field */}
              <form.Field name="description">
                {(field) => (
                  <div>
                    <label
                      htmlFor="description"
                      className="block text-sm font-medium text-gray-700 mb-2"
                    >
                      설명
                    </label>
                    <textarea
                      id="description"
                      value={field.state.value}
                      onChange={(e) => field.handleChange(e.target.value)}
                      onBlur={field.handleBlur}
                      placeholder="데이터셋에 대한 설명을 입력하세요 (선택사항)"
                      rows={3}
                      className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                )}
              </form.Field>

              {/* Category field */}
              <form.Field name="category">
                {(field) => (
                  <div>
                    <label
                      htmlFor="category"
                      className="block text-sm font-medium text-gray-700 mb-2"
                    >
                      카테고리
                    </label>
                    <input
                      id="category"
                      type="text"
                      value={field.state.value}
                      onChange={(e) => field.handleChange(e.target.value)}
                      onBlur={field.handleBlur}
                      placeholder="예: 학생정보, 성적, 등록현황 (선택사항)"
                      className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                )}
              </form.Field>

              {/* File upload */}
              <form.Field name="file">
                {(field) => (
                  <div>
                    <label
                      htmlFor="file"
                      className="block text-sm font-medium text-gray-700 mb-2"
                    >
                      Excel 파일 <span className="text-red-500">*</span>
                    </label>
                    <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-lg hover:border-blue-400 transition-colors">
                      <div className="space-y-1 text-center">
                        <svg
                          className="mx-auto h-12 w-12 text-gray-400"
                          stroke="currentColor"
                          fill="none"
                          viewBox="0 0 48 48"
                          aria-hidden="true"
                        >
                          <path
                            d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                            strokeWidth={2}
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                        </svg>
                        <div className="flex text-sm text-gray-600">
                          <label
                            htmlFor="file"
                            className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500"
                          >
                            <span>파일 선택</span>
                            <input
                              id="file"
                              type="file"
                              accept=".xlsx,.xls"
                              onChange={handleFileChange}
                              className="sr-only"
                              required
                            />
                          </label>
                          <p className="pl-1">또는 드래그 앤 드롭</p>
                        </div>
                        <p className="text-xs text-gray-500">
                          XLSX, XLS 파일 (최대 10MB)
                        </p>
                      </div>
                    </div>

                    {/* File preview */}
                    {field.state.value && (
                      <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className="text-2xl">📄</div>
                            <div>
                              <p className="text-sm font-medium text-gray-900">
                                {field.state.value.name}
                              </p>
                              <p className="text-xs text-gray-500">
                                {formatFileSize(field.state.value.size)}
                              </p>
                            </div>
                          </div>
                          <button
                            type="button"
                            onClick={() => {
                              form.setFieldValue('file', null);
                              const input = document.getElementById('file') as HTMLInputElement;
                              if (input) input.value = '';
                            }}
                            className="text-red-600 hover:text-red-800"
                          >
                            ✕
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </form.Field>

              {/* Error message */}
              {uploadError && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <p className="text-red-800 text-sm">{uploadError}</p>
                </div>
              )}

              {/* Success message */}
              {uploadSuccess && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <p className="text-green-800 text-sm">
                    ✓ 업로드 성공! 데이터셋 페이지로 이동합니다...
                  </p>
                </div>
              )}

              {/* Upload progress */}
              {uploading && (
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm text-gray-700">업로드 중...</span>
                    <span className="text-sm font-medium text-blue-600">
                      {uploadProgress}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Submit button */}
              <div className="flex gap-4">
                <button
                  type="submit"
                  disabled={uploading || uploadSuccess}
                  className="flex-1 px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed font-medium"
                >
                  {uploading ? '업로드 중...' : '업로드'}
                </button>
                <button
                  type="button"
                  onClick={() => router.push('/datasets')}
                  disabled={uploading}
                  className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  취소
                </button>
              </div>
            </div>
          </form>
        </div>

        {/* Info section */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-blue-900 mb-2">📋 업로드 안내</h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Excel 파일 형식: .xlsx 또는 .xls</li>
            <li>• 최대 파일 크기: 10MB</li>
            <li>• 첫 번째 행은 컬럼 이름(헤더)으로 사용됩니다</li>
            <li>• 두 번째 행부터 데이터로 인식됩니다</li>
            <li>• 빈 셀은 null 값으로 저장됩니다</li>
            <li>• 업로드 후 자동으로 데이터가 파싱됩니다</li>
          </ul>
        </div>
      </div>
    </Layout>
  );
}

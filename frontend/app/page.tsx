/**
 * Home Page - Dashboard Overview
 *
 * Displays statistics and recent datasets.
 */

'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import Layout from '@/components/Layout';
import api, { DatasetStatistics } from '@/lib/api';
import { formatFileSize, formatNumber } from '@/lib/utils';

export default function Home() {
  const [statistics, setStatistics] = useState<DatasetStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStatistics();
  }, []);

  const fetchStatistics = async () => {
    try {
      setLoading(true);
      const data = await api.statistics.overview();
      setStatistics(data);
    } catch (err) {
      console.error('Failed to fetch statistics:', err);
      setError('통계 데이터를 불러올 수 없습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="px-4 sm:px-0">
        {/* Page header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            대시보드 개요
          </h1>
          <p className="mt-2 text-sm text-gray-700">
            데이터셋 현황 및 통계를 확인하세요
          </p>
        </div>

        {/* Statistics cards */}
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-pulse text-gray-500">로딩 중...</div>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">{error}</p>
            <button
              onClick={fetchStatistics}
              className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
            >
              다시 시도
            </button>
          </div>
        ) : statistics ? (
          <>
            {/* Overview cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0 bg-blue-500 rounded-md p-3">
                    <span className="text-2xl">📊</span>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        전체 데이터셋
                      </dt>
                      <dd className="text-3xl font-semibold text-gray-900">
                        {formatNumber(statistics.total_datasets)}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0 bg-green-500 rounded-md p-3">
                    <span className="text-2xl">📝</span>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        전체 레코드
                      </dt>
                      <dd className="text-3xl font-semibold text-gray-900">
                        {formatNumber(statistics.total_records)}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0 bg-purple-500 rounded-md p-3">
                    <span className="text-2xl">💾</span>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        전체 크기
                      </dt>
                      <dd className="text-3xl font-semibold text-gray-900">
                        {formatFileSize(statistics.total_size)}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            {/* Category breakdown */}
            {statistics.categories.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6 mb-8">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  카테고리별 분포
                </h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {statistics.categories.map((category) => (
                    <div
                      key={category.category}
                      className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
                    >
                      <p className="text-sm text-gray-500 mb-1">
                        {category.category || '미분류'}
                      </p>
                      <p className="text-2xl font-bold text-gray-900">
                        {category.count}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recent uploads */}
            {statistics.recent_uploads.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-lg font-semibold text-gray-900">
                    최근 업로드
                  </h2>
                  <Link
                    href="/datasets"
                    className="text-sm text-blue-600 hover:text-blue-800"
                  >
                    전체 보기 →
                  </Link>
                </div>
                <div className="space-y-3">
                  {statistics.recent_uploads.map((dataset) => (
                    <div
                      key={dataset.id}
                      className="flex justify-between items-center p-3 border rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900">
                          {dataset.title}
                        </h3>
                        <p className="text-sm text-gray-500">
                          {dataset.record_count}개 레코드 •{' '}
                          {formatFileSize(dataset.file_size)} •{' '}
                          {dataset.category || '미분류'}
                        </p>
                      </div>
                      <Link
                        href={`/datasets/${dataset.id}`}
                        className="ml-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                      >
                        보기
                      </Link>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Quick actions */}
            <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
              <Link
                href="/upload"
                className="bg-blue-500 text-white rounded-lg p-6 hover:bg-blue-600 transition-colors shadow"
              >
                <h3 className="text-xl font-semibold mb-2">📤 새 데이터 업로드</h3>
                <p className="text-blue-100">
                  Excel 파일을 업로드하여 새로운 데이터셋을 생성하세요
                </p>
              </Link>

              <Link
                href="/analytics"
                className="bg-green-500 text-white rounded-lg p-6 hover:bg-green-600 transition-colors shadow"
              >
                <h3 className="text-xl font-semibold mb-2">📈 데이터 분석</h3>
                <p className="text-green-100">
                  차트와 그래프로 데이터를 시각화하고 분석하세요
                </p>
              </Link>
            </div>
          </>
        ) : null}
      </div>
    </Layout>
  );
}

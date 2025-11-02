/**
 * Dataset Detail Page
 *
 * Displays dataset metadata and all records with TanStack Table.
 * Features: sorting, filtering, pagination
 */

'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  flexRender,
  createColumnHelper,
  SortingState,
  ColumnFiltersState,
} from '@tanstack/react-table';
import Layout from '@/components/Layout';
import ExportButton from '@/components/ExportButton';
import api, { Dataset, DataRecord } from '@/lib/api';
import { formatFileSize, formatDate, formatNumber } from '@/lib/utils';

export default function DatasetDetailPage() {
  const params = useParams();
  const router = useRouter();
  const datasetId = Number(params.id);

  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [records, setRecords] = useState<DataRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [globalFilter, setGlobalFilter] = useState('');

  useEffect(() => {
    if (datasetId) {
      fetchDataset();
    }
  }, [datasetId]);

  const fetchDataset = async () => {
    try {
      setLoading(true);

      // Fetch dataset metadata
      const datasetData = await api.datasets.get(datasetId);
      setDataset(datasetData);

      // Fetch records
      const recordsData = await api.datasets.getRecords(datasetId, {
        page_size: 1000,
      });
      setRecords(recordsData.results);
    } catch (err) {
      console.error('Failed to fetch dataset:', err);
      setError('데이터셋을 불러올 수 없습니다.');
    } finally {
      setLoading(false);
    }
  };

  // Dynamically create columns based on first record's data
  const columns = records.length > 0
    ? Object.keys(records[0].data).map((key) => {
        const columnHelper = createColumnHelper<DataRecord>();
        return columnHelper.accessor((row) => row.data[key], {
          id: key,
          header: key,
          cell: (info) => {
            const value = info.getValue();
            if (value === null || value === undefined) {
              return <span className="text-gray-400 italic">-</span>;
            }
            return <span className="text-gray-700">{String(value)}</span>;
          },
        });
      })
    : [];

  const table = useReactTable({
    data: records,
    columns,
    state: {
      sorting,
      columnFilters,
      globalFilter,
    },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: {
      pagination: {
        pageSize: 20,
      },
    },
  });

  const handleDelete = async () => {
    if (!confirm('정말로 이 데이터셋을 삭제하시겠습니까? 모든 레코드도 함께 삭제됩니다.')) {
      return;
    }

    try {
      await api.datasets.delete(datasetId);
      router.push('/datasets');
    } catch (err) {
      console.error('Failed to delete dataset:', err);
      alert('데이터셋 삭제에 실패했습니다.');
    }
  };

  return (
    <Layout>
      <div className="px-4 sm:px-0">
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-pulse text-gray-500">로딩 중...</div>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">{error}</p>
            <button
              onClick={fetchDataset}
              className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
            >
              다시 시도
            </button>
          </div>
        ) : dataset ? (
          <>
            {/* Back button */}
            <div className="mb-4">
              <Link
                href="/datasets"
                className="text-blue-600 hover:text-blue-800 flex items-center gap-2"
              >
                ← 목록으로 돌아가기
              </Link>
            </div>

            {/* Dataset metadata */}
            <div className="bg-white rounded-lg shadow p-6 mb-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900">
                    {dataset.title}
                  </h1>
                  <p className="mt-2 text-gray-600">{dataset.description}</p>
                </div>
                <div className="flex gap-3">
                  <ExportButton
                    datasetId={dataset.id}
                    datasetTitle={dataset.title}
                  />
                  <button
                    onClick={handleDelete}
                    className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
                  >
                    🗑️ 삭제
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm text-gray-500">카테고리</p>
                  <p className="font-medium text-gray-900">
                    {dataset.category || '미분류'}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">레코드 수</p>
                  <p className="font-medium text-gray-900">
                    {formatNumber(dataset.record_count)}개
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">파일 크기</p>
                  <p className="font-medium text-gray-900">
                    {formatFileSize(dataset.file_size)}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">업로드 날짜</p>
                  <p className="font-medium text-gray-900">
                    {formatDate(dataset.upload_date)}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">파일명</p>
                  <p className="font-medium text-gray-900">{dataset.filename}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">업로더</p>
                  <p className="font-medium text-gray-900">
                    {dataset.uploaded_by.username}
                  </p>
                </div>
              </div>
            </div>

            {/* Records table */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-4 border-b flex justify-between items-center">
                <h2 className="text-xl font-semibold text-gray-900">
                  데이터 레코드
                </h2>
                <input
                  type="text"
                  value={globalFilter ?? ''}
                  onChange={(e) => setGlobalFilter(e.target.value)}
                  placeholder="검색..."
                  className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {records.length === 0 ? (
                <div className="p-12 text-center">
                  <div className="text-6xl mb-4">📄</div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    레코드가 없습니다
                  </h3>
                  <p className="text-gray-600">
                    이 데이터셋에는 아직 레코드가 없습니다.
                  </p>
                </div>
              ) : (
                <>
                  {/* Table */}
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        {table.getHeaderGroups().map((headerGroup) => (
                          <tr key={headerGroup.id}>
                            {headerGroup.headers.map((header) => (
                              <th
                                key={header.id}
                                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                                onClick={header.column.getToggleSortingHandler()}
                              >
                                <div className="flex items-center gap-2">
                                  {flexRender(
                                    header.column.columnDef.header,
                                    header.getContext()
                                  )}
                                  {header.column.getIsSorted() && (
                                    <span>
                                      {header.column.getIsSorted() === 'asc'
                                        ? '↑'
                                        : '↓'}
                                    </span>
                                  )}
                                </div>
                              </th>
                            ))}
                          </tr>
                        ))}
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {table.getRowModel().rows.map((row) => (
                          <tr key={row.id} className="hover:bg-gray-50">
                            {row.getVisibleCells().map((cell) => (
                              <td
                                key={cell.id}
                                className="px-6 py-4 whitespace-nowrap text-sm"
                              >
                                {flexRender(
                                  cell.column.columnDef.cell,
                                  cell.getContext()
                                )}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Pagination */}
                  <div className="px-6 py-4 border-t flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => table.setPageIndex(0)}
                        disabled={!table.getCanPreviousPage()}
                        className="px-3 py-1 border rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        ⏮
                      </button>
                      <button
                        onClick={() => table.previousPage()}
                        disabled={!table.getCanPreviousPage()}
                        className="px-3 py-1 border rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        ◀
                      </button>
                      <button
                        onClick={() => table.nextPage()}
                        disabled={!table.getCanNextPage()}
                        className="px-3 py-1 border rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        ▶
                      </button>
                      <button
                        onClick={() =>
                          table.setPageIndex(table.getPageCount() - 1)
                        }
                        disabled={!table.getCanNextPage()}
                        className="px-3 py-1 border rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        ⏭
                      </button>
                    </div>

                    <div className="flex items-center gap-4">
                      <span className="text-sm text-gray-700">
                        페이지{' '}
                        <strong>
                          {table.getState().pagination.pageIndex + 1} /{' '}
                          {table.getPageCount()}
                        </strong>
                      </span>
                      <select
                        value={table.getState().pagination.pageSize}
                        onChange={(e) =>
                          table.setPageSize(Number(e.target.value))
                        }
                        className="border rounded px-2 py-1 text-sm"
                      >
                        {[20, 50, 100].map((pageSize) => (
                          <option key={pageSize} value={pageSize}>
                            {pageSize}개씩 보기
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {/* Stats */}
                  <div className="px-6 py-3 bg-gray-50 text-sm text-gray-500">
                    전체 {records.length}개 레코드 중{' '}
                    {table.getFilteredRowModel().rows.length}개 표시
                  </div>
                </>
              )}
            </div>
          </>
        ) : null}
      </div>
    </Layout>
  );
}

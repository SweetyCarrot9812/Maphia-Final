/**
 * Datasets List Page
 *
 * Displays all datasets with TanStack Table.
 * Features: sorting, filtering, pagination
 */

'use client';

import { useEffect, useState } from 'react';
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
import api, { Dataset } from '@/lib/api';
import { formatFileSize, formatDate, formatNumber } from '@/lib/utils';

const columnHelper = createColumnHelper<Dataset>();

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [globalFilter, setGlobalFilter] = useState('');

  useEffect(() => {
    fetchDatasets();
  }, []);

  const fetchDatasets = async () => {
    try {
      setLoading(true);
      const response = await api.datasets.list({ page_size: 100 });
      setDatasets(response.results);
    } catch (err) {
      console.error('Failed to fetch datasets:', err);
      setError('데이터셋을 불러올 수 없습니다.');
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    columnHelper.accessor('title', {
      header: '제목',
      cell: (info) => (
        <Link
          href={`/datasets/${info.row.original.id}`}
          className="text-blue-600 hover:text-blue-800 font-medium"
        >
          {info.getValue()}
        </Link>
      ),
    }),
    columnHelper.accessor('category', {
      header: '카테고리',
      cell: (info) => (
        <span className="px-2 py-1 text-xs font-medium bg-gray-100 rounded-full">
          {info.getValue() || '미분류'}
        </span>
      ),
    }),
    columnHelper.accessor('record_count', {
      header: '레코드 수',
      cell: (info) => (
        <span className="text-gray-700">{formatNumber(info.getValue())}</span>
      ),
    }),
    columnHelper.accessor('file_size', {
      header: '파일 크기',
      cell: (info) => (
        <span className="text-gray-700">{formatFileSize(info.getValue())}</span>
      ),
    }),
    columnHelper.accessor('uploaded_by', {
      header: '업로더',
      cell: (info) => (
        <span className="text-gray-700">{info.getValue().username}</span>
      ),
    }),
    columnHelper.accessor('upload_date', {
      header: '업로드 날짜',
      cell: (info) => (
        <span className="text-gray-500 text-sm">
          {formatDate(info.getValue())}
        </span>
      ),
    }),
    columnHelper.display({
      id: 'actions',
      header: '작업',
      cell: (info) => (
        <div className="flex gap-2">
          <Link
            href={`/datasets/${info.row.original.id}`}
            className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            보기
          </Link>
          <button
            onClick={() => handleDelete(info.row.original.id)}
            className="px-3 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600"
          >
            삭제
          </button>
        </div>
      ),
    }),
  ];

  const table = useReactTable({
    data: datasets,
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
        pageSize: 10,
      },
    },
  });

  const handleDelete = async (id: number) => {
    if (!confirm('정말로 이 데이터셋을 삭제하시겠습니까?')) {
      return;
    }

    try {
      await api.datasets.delete(id);
      setDatasets(datasets.filter((d) => d.id !== id));
    } catch (err) {
      console.error('Failed to delete dataset:', err);
      alert('데이터셋 삭제에 실패했습니다.');
    }
  };

  return (
    <Layout>
      <div className="px-4 sm:px-0">
        {/* Page header */}
        <div className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">데이터셋 목록</h1>
            <p className="mt-2 text-sm text-gray-700">
              업로드된 모든 데이터셋을 확인하고 관리하세요
            </p>
          </div>
          <Link
            href="/upload"
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            📤 새 데이터셋 업로드
          </Link>
        </div>

        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-pulse text-gray-500">로딩 중...</div>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">{error}</p>
            <button
              onClick={fetchDatasets}
              className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
            >
              다시 시도
            </button>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow">
            {/* Search bar */}
            <div className="p-4 border-b">
              <input
                type="text"
                value={globalFilter ?? ''}
                onChange={(e) => setGlobalFilter(e.target.value)}
                placeholder="검색..."
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

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
                  onClick={() => table.setPageIndex(table.getPageCount() - 1)}
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
                  onChange={(e) => table.setPageSize(Number(e.target.value))}
                  className="border rounded px-2 py-1 text-sm"
                >
                  {[10, 20, 50].map((pageSize) => (
                    <option key={pageSize} value={pageSize}>
                      {pageSize}개씩 보기
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        )}

        {/* Stats */}
        {!loading && !error && datasets.length > 0 && (
          <div className="mt-4 text-sm text-gray-500">
            전체 {datasets.length}개 데이터셋 중{' '}
            {table.getFilteredRowModel().rows.length}개 표시
          </div>
        )}

        {/* Empty state */}
        {!loading && !error && datasets.length === 0 && (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <div className="text-6xl mb-4">📊</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              데이터셋이 없습니다
            </h3>
            <p className="text-gray-600 mb-6">
              첫 번째 데이터셋을 업로드하여 시작하세요
            </p>
            <Link
              href="/upload"
              className="inline-block px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
            >
              📤 데이터셋 업로드하기
            </Link>
          </div>
        )}
      </div>
    </Layout>
  );
}

/**
 * Analytics Page
 *
 * Data visualization with Recharts.
 * Features: Multiple chart types, dataset selection, field mapping
 */

'use client';

import { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import api, { Dataset, DataRecord } from '@/lib/api';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';

type ChartType = 'bar' | 'line' | 'pie' | 'area';

const COLORS = [
  '#3B82F6', // blue-500
  '#10B981', // green-500
  '#F59E0B', // amber-500
  '#EF4444', // red-500
  '#8B5CF6', // violet-500
  '#EC4899', // pink-500
  '#14B8A6', // teal-500
  '#F97316', // orange-500
];

export default function AnalyticsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | null>(null);
  const [records, setRecords] = useState<DataRecord[]>([]);
  const [fields, setFields] = useState<string[]>([]);
  const [chartType, setChartType] = useState<ChartType>('bar');
  const [xField, setXField] = useState<string>('');
  const [yField, setYField] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDatasets();
  }, []);

  useEffect(() => {
    if (selectedDatasetId) {
      fetchRecords(selectedDatasetId);
    }
  }, [selectedDatasetId]);

  const fetchDatasets = async () => {
    try {
      const response = await api.datasets.list({ page_size: 100 });
      setDatasets(response.results);
    } catch (err) {
      console.error('Failed to fetch datasets:', err);
      setError('데이터셋을 불러올 수 없습니다.');
    }
  };

  const fetchRecords = async (datasetId: number) => {
    try {
      setLoading(true);
      const response = await api.datasets.getRecords(datasetId, {
        page_size: 1000,
      });
      setRecords(response.results);

      // Extract field names from first record
      if (response.results.length > 0) {
        const fieldNames = Object.keys(response.results[0].data);
        setFields(fieldNames);

        // Auto-select first two fields
        if (fieldNames.length >= 2) {
          setXField(fieldNames[0]);
          setYField(fieldNames[1]);
        }
      }
    } catch (err) {
      console.error('Failed to fetch records:', err);
      setError('레코드를 불러올 수 없습니다.');
    } finally {
      setLoading(false);
    }
  };

  // Prepare chart data
  const chartData = records.map((record) => ({
    name: String(record.data[xField] || ''),
    value: Number(record.data[yField]) || 0,
  }));

  // Aggregate data for better visualization (group by name and sum values)
  const aggregatedData = chartData.reduce((acc, item) => {
    const existing = acc.find((d) => d.name === item.name);
    if (existing) {
      existing.value += item.value;
    } else {
      acc.push({ ...item });
    }
    return acc;
  }, [] as { name: string; value: number }[]);

  const renderChart = () => {
    if (!xField || !yField || aggregatedData.length === 0) {
      return (
        <div className="flex flex-col items-center justify-center h-96 text-gray-500">
          <div className="text-6xl mb-4">📊</div>
          <p className="text-lg">차트를 생성하려면 데이터셋과 필드를 선택하세요</p>
        </div>
      );
    }

    const commonProps = {
      width: 500,
      height: 400,
      data: aggregatedData,
    };

    switch (chartType) {
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={aggregatedData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="value" fill="#3B82F6" name={yField} />
            </BarChart>
          </ResponsiveContainer>
        );

      case 'line':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={aggregatedData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#3B82F6"
                strokeWidth={2}
                name={yField}
              />
            </LineChart>
          </ResponsiveContainer>
        );

      case 'area':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={aggregatedData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#3B82F6"
                fill="#3B82F6"
                fillOpacity={0.6}
                name={yField}
              />
            </AreaChart>
          </ResponsiveContainer>
        );

      case 'pie':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <PieChart>
              <Pie
                data={aggregatedData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={120}
                label={(entry) => `${entry.name}: ${entry.value}`}
              >
                {aggregatedData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={COLORS[index % COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        );

      default:
        return null;
    }
  };

  return (
    <Layout>
      <div className="px-4 sm:px-0">
        {/* Page header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">데이터 분석</h1>
          <p className="mt-2 text-sm text-gray-700">
            차트로 데이터를 시각화하고 분석하세요
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Control panel */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6 space-y-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                차트 설정
              </h2>

              {/* Dataset selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  데이터셋 선택
                </label>
                <select
                  value={selectedDatasetId || ''}
                  onChange={(e) => setSelectedDatasetId(Number(e.target.value))}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">선택하세요...</option>
                  {datasets.map((dataset) => (
                    <option key={dataset.id} value={dataset.id}>
                      {dataset.title}
                    </option>
                  ))}
                </select>
              </div>

              {/* Chart type selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  차트 타입
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { type: 'bar', label: '막대', icon: '📊' },
                    { type: 'line', label: '선', icon: '📈' },
                    { type: 'area', label: '영역', icon: '📉' },
                    { type: 'pie', label: '파이', icon: '🥧' },
                  ].map((item) => (
                    <button
                      key={item.type}
                      onClick={() => setChartType(item.type as ChartType)}
                      className={`px-3 py-2 rounded-lg border transition-colors ${
                        chartType === item.type
                          ? 'bg-blue-500 text-white border-blue-500'
                          : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      <div className="text-2xl mb-1">{item.icon}</div>
                      <div className="text-xs">{item.label}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* X-axis field */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  X축 (카테고리)
                </label>
                <select
                  value={xField}
                  onChange={(e) => setXField(e.target.value)}
                  disabled={fields.length === 0}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                >
                  <option value="">선택하세요...</option>
                  {fields.map((field) => (
                    <option key={field} value={field}>
                      {field}
                    </option>
                  ))}
                </select>
              </div>

              {/* Y-axis field */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Y축 (값)
                </label>
                <select
                  value={yField}
                  onChange={(e) => setYField(e.target.value)}
                  disabled={fields.length === 0}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                >
                  <option value="">선택하세요...</option>
                  {fields.map((field) => (
                    <option key={field} value={field}>
                      {field}
                    </option>
                  ))}
                </select>
              </div>

              {/* Stats */}
              {records.length > 0 && (
                <div className="pt-4 border-t">
                  <div className="text-sm text-gray-600">
                    <p className="mb-1">
                      <strong>레코드 수:</strong> {records.length}개
                    </p>
                    <p>
                      <strong>데이터 포인트:</strong> {aggregatedData.length}개
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Chart display */}
          <div className="lg:col-span-3">
            <div className="bg-white rounded-lg shadow p-6">
              {loading ? (
                <div className="flex justify-center items-center h-96">
                  <div className="animate-pulse text-gray-500">로딩 중...</div>
                </div>
              ) : error ? (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <p className="text-red-800">{error}</p>
                </div>
              ) : (
                <>
                  <div className="mb-6">
                    <h2 className="text-xl font-semibold text-gray-900">
                      {selectedDatasetId
                        ? datasets.find((d) => d.id === selectedDatasetId)?.title
                        : '차트'}
                    </h2>
                    {xField && yField && (
                      <p className="text-sm text-gray-600 mt-1">
                        {xField} vs {yField}
                      </p>
                    )}
                  </div>
                  {renderChart()}
                </>
              )}
            </div>

            {/* Tips */}
            {!selectedDatasetId && (
              <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-semibold text-blue-900 mb-2">💡 사용 팁</h3>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• 먼저 분석할 데이터셋을 선택하세요</li>
                  <li>• 차트 타입을 선택하세요 (막대, 선, 영역, 파이)</li>
                  <li>• X축과 Y축에 표시할 필드를 선택하세요</li>
                  <li>• 파이 차트는 카테고리 데이터에 적합합니다</li>
                  <li>• 선/영역 차트는 시간 흐름 데이터에 적합합니다</li>
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}

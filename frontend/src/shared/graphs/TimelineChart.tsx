/**
 * TimelineChart.tsx - Temporal visualization of pharmaceutical data
 * Uses Chart.js for interactive time-series visualization
 */

import React, { useRef, useEffect, useCallback, useMemo, useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  TimeScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import { Card, Select, DatePicker, Space, Row, Col, Statistic, Button, Spin } from 'antd';
import {
  DownloadOutlined,
  BarChartOutlined,
  LineChartOutlined,
  PieChartOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { RangeValue } from 'antd/es/date-picker';
import dayjs from 'dayjs';
import axios from 'axios';

import type { TimelineDataPoint } from './types';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  TimeScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const { RangePicker } = DatePicker;

interface TimelineChartProps {
  apiBaseUrl?: string;
  height?: number;
  onDataPointClick?: (dataPoint: TimelineDataPoint) => void;
  onExport?: (data: TimelineDataPoint[]) => void;
}

type ChartType = 'line' | 'bar' | 'doughnut';
type DataType = 'submissions' | 'trials' | 'approvals' | 'all';

interface TimelineChartConfig {
  label: string;
  color: string;
  backgroundColor: string;
  apiEndpoint: string;
}

const DATA_TYPE_CONFIGS: Record<DataType, TimelineChartConfig> = {
  submissions: {
    label: 'Regulatory Submissions',
    color: 'rgb(255, 99, 132)',
    backgroundColor: 'rgba(255, 99, 132, 0.5)',
    apiEndpoint: '/regulatory/timeline'
  },
  trials: {
    label: 'Clinical Trials',
    color: 'rgb(54, 162, 235)',
    backgroundColor: 'rgba(54, 162, 235, 0.5)',
    apiEndpoint: '/clinical/timeline'
  },
  approvals: {
    label: 'Drug Approvals',
    color: 'rgb(75, 192, 192)',
    backgroundColor: 'rgba(75, 192, 192, 0.5)',
    apiEndpoint: '/regulatory/approvals-timeline'
  },
  all: {
    label: 'All Events',
    color: 'rgb(153, 102, 255)',
    backgroundColor: 'rgba(153, 102, 255, 0.5)',
    apiEndpoint: '/cross/timeline'
  }
};

export const TimelineChart: React.FC<TimelineChartProps> = ({
  apiBaseUrl = '/api/v1',
  height = 400,
  onDataPointClick,
  onExport
}) => {
  const chartRef = useRef<any>(null);
  const [chartType, setChartType] = useState<ChartType>('line');
  const [dataType, setDataType] = useState<DataType>('all');
  const [dateRange, setDateRange] = useState<RangeValue<dayjs.Dayjs>>([null, null]);
  const [timelineData, setTimelineData] = useState<TimelineDataPoint[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [aggregation, setAggregation] = useState<'day' | 'week' | 'month' | 'quarter' | 'year'>('month');

  // Fetch timeline data from API
  const fetchTimelineData = useCallback(async () => {
    setLoading(true);
    const startTime = performance.now();

    try {
      const config = DATA_TYPE_CONFIGS[dataType];
      const params: any = {
        aggregation
      };

      if (dateRange?.[0]) {
        params.start_date = dateRange[0].format('YYYY-MM-DD');
      }
      if (dateRange?.[1]) {
        params.end_date = dateRange[1].format('YYYY-MM-DD');
      }

      const response = await axios.get(
        `${apiBaseUrl}${config.apiEndpoint}`,
        { params }
      );

      const endTime = performance.now();
      console.log(`Timeline fetch time: ${(endTime - startTime).toFixed(2)}ms`);

      if (response.data && response.data.data) {
        setTimelineData(response.data.data);
      } else if (Array.isArray(response.data)) {
        setTimelineData(response.data);
      } else {
        setTimelineData([]);
      }
    } catch (error: any) {
      console.error('Error fetching timeline data:', error);
      // For demo purposes, generate mock data if API fails
      setTimelineData(generateMockTimelineData(dataType));
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl, dataType, dateRange, aggregation]);

  // Generate mock data for demonstration
  const generateMockTimelineData = useCallback((type: DataType): TimelineDataPoint[] => {
    const data: TimelineDataPoint[] = [];
    const startDate = dayjs().subtract(2, 'year');
    const endDate = dayjs();
    let currentDate = startDate;

    while (currentDate.isBefore(endDate)) {
      const baseCount = type === 'all' ? 50 : 30;
      const variance = Math.random() * 20 - 10;
      const count = Math.max(0, Math.round(baseCount + variance));

      data.push({
        date: currentDate.format('YYYY-MM-DD'),
        count,
        category: type
      });

      currentDate = currentDate.add(1, aggregation === 'day' ? 'day' : aggregation === 'week' ? 'week' : 'month');
    }

    return data;
  }, [aggregation]);

  // Export chart data
  const handleExport = useCallback(() => {
    const exportData = {
      dataType,
      dateRange: dateRange?.[0]?.format('YYYY-MM-DD') + ' to ' + dateRange?.[1]?.format('YYYY-MM-DD'),
      aggregation,
      data: timelineData
    };

    if (onExport) {
      onExport(timelineData);
    } else {
      const dataStr = JSON.stringify(exportData, null, 2);
      const blob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `timeline_${dataType}_${new Date().toISOString().slice(0, 10)}.json`;
      link.click();
      URL.revokeObjectURL(url);
    }
  }, [timelineData, dataType, dateRange, aggregation, onExport]);

  // Export chart as image
  const handleExportImage = useCallback(() => {
    if (chartRef.current) {
      const link = document.createElement('a');
      link.download = `timeline_${dataType}_chart.png`;
      link.href = chartRef.current.toBase64Image();
      link.click();
    }
  }, [chartRef, dataType]);

  // Chart.js options
  const chartOptions = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    height,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          font: { size: 12 }
        }
      },
      title: {
        display: true,
        text: DATA_TYPE_CONFIGS[dataType].label + ' Over Time',
        font: { size: 16, weight: 'bold' as const }
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
        callbacks: {
          label: function(context: any) {
            return `${context.dataset.label}: ${context.parsed.y} events`;
          }
        }
      }
    },
    scales: {
      x: {
        type: 'time' as const,
        time: {
          unit: aggregation === 'day' ? 'day' : aggregation === 'week' ? 'week' : 'month'
        },
        title: {
          display: true,
          text: 'Date'
        }
      },
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Count'
        }
      }
    },
    onClick: (_event: any, elements: any[]) => {
      if (elements.length > 0 && onDataPointClick) {
        const index = elements[0].index;
        onDataPointClick(timelineData[index]);
      }
    }
  }), [height, dataType, aggregation, onDataPointClick, timelineData]);

  // Prepare chart data
  const chartData = useMemo(() => {
    const config = DATA_TYPE_CONFIGS[dataType];

    return {
      labels: timelineData.map(d => d.date),
      datasets: [{
        label: config.label,
        data: timelineData.map(d => d.count),
        borderColor: config.color,
        backgroundColor: config.backgroundColor,
        fill: chartType === 'line',
        tension: 0.1
      }]
    };
  }, [timelineData, dataType, chartType]);

  // Calculate statistics
  const stats = useMemo(() => {
    if (timelineData.length === 0) {
      return { total: 0, average: 0, max: 0, min: 0 };
    }

    const counts = timelineData.map(d => d.count);
    return {
      total: counts.reduce((a, b) => a + b, 0),
      average: Math.round(counts.reduce((a, b) => a + b, 0) / counts.length),
      max: Math.max(...counts),
      min: Math.min(...counts)
    };
  }, [timelineData]);

  // Initial data load
  useEffect(() => {
    fetchTimelineData();
  }, [dataType, aggregation]); // Only refetch on type/agg change, not date range

  // Render chart based on type
  const renderChart = () => {
    const commonProps = {
      ref: chartRef,
      data: chartData,
      options: chartOptions
    };

    switch (chartType) {
      case 'line':
        return <Line {...commonProps} />;
      case 'bar':
        return <Bar {...commonProps} />;
      case 'doughnut':
        return <Doughnut {...commonProps} />;
      default:
        return <Line {...commonProps} />;
    }
  };

  return (
    <Card
      title="Timeline Visualization"
      extra={
        <Space>
          <Button icon={<ReloadOutlined />} onClick={fetchTimelineData} loading={loading}>
            Refresh
          </Button>
          <Button icon={<DownloadOutlined />} onClick={handleExport}>
            Export Data
          </Button>
          <Button icon={<DownloadOutlined />} onClick={handleExportImage}>
            Export Image
          </Button>
        </Space>
      }
    >
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        {/* Controls */}
        <Row gutter={16}>
          <Col span={6}>
            <div style={{ marginBottom: 8 }}>
              <strong>Data Type:</strong>
            </div>
            <Select
              style={{ width: '100%' }}
              value={dataType}
              onChange={setDataType}
            >
              <Select.Option value="submissions">Regulatory Submissions</Select.Option>
              <Select.Option value="trials">Clinical Trials</Select.Option>
              <Select.Option value="approvals">Drug Approvals</Select.Option>
              <Select.Option value="all">All Events</Select.Option>
            </Select>
          </Col>
          <Col span={6}>
            <div style={{ marginBottom: 8 }}>
              <strong>Chart Type:</strong>
            </div>
            <Select
              style={{ width: '100%' }}
              value={chartType}
              onChange={setChartType}
            >
              <Select.Option value="line">
                <LineChartOutlined /> Line Chart
              </Select.Option>
              <Select.Option value="bar">
                <BarChartOutlined /> Bar Chart
              </Select.Option>
              <Select.Option value="doughnut">
                <PieChartOutlined /> Doughnut Chart
              </Select.Option>
            </Select>
          </Col>
          <Col span={6}>
            <div style={{ marginBottom: 8 }}>
              <strong>Aggregation:</strong>
            </div>
            <Select
              style={{ width: '100%' }}
              value={aggregation}
              onChange={setAggregation}
            >
              <Select.Option value="day">Daily</Select.Option>
              <Select.Option value="week">Weekly</Select.Option>
              <Select.Option value="month">Monthly</Select.Option>
              <Select.Option value="quarter">Quarterly</Select.Option>
              <Select.Option value="year">Yearly</Select.Option>
            </Select>
          </Col>
          <Col span={6}>
            <div style={{ marginBottom: 8 }}>
              <strong>Date Range:</strong>
            </div>
            <RangePicker
              style={{ width: '100%' }}
              value={dateRange}
              onChange={setDateRange}
              allowClear
            />
          </Col>
        </Row>

        {/* Statistics */}
        <Row gutter={16}>
          <Col span={6}>
            <Statistic title="Total Events" value={stats.total} />
          </Col>
          <Col span={6}>
            <Statistic title="Average per Period" value={stats.average} />
          </Col>
          <Col span={6}>
            <Statistic title="Peak Count" value={stats.max} />
          </Col>
          <Col span={6}>
            <Statistic title="Minimum Count" value={stats.min} />
          </Col>
        </Row>

        {/* Chart */}
        <Spin spinning={loading}>
          <div style={{ height: `${height}px`, position: 'relative' }}>
            {renderChart()}
          </div>
        </Spin>
      </Space>
    </Card>
  );
};

export default TimelineChart;

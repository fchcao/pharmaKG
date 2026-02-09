import React, { useState } from 'react';
import {
  Table,
  Button,
  Space,
  Dropdown,
  Input,
  Typography,
  Tag,
  message,
  Checkbox,
  Card,
} from 'antd';
import {
  DownloadOutlined,
  SearchOutlined,
  FilterOutlined,
  ClearOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import type { ColumnType, TableProps } from 'antd/es/table';
import type { FilterValue, SorterResult } from 'antd/es/table/interface';
import { DataTableProps, ExportFormat } from '../types';
import { exportAsCSV, downloadAsFile } from '../utils/helpers';

const { Text } = Typography;

export function DataTable<T extends Record<string, unknown>>({
  columns,
  data,
  loading = false,
  pagination,
  onRowClick,
  rowSelection,
}: DataTableProps<T>): React.ReactElement {
  const [searchText, setSearchText] = useState('');
  const [filteredInfo, setFilteredInfo] = useState<Record<string, FilterValue | null>>({});
  const [sortedInfo, setSortedInfo] = useState<SorterResult<T>>({});
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([]);

  // Handle search
  const handleSearch = (value: string) => {
    setSearchText(value);
  };

  // Handle filter change
  const handleTableChange: TableProps<T>['onChange'] = (pagination, filters, sorter) => {
    setFilteredInfo(filters);
    setSortedInfo(sorter as SorterResult<T>);
  };

  // Clear all filters
  const handleClearFilters = () => {
    setFilteredInfo({});
    setSortedInfo({});
    setSearchText('');
    setSelectedRowKeys([]);
  };

  // Export data
  const handleExport = (format: ExportFormat) => {
    const dataToExport = selectedRowKeys.length > 0
      ? data.filter((item) => selectedRowKeys.includes(String(item.id || item.key)))
      : data;

    if (dataToExport.length === 0) {
      message.warning('No data to export');
      return;
    }

    const timestamp = new Date().toISOString().slice(0, 10);

    switch (format) {
      case 'csv':
        exportAsCSV(dataToExport as Record<string, unknown>[], `export-${timestamp}`);
        break;
      case 'json':
        downloadAsFile(dataToExport, `export-${timestamp}.json`, 'application/json');
        break;
      default:
        message.error('Unsupported export format');
    }
  };

  // Export menu
  const exportMenu = {
    items: [
      {
        key: 'csv',
        label: 'Export as CSV',
        onClick: () => handleExport('csv'),
      },
      {
        key: 'json',
        label: 'Export as JSON',
        onClick: () => handleExport('json'),
      },
    ],
  };

  // Build enhanced columns with search and filter
  const enhancedColumns = columns.map((col) => {
    const column: ColumnType<T> = {
      ...col,
      sorter: col.sorter ? true : false,
      sortOrder: sortedInfo.columnKey === col.key ? sortedInfo.order : null,
      filteredValue: filteredInfo[col.key] || null,
    };

    // Add search input for filterable columns
    if (col.filterable && col.dataIndex) {
      column.filterDropdown = ({
        setSelectedKeys,
        selectedKeys,
        confirm,
        clearFilters,
      }) => (
        <div style={{ padding: 8 }}>
          <Input
            placeholder={`Search ${col.title}`}
            value={selectedKeys[0] as string}
            onChange={(e) => setSelectedKeys(e.target.value ? [e.target.value] : [])}
            onPressEnter={() => confirm()}
            style={{ width: 188, marginBottom: 8, display: 'block' }}
          />
          <Space>
            <Button
              type="primary"
              onClick={() => confirm()}
              icon={<SearchOutlined />}
              size="small"
              style={{ width: 90 }}
            >
              Search
            </Button>
            <Button
              onClick={() => {
                clearFilters && clearFilters();
                confirm();
              }}
              size="small"
              style={{ width: 90 }}
            >
              Reset
            </Button>
          </Space>
        </div>
      );
      column.filterIcon = (filtered: boolean) => (
        <SearchOutlined style={{ color: filtered ? '#1890ff' : undefined }} />
      );
      column.onFilter = (value: string | number | boolean, record: T) => {
        const recordValue = record[col.dataIndex as keyof T];
        return String(recordValue)
          .toLowerCase()
          .includes(String(value).toLowerCase());
      };
    }

    return column;
  });

  // Row selection handler
  const handleRowSelectionChange = (keys: React.Key[]) => {
    setSelectedRowKeys(keys as string[]);
    rowSelection?.onChange?.(keys as string[]);
  };

  // Row props for click handling
  const getRowProps = (record: T) => ({
    onDoubleClick: () => onRowClick?.(record),
    style: { cursor: onRowClick ? 'pointer' : 'default' },
  });

  return (
    <Card
      className="data-table-card"
      bordered={false}
      style={{ marginBottom: 24 }}
    >
      {/* Toolbar */}
      <Space
        direction="vertical"
        style={{ width: '100%', marginBottom: 16 }}
        size="middle"
      >
        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
          <Space>
            <Input
              placeholder="Search all columns..."
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => handleSearch(e.target.value)}
              style={{ width: 250 }}
              allowClear
            />
            {(Object.keys(filteredInfo).some((k) => filteredInfo[k]) || sortedInfo.columnKey) && (
              <Button
                icon={<ClearOutlined />}
                onClick={handleClearFilters}
                size="small"
              >
                Clear Filters
              </Button>
            )}
          </Space>

          <Space>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {data.length} items
              {selectedRowKeys.length > 0 && ` (${selectedRowKeys.length} selected)`}
            </Text>
            <Dropdown menu={exportMenu} trigger={['click']}>
              <Button icon={<DownloadOutlined />} disabled={data.length === 0}>
                Export
              </Button>
            </Dropdown>
            {pagination && (
              <Button
                icon={<ReloadOutlined />}
                onClick={() => window.location.reload()}
                size="small"
              >
                Refresh
              </Button>
            )}
          </Space>
        </Space>

        {/* Active filters display */}
        {(Object.keys(filteredInfo).some((k) => filteredInfo[k]) || sortedInfo.columnKey) && (
          <Space wrap>
            {Object.entries(filteredInfo).map(([key, value]) =>
              value ? (
                <Tag
                  key={key}
                  closable
                  onClose={() =>
                    setFilteredInfo((prev) => ({ ...prev, [key]: null }))
                  }
                >
                  {key}: {String(value)}
                </Tag>
              ) : null
            )}
            {sortedInfo.columnKey && (
              <Tag
                closable
                onClose={() => setSortedInfo({})}
              >
                Sorted by: {String(sortedInfo.columnKey)} {sortedInfo.order === 'ascend' ? '↑' : '↓'}
              </Tag>
            )}
          </Space>
        )}
      </Space>

      {/* Table */}
      <Table
        columns={enhancedColumns}
        dataSource={data}
        loading={loading}
        rowKey={(record) => String(record.id || record.key)}
        onChange={handleTableChange}
        onRow={getRowProps}
        pagination={
          pagination
            ? {
                current: pagination.page,
                pageSize: pagination.pageSize,
                total: pagination.total,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `Total ${total} items`,
                onChange: pagination.onPageChange,
              }
            : false
        }
        rowSelection={
          rowSelection
            ? {
                selectedRowKeys,
                onChange: handleRowSelectionChange,
              }
            : undefined
        }
        size="small"
        scroll={{ x: 'max-content' }}
      />
    </Card>
  );
}

export default DataTable;

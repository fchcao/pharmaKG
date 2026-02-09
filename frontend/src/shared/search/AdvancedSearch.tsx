import React, { useState, useCallback } from 'react';
import {
  Card,
  Form,
  Input,
  Select,
  Button,
  Space,
  Typography,
  Row,
  Col,
  Divider,
  Tag,
  Collapse,
  DatePicker,
  InputNumber,
  Switch,
  Alert,
  Modal,
  List,
  Tooltip,
} from 'antd';
import {
  PlusOutlined,
  DeleteOutlined,
  SaveOutlined,
  SearchOutlined,
  ClearOutlined,
  InfoCircleOutlined,
  CopyOutlined,
} from '@ant-design/icons';
import { EntityType, Domain } from '../types';
import { SearchFilters, SavedQuery } from './types';
import { useSaveQuery, useSavedQueries, useDeleteQuery } from './api';
import dayjs, { Dayjs } from 'dayjs';

const { Title, Text } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;
const { Panel } = Collapse;

const ENTITY_TYPE_OPTIONS: { value: EntityType; label: string; availableFilters: string[] }[] = [
  {
    value: 'Compound',
    label: 'Compound',
    availableFilters: ['name', 'smiles', 'inchikey', 'molecular_weight', 'logp', 'rotatable_bonds'],
  },
  {
    value: 'Target',
    label: 'Target',
    availableFilters: ['name', 'uniprot_id', 'organism', 'protein_family', 'target_class'],
  },
  {
    value: 'Assay',
    label: 'Assay',
    availableFilters: ['name', 'assay_type', 'assay_format', 'target_type', 'confidence_score'],
  },
  {
    value: 'Pathway',
    label: 'Pathway',
    availableFilters: ['name', 'pathway_id', 'organism', 'category', 'disease_relevance'],
  },
  {
    value: 'Trial',
    label: 'Clinical Trial',
    availableFilters: [
      'name',
      'phase',
      'status',
      'start_date',
      'completion_date',
      'enrollment',
      'intervention_type',
    ],
  },
  {
    value: 'Subject',
    label: 'Trial Subject',
    availableFilters: ['subject_id', 'age', 'gender', 'condition', 'baseline_characteristics'],
  },
  {
    value: 'Intervention',
    label: 'Intervention',
    availableFilters: ['name', 'type', 'description', 'dosage', 'frequency'],
  },
  {
    value: 'Outcome',
    label: 'Outcome',
    availableFilters: ['name', 'category', 'statistical_significance', 'effect_size', 'confidence_interval'],
  },
  {
    value: 'Manufacturer',
    label: 'Manufacturer',
    availableFilters: ['name', 'location', 'certification_status', 'production_capacity'],
  },
  {
    value: 'Facility',
    label: 'Facility',
    availableFilters: ['name', 'type', 'location', 'capacity', 'certification_level'],
  },
  {
    value: 'Document',
    label: 'Document',
    availableFilters: ['title', 'document_type', 'publication_date', 'author', 'keywords'],
  },
  {
    value: 'Agency',
    label: 'Regulatory Agency',
    availableFilters: ['name', 'country', 'jurisdiction', 'authority_level'],
  },
  {
    value: 'Submission',
    label: 'Submission',
    availableFilters: ['submission_id', 'submission_type', 'submission_date', 'status', 'applicant'],
  },
];

interface FilterCondition {
  id: string;
  field: string;
  operator: string;
  value: string | number | [Dayjs, Dayjs];
  value2?: string | number;
}

interface AdvancedSearchProps {
  onSearch: (filters: SearchFilters) => void;
  className?: string;
  initialFilters?: SearchFilters;
}

const OPERATORS: Record<string, { value: string; label: string; inputType?: string; needsRange?: boolean }[]> = {
  text: [
    { value: 'contains', label: 'Contains' },
    { value: 'not_contains', label: 'Does Not Contain' },
    { value: 'equals', label: 'Equals' },
    { value: 'not_equals', label: 'Does Not Equal' },
    { value: 'starts_with', label: 'Starts With' },
    { value: 'ends_with', label: 'Ends With' },
  ],
  number: [
    { value: 'equals', label: 'Equals' },
    { value: 'not_equals', label: 'Does Not Equal' },
    { value: 'greater_than', label: 'Greater Than' },
    { value: 'less_than', label: 'Less Than' },
    { value: 'between', label: 'Between', needsRange: true },
    { value: 'in_range', label: 'In Range', needsRange: true },
  ],
  date: [
    { value: 'on', label: 'On' },
    { value: 'before', label: 'Before' },
    { value: 'after', label: 'After' },
    { value: 'between', label: 'Between', needsRange: true },
  ],
  enum: [
    { value: 'equals', label: 'Equals' },
    { value: 'not_equals', label: 'Does Not Equal' },
    { value: 'in', label: 'In' },
    { value: 'not_in', label: 'Not In' },
  ],
};

const getFieldType = (field: string): 'text' | 'number' | 'date' | 'enum' => {
  if (field.includes('date') || field.includes('Date')) return 'date';
  if (field.includes('weight') || field.includes('logp') || field.includes('capacity') || field.includes('size')) return 'number';
  if (['phase', 'status', 'type', 'gender'].includes(field)) return 'enum';
  return 'text';
};

export const AdvancedSearch: React.FC<AdvancedSearchProps> = ({
  onSearch,
  className = '',
  initialFilters,
}) => {
  const [form] = Form.useForm();
  const [selectedEntityTypes, setSelectedEntityTypes] = useState<EntityType[]>(
    initialFilters?.entityTypes || []
  );
  const [conditions, setConditions] = useState<FilterCondition[]>([]);
  const [booleanOperator, setBooleanOperator] = useState<'AND' | 'OR' | 'NOT'>('AND');
  const [useDateRange, setUseDateRange] = useState(false);
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs] | null>(null);
  const [savedQueriesModalVisible, setSavedQueriesModalVisible] = useState(false);

  const saveQueryMutation = useSaveQuery();
  const { data: savedQueries } = useSavedQueries();
  const deleteQueryMutation = useDeleteQuery();

  // Add a new condition
  const addCondition = useCallback(() => {
    const newCondition: FilterCondition = {
      id: `condition-${Date.now()}`,
      field: '',
      operator: 'contains',
      value: '',
    };
    setConditions([...conditions, newCondition]);
  }, [conditions]);

  // Remove a condition
  const removeCondition = useCallback((id: string) => {
    setConditions(conditions.filter((c) => c.id !== id));
  }, [conditions]);

  // Update a condition
  const updateCondition = useCallback((id: string, updates: Partial<FilterCondition>) => {
    setConditions(
      conditions.map((c) => (c.id === id ? { ...c, ...updates } : c))
    );
  }, [conditions]);

  // Get available fields based on selected entity types
  const getAvailableFields = useCallback(() => {
    if (selectedEntityTypes.length === 0) return [];

    const allFields = new Set<string>();
    selectedEntityTypes.forEach((entityType) => {
      const option = ENTITY_TYPE_OPTIONS.find((opt) => opt.value === entityType);
      if (option) {
        option.availableFilters.forEach((field) => allFields.add(field));
      }
    });

    return Array.from(allFields).sort();
  }, [selectedEntityTypes]);

  // Build search filters
  const buildSearchFilters = useCallback((): SearchFilters => {
    const numericalRanges: Record<string, { min?: number; max?: number }> = {};
    const properties: Record<string, unknown> = {};

    conditions.forEach((condition) => {
      if (!condition.field || !condition.operator) return;

      const fieldType = getFieldType(condition.field);

      if (fieldType === 'number' && (condition.operator === 'between' || condition.operator === 'in_range')) {
        const [min, max] = condition.value as [number, number];
        numericalRanges[condition.field] = { min, max };
      } else if (condition.operator === 'between' && fieldType === 'date') {
        const [start, end] = condition.value as [Dayjs, Dayjs];
        properties[`${condition.field}_start`] = start.toISOString();
        properties[`${condition.field}_end`] = end.toISOString();
      } else {
        properties[condition.field] = condition.value;
      }
    });

    return {
      query: form.getFieldValue('query') || '',
      domains: form.getFieldValue('domains'),
      entityTypes: selectedEntityTypes.length > 0 ? selectedEntityTypes : undefined,
      dateRange: useDateRange && dateRange
        ? {
            start: dateRange[0].toISOString(),
            end: dateRange[1].toISOString(),
          }
        : undefined,
      numericalRanges: Object.keys(numericalRanges).length > 0 ? numericalRanges : undefined,
      properties: Object.keys(properties).length > 0 ? properties : undefined,
      booleanOperator,
    };
  }, [conditions, form, selectedEntityTypes, useDateRange, dateRange, booleanOperator]);

  // Handle search
  const handleSearch = useCallback(() => {
    const filters = buildSearchFilters();
    onSearch(filters);
  }, [buildSearchFilters, onSearch]);

  // Clear all filters
  const handleClear = useCallback(() => {
    form.resetFields();
    setConditions([]);
    setSelectedEntityTypes([]);
    setBooleanOperator('AND');
    setUseDateRange(false);
    setDateRange(null);
  }, [form]);

  // Save query
  const handleSaveQuery = useCallback(() => {
    const filters = buildSearchFilters();

    Modal.confirm({
      title: 'Save Search Query',
      content: (
        <div>
          <Input
            placeholder="Enter a name for this query"
            id="query-name-input"
            autoFocus
            onPressEnter={(e) => {
              const input = e.target as HTMLInputElement;
              if (input.value) {
                saveQueryMutation.mutate({
                  name: input.value,
                  query: filters.query,
                  filters,
                });
              }
            }}
          />
        </div>
      ),
      onOk: () => {
        const input = document.getElementById('query-name-input') as HTMLInputElement;
        if (input?.value) {
          saveQueryMutation.mutate({
            name: input.value,
            query: filters.query,
            filters,
          });
        }
      },
    });
  }, [buildSearchFilters, saveQueryMutation]);

  // Load saved query
  const handleLoadQuery = useCallback((savedQuery: SavedQuery) => {
    form.setFieldsValue({
      query: savedQuery.query,
      domains: savedQuery.filters.domains,
    });

    if (savedQuery.filters.entityTypes) {
      setSelectedEntityTypes(savedQuery.filters.entityTypes);
    }

    if (savedQuery.filters.dateRange) {
      setUseDateRange(true);
      setDateRange([
        dayjs(savedQuery.filters.dateRange.start),
        dayjs(savedQuery.filters.dateRange.end),
      ]);
    }

    if (savedQuery.filters.booleanOperator) {
      setBooleanOperator(savedQuery.filters.booleanOperator);
    }

    // Rebuild conditions from properties
    const newConditions: FilterCondition[] = [];
    if (savedQuery.filters.properties) {
      Object.entries(savedQuery.filters.properties).forEach(([field, value]) => {
        if (field.endsWith('_start') || field.endsWith('_end')) return;

        const endValue = savedQuery.filters.properties?.[`${field}_end`];
        if (endValue) {
          newConditions.push({
            id: `condition-${Date.now()}-${field}`,
            field,
            operator: 'between',
            value: [dayjs(value as string), dayjs(endValue as string)],
          });
        } else {
          newConditions.push({
            id: `condition-${Date.now()}-${field}`,
            field,
            operator: 'equals',
            value: value as string,
          });
        }
      });
    }

    setConditions(newConditions);
    setSavedQueriesModalVisible(false);
  }, [form]);

  // Export query
  const handleExportQuery = useCallback(() => {
    const filters = buildSearchFilters();
    const queryStr = JSON.stringify(filters, null, 2);

    Modal.info({
      title: 'Export Query',
      content: (
        <div>
          <Text>Copy the query configuration below:</Text>
          <Input.TextArea
            value={queryStr}
            autoSize={{ minRows: 10, maxRows: 20 }}
            readOnly
            style={{ marginTop: 8, fontFamily: 'monospace', fontSize: '12px' }}
          />
        </div>
      ),
      width: 600,
    });
  }, [buildSearchFilters]);

  // Render condition input based on field type and operator
  const renderConditionInput = (condition: FilterCondition) => {
    if (!condition.field) return null;

    const fieldType = getFieldType(condition.field);
    const operatorConfig = OPERATORS[fieldType]?.find((op) => op.value === condition.operator);

    if (operatorConfig?.needsRange) {
      if (fieldType === 'number') {
        return (
          <InputNumber.Group compact>
            <InputNumber
              placeholder="Min"
              value={(condition.value as [number, number])?.[0]}
              onChange={(val) =>
                updateCondition(condition.id, {
                  value: [val || 0, (condition.value as [number, number])?.[1] || 0],
                })
              }
              style={{ width: '50%' }}
            />
            <InputNumber
              placeholder="Max"
              value={(condition.value as [number, number])?.[1]}
              onChange={(val) =>
                updateCondition(condition.id, {
                  value: [(condition.value as [number, number])?.[0] || 0, val || 0],
                })
              }
              style={{ width: '50%' }}
            />
          </InputNumber.Group>
        );
      } else if (fieldType === 'date') {
        return (
          <RangePicker
            value={condition.value as [Dayjs, Dayjs]}
            onChange={(dates) =>
              updateCondition(condition.id, { value: dates as [Dayjs, Dayjs] })
            }
            style={{ width: '100%' }}
          />
        );
      }
    }

    if (fieldType === 'number') {
      return (
        <InputNumber
          value={condition.value as number}
          onChange={(val) => updateCondition(condition.id, { value: val || 0 })}
          style={{ width: '100%' }}
        />
      );
    }

    if (fieldType === 'date') {
      return (
        <DatePicker
          value={condition.value as Dayjs}
          onChange={(date) => updateCondition(condition.id, { value: date as Dayjs })}
          style={{ width: '100%' }}
        />
      );
    }

    if (fieldType === 'enum') {
      const enumOptions: Record<string, string[]> = {
        phase: ['Phase 1', 'Phase 2', 'Phase 3', 'Phase 4', 'Not Applicable'],
        status: [
          'Not Yet Recruiting',
          'Recruiting',
          'Enrolling by Invitation',
          'Active',
          'Completed',
          'Terminated',
          'Withdrawn',
        ],
        type: ['Drug', 'Biological', 'Device', 'Procedure', 'Behavioral', 'Other'],
        gender: ['Male', 'Female', 'All', 'Not Reported'],
      };

      const options = enumOptions[condition.field] || [];

      if (condition.operator === 'in' || condition.operator === 'not_in') {
        return (
          <Select
            mode="multiple"
            value={condition.value as string[]}
            onChange={(val) => updateCondition(condition.id, { value: val })}
            style={{ width: '100%' }}
            options={options.map((opt) => ({ label: opt, value: opt }))}
          />
        );
      }

      return (
        <Select
          value={condition.value as string}
          onChange={(val) => updateCondition(condition.id, { value: val })}
          style={{ width: '100%' }}
          options={options.map((opt) => ({ label: opt, value: opt }))}
        />
      );
    }

    return (
      <Input
        value={condition.value as string}
        onChange={(e) => updateCondition(condition.id, { value: e.target.value })}
        placeholder="Enter value"
      />
    );
  };

  return (
    <div className={`advanced-search ${className}`}>
      <Card>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Title level={3}>Advanced Search</Title>
            <Text type="secondary">
              Build complex queries with multiple filters and conditions
            </Text>
          </div>

          <Form form={form} layout="vertical">
            {/* Main Query */}
            <Form.Item label="Search Query" name="query">
              <Input
                placeholder="Enter your main search query..."
                prefix={<SearchOutlined />}
                onPressEnter={handleSearch}
              />
            </Form.Item>

            {/* Domain Selection */}
            <Form.Item label="Domains" name="domains">
              <Select
                mode="multiple"
                placeholder="Select domains to search"
                options={[
                  { label: 'R&D', value: 'rd' },
                  { label: 'Clinical', value: 'clinical' },
                  { label: 'Supply Chain', value: 'supply' },
                  { label: 'Regulatory', value: 'regulatory' },
                ]}
              />
            </Form.Item>

            {/* Entity Type Selection */}
            <Form.Item label="Entity Types">
              <Select
                mode="multiple"
                placeholder="Select entity types to search"
                value={selectedEntityTypes}
                onChange={setSelectedEntityTypes}
                options={ENTITY_TYPE_OPTIONS.map((opt) => ({
                  label: opt.label,
                  value: opt.value,
                }))}
              />
            </Form.Item>

            {/* Boolean Operator */}
            <Form.Item label="Boolean Operator">
              <Space>
                <Select
                  value={booleanOperator}
                  onChange={setBooleanOperator}
                  style={{ width: 150 }}
                >
                  <Option value="AND">AND</Option>
                  <Option value="OR">OR</Option>
                  <Option value="NOT">NOT</Option>
                </Select>
                <Tooltip title="Combine multiple conditions using this operator">
                  <InfoCircleOutlined style={{ color: '#999' }} />
                </Tooltip>
              </Space>
            </Form.Item>

            {/* Custom Conditions */}
            <div>
              <Space style={{ marginBottom: 12 }}>
                <Text strong>Custom Conditions</Text>
                <Tooltip title="Add specific field filters">
                  <InfoCircleOutlined style={{ color: '#999' }} />
                </Tooltip>
              </Space>

              {conditions.length === 0 ? (
                <Alert
                  message="No conditions added"
                  description="Add conditions to create a more specific search"
                  type="info"
                  showIcon
                  style={{ marginBottom: 12 }}
                />
              ) : (
                <Space direction="vertical" style={{ width: '100%', marginBottom: 12 }}>
                  {conditions.map((condition, index) => (
                    <Card key={condition.id} size="small">
                      <Row gutter={16} align="middle">
                        <Col span={1}>
                          <Text strong>{index + 1}</Text>
                        </Col>
                        <Col span={7}>
                          <Select
                            placeholder="Select field"
                            value={condition.field || undefined}
                            onChange={(val) => updateCondition(condition.id, { field: val, operator: 'contains', value: '' })}
                            style={{ width: '100%' }}
                            options={getAvailableFields().map((field) => ({
                              label: field,
                              value: field,
                            }))}
                          />
                        </Col>
                        <Col span={5}>
                          <Select
                            placeholder="Operator"
                            value={condition.operator || undefined}
                            onChange={(val) =>
                              updateCondition(condition.id, { operator: val })
                            }
                            disabled={!condition.field}
                            style={{ width: '100%' }}
                            options={
                              condition.field
                                ? OPERATORS[getFieldType(condition.field)]
                                : []
                            }
                          />
                        </Col>
                        <Col span={9}>
                          {renderConditionInput(condition)}
                        </Col>
                        <Col span={2}>
                          <Button
                            type="text"
                            danger
                            icon={<DeleteOutlined />}
                            onClick={() => removeCondition(condition.id)}
                          />
                        </Col>
                      </Row>
                    </Card>
                  ))}
                </Space>
              )}

              <Button
                type="dashed"
                icon={<PlusOutlined />}
                onClick={addCondition}
                disabled={selectedEntityTypes.length === 0}
                block
              >
                Add Condition
              </Button>
            </div>

            {/* Date Range Filter */}
            <Divider orientation="left">Temporal Filters</Divider>
            <Form.Item label="Enable Date Range Filter">
              <Switch
                checked={useDateRange}
                onChange={setUseDateRange}
                checkedChildren="Enabled"
                unCheckedChildren="Disabled"
              />
            </Form.Item>

            {useDateRange && (
              <Form.Item label="Date Range">
                <RangePicker
                  value={dateRange}
                  onChange={setDateRange}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            )}

            {/* Action Buttons */}
            <Row gutter={16}>
              <Col span={6}>
                <Button
                  type="primary"
                  icon={<SearchOutlined />}
                  onClick={handleSearch}
                  block
                >
                  Search
                </Button>
              </Col>
              <Col span={6}>
                <Button icon={<ClearOutlined />} onClick={handleClear} block>
                  Clear All
                </Button>
              </Col>
              <Col span={6}>
                <Button
                  icon={<SaveOutlined />}
                  onClick={handleSaveQuery}
                  block
                  disabled={saveQueryMutation.isPending}
                >
                  Save Query
                </Button>
              </Col>
              <Col span={6}>
                <Button icon={<CopyOutlined />} onClick={handleExportQuery} block>
                  Export Query
                </Button>
              </Col>
            </Row>

            {/* Saved Queries */}
            <Divider orientation="left">Saved Queries</Divider>
            <Button onClick={() => setSavedQueriesModalVisible(true)} block>
              View Saved Queries ({savedQueries?.length || 0})
            </Button>
          </Form>
        </Space>
      </Card>

      {/* Saved Queries Modal */}
      <Modal
        title="Saved Queries"
        open={savedQueriesModalVisible}
        onCancel={() => setSavedQueriesModalVisible(false)}
        footer={null}
        width={800}
      >
        {savedQueries && savedQueries.length > 0 ? (
          <List
            dataSource={savedQueries}
            renderItem={(item) => (
              <List.Item
                actions={[
                  <Button
                    type="link"
                    onClick={() => handleLoadQuery(item)}
                  >
                    Load
                  </Button>,
                  <Button
                    type="link"
                    danger
                    onClick={() => deleteQueryMutation.mutate(item.id)}
                  >
                    Delete
                  </Button>,
                ]}
              >
                <List.Item.Meta
                  title={item.name}
                  description={
                    <Space>
                      <Text type="secondary">Query: {item.query}</Text>
                      {item.filters.domains && (
                        <>
                          {item.filters.domains.map((d) => (
                            <Tag key={d}>{d}</Tag>
                          ))}
                        </>
                      )}
                      {item.filters.entityTypes && (
                        <>
                          {item.filters.entityTypes.map((t) => (
                            <Tag key={t}>{t}</Tag>
                          ))}
                        </>
                      )}
                    </Space>
                  }
                />
              </List.Item>
            )}
          />
        ) : (
          <Alert
            message="No saved queries"
            description="Save a search query to see it here"
            type="info"
            showIcon
          />
        )}
      </Modal>
    </div>
  );
};

export default AdvancedSearch;

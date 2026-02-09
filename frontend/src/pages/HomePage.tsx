import React from 'react';
import { Card, Row, Col, Statistic } from 'antd';
import {
  ExperimentOutlined,
  MedicineBoxOutlined,
  ShoppingCartOutlined,
  FileProtectOutlined,
} from '@ant-design/icons';

const HomePage: React.FC = () => {
  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: '28px', fontWeight: 600, marginBottom: 8 }}>
          Welcome to PharmaKG
        </h1>
        <p style={{ fontSize: '16px', color: '#666' }}>
          Pharmaceutical Knowledge Graph - Comprehensive insights across R&D, Clinical, Supply Chain, and Regulatory domains
        </p>
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="R&D Domain"
              value={0}
              suffix="entities"
              prefix={<ExperimentOutlined style={{ color: '#4CAF50' }} />}
              valueStyle={{ color: '#4CAF50' }}
            />
            <p style={{ marginTop: 12, color: '#666' }}>
              Compounds, targets, pathways, and assays
            </p>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Clinical Domain"
              value={0}
              suffix="trials"
              prefix={<MedicineBoxOutlined style={{ color: '#2196F3' }} />}
              valueStyle={{ color: '#2196F3' }}
            />
            <p style={{ marginTop: 12, color: '#666' }}>
              Clinical trials, subjects, and outcomes
            </p>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Supply Chain"
              value={0}
              suffix="facilities"
              prefix={<ShoppingCartOutlined style={{ color: '#FF9800' }} />}
              valueStyle={{ color: '#FF9800' }}
            />
            <p style={{ marginTop: 12, color: '#666' }}>
              Manufacturers, suppliers, and facilities
            </p>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Regulatory"
              value={0}
              suffix="submissions"
              prefix={<FileProtectOutlined style={{ color: '#9C27B0' }} />}
              valueStyle={{ color: '#9C27B0' }}
            />
            <p style={{ marginTop: 12, color: '#666' }}>
              Submissions, approvals, and compliance
            </p>
          </Card>
        </Col>
      </Row>

      <Card style={{ marginTop: 24 }} title="Quick Start">
        <p>
          Welcome to PharmaKG - a comprehensive pharmaceutical knowledge graph platform.
          Use the navigation menu to explore different domains:
        </p>
        <ul>
          <li><strong>Research & Development:</strong> Explore compounds, targets, and pathways</li>
          <li><strong>Clinical Trials:</strong> Browse clinical trials and study results</li>
          <li><strong>Supply Chain:</strong> View manufacturers and supply networks</li>
          <li><strong>Regulatory:</strong> Access submissions and approval status</li>
        </ul>
      </Card>
    </div>
  );
};

export default HomePage;

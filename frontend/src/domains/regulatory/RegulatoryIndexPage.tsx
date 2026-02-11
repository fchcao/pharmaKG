import React from 'react';
import { Tabs } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  SubmissionsPage,
  ApprovalsPage,
  DocumentsPage,
  CRLsPage,
} from './';

const RegulatoryIndexPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  // Determine active tab from current path
  const getActiveKey = () => {
    const path = location.pathname;
    if (path.includes('/approvals')) return 'approvals';
    if (path.includes('/documents')) return 'documents';
    if (path.includes('/crls')) return 'crls';
    return 'submissions';
  };

  const activeKey = getActiveKey();

  const handleTabChange = (key: string) => {
    navigate(`/regulatory/${key}`);
  };

  const tabItems = [
    {
      key: 'submissions',
      label: 'Regulatory Submissions',
      children: <SubmissionsPage />,
    },
    {
      key: 'approvals',
      label: 'Regulatory Approvals',
      children: <ApprovalsPage />,
    },
    {
      key: 'crls',
      label: 'FDA CRLs',
      children: <CRLsPage />,
    },
    {
      key: 'documents',
      label: 'Regulatory Documents',
      children: <DocumentsPage />,
    },
  ];

  return (
    <div>
      <Tabs
        activeKey={activeKey}
        onChange={handleTabChange}
        items={tabItems}
        size="large"
      />
    </div>
  );
};

export default RegulatoryIndexPage;

import React from 'react';
import { Tabs } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  TrialsPage,
  ConditionsPage,
  InterventionsPage,
} from './';

const ClinicalIndexPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  // Determine active tab from current path
  const getActiveKey = () => {
    const path = location.pathname;
    if (path.includes('/conditions')) return 'conditions';
    if (path.includes('/interventions')) return 'interventions';
    return 'trials';
  };

  const activeKey = getActiveKey();

  const handleTabChange = (key: string) => {
    navigate(`/clinical/${key}`);
  };

  const tabItems = [
    {
      key: 'trials',
      label: 'Clinical Trials',
      children: <TrialsPage />,
    },
    {
      key: 'conditions',
      label: 'Medical Conditions',
      children: <ConditionsPage />,
    },
    {
      key: 'interventions',
      label: 'Interventions',
      children: <InterventionsPage />,
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

export default ClinicalIndexPage;

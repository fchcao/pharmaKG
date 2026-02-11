import React from 'react';
import { Tabs } from 'antd';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import {
  CompoundsPage,
  TargetsPage,
  AssaysPage,
  PathwaysPage,
} from './';

const ResearchIndexPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  // Determine active tab from current path
  const getActiveKey = () => {
    const path = location.pathname;
    if (path.includes('/targets')) return 'targets';
    if (path.includes('/assays')) return 'assays';
    if (path.includes('/pathways')) return 'pathways';
    return 'compounds';
  };

  const activeKey = getActiveKey();

  const handleTabChange = (key: string) => {
    navigate(`/rd/${key}`);
  };

  const tabItems = [
    {
      key: 'compounds',
      label: 'Compounds',
      children: <CompoundsPage />,
    },
    {
      key: 'targets',
      label: 'Protein Targets',
      children: <TargetsPage />,
    },
    {
      key: 'assays',
      label: 'Bioassays',
      children: <AssaysPage />,
    },
    {
      key: 'pathways',
      label: 'Pathways',
      children: <PathwaysPage />,
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

export default ResearchIndexPage;

import React from 'react';
import { Tabs } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  ManufacturersPage,
  FacilitiesPage,
  ShortageMonitorPage,
} from './';

const SupplyIndexPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  // Determine active tab from current path
  const getActiveKey = () => {
    const path = location.pathname;
    if (path.includes('/facilities')) return 'facilities';
    if (path.includes('/shortages')) return 'shortages';
    return 'manufacturers';
  };

  const activeKey = getActiveKey();

  const handleTabChange = (key: string) => {
    navigate(`/supply/${key}`);
  };

  const tabItems = [
    {
      key: 'manufacturers',
      label: 'Manufacturers',
      children: <ManufacturersPage />,
    },
    {
      key: 'facilities',
      label: 'Facilities',
      children: <FacilitiesPage />,
    },
    {
      key: 'shortages',
      label: 'Drug Shortage Monitor',
      children: <ShortageMonitorPage />,
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

export default SupplyIndexPage;

import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, App as AntdApp } from 'antd';
import { MainLayout } from '@/layouts';

import {
  HomePage,
  DashboardPage,
  AdminDashboardPage,
} from '@/pages';
import CrossDomainPage from '@/pages/CrossDomainPage';
import TestApi from '@/TestApi';

// R&D Domain Pages
import {
  CompoundsPage,
  CompoundDetailPage,
  TargetsPage,
  TargetDetailPage,
  AssaysPage,
  PathwaysPage,
} from '@/domains/research';

// Clinical Domain Pages
import {
  TrialsPage,
  TrialDetailPage,
  ConditionsPage,
  InterventionsPage,
} from '@/domains/clinical';

// Supply Chain Domain Pages
import {
  ManufacturersPage,
  ManufacturerDetailPage,
  ShortageMonitorPage,
  FacilitiesPage
} from '@/domains/supply';

// Regulatory Domain Pages
import {
  RegulatoryDashboardPage,
  SubmissionsPage,
  SubmissionDetailPage,
  ApprovalsPage,
  ApprovalDetailPage,
  DocumentsPage,
} from '@/domains/regulatory';

const SearchPage = () => <div><h1>Search</h1><p>Coming soon...</p></div>;
const SettingsPage = () => <div><h1>Settings</h1><p>Coming soon...</p></div>;

const App: React.FC = () => {
  return (
    <ConfigProvider>
      <AntdApp>
        <Routes>
          <Route path="/" element={<MainLayout />}>
            <Route index element={<HomePage />} />

            {/* Dashboard Routes */}
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="dashboard/admin" element={<AdminDashboardPage />} />

            {/* R&D Domain Routes */}
            <Route path="rd" element={<CompoundsPage />} />
            <Route path="rd/compounds" element={<CompoundsPage />} />
            <Route path="rd/compounds/:id" element={<CompoundDetailPage />} />
            <Route path="rd/targets" element={<TargetsPage />} />
            <Route path="rd/targets/:id" element={<TargetDetailPage />} />
            <Route path="rd/assays" element={<AssaysPage />} />
            <Route path="rd/pathways" element={<PathwaysPage />} />

            {/* Clinical Domain Routes */}
            <Route path="clinical" element={<TrialsPage />} />
            <Route path="clinical/trials" element={<TrialsPage />} />
            <Route path="clinical/trials/:id" element={<TrialDetailPage />} />
            <Route path="clinical/conditions" element={<ConditionsPage />} />
            <Route path="clinical/conditions/:id" element={<div>Condition Detail Page - Coming Soon</div>} />
            <Route path="clinical/interventions" element={<InterventionsPage />} />
            <Route path="clinical/interventions/:id" element={<div>Intervention Detail Page - Coming Soon</div>} />

            {/* Supply Chain Domain Routes */}
            <Route path="supply" element={<ManufacturersPage />} />
            <Route path="supply/manufacturers" element={<ManufacturersPage />} />
            <Route path="supply/manufacturers/:id" element={<ManufacturerDetailPage />} />
            <Route path="supply/shortages" element={<ShortageMonitorPage />} />
            <Route path="supply/facilities" element={<FacilitiesPage />} />

            {/* Regulatory Domain Routes */}
            <Route path="regulatory" element={<RegulatoryDashboardPage />} />
            <Route path="regulatory/submissions" element={<SubmissionsPage />} />
            <Route path="regulatory/submissions/:id" element={<SubmissionDetailPage />} />
            <Route path="regulatory/approvals" element={<ApprovalsPage />} />
            <Route path="regulatory/approvals/:id" element={<ApprovalDetailPage />} />
            <Route path="regulatory/documents" element={<DocumentsPage />} />

            {/* Cross-Domain Query Routes */}
            <Route path="cross-domain" element={<CrossDomainPage />} />

            <Route path="search" element={<SearchPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="test-api" element={<TestApi />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </AntdApp>
    </ConfigProvider>
  );
};

export default App;

import { lazy, Suspense } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "@/components/layout/AppLayout";
import ProtectedRoute from "@/components/auth/ProtectedRoute";

const Dashboard = lazy(() => import("@/pages/Dashboard"));
const CatRoom = lazy(() => import("@/pages/CatRoom"));
const Assistants = lazy(() => import("@/pages/Assistants"));
const CreateWizard = lazy(() => import("@/pages/CreateWizard"));
const Approvals = lazy(() => import("@/pages/Approvals"));
const ActivityLog = lazy(() => import("@/pages/ActivityLog"));
const Connectors = lazy(() => import("@/pages/Connectors"));
const AssistantDetail = lazy(() => import("@/pages/AssistantDetail"));
const Marketplace = lazy(() => import("@/pages/Marketplace"));
const Settings = lazy(() => import("@/pages/Settings"));
const Login = lazy(() => import("@/pages/Login"));
const AuthCallback = lazy(() => import("@/pages/AuthCallback"));

function PageLoader() {
  return (
    <div className="flex h-full items-center justify-center text-sm text-[#9a9a9a]">
      불러오는 중...
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="login" element={<Login />} />
          <Route path="auth/callback" element={<AuthCallback />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route index element={<Dashboard />} />
              <Route path="cat-room" element={<CatRoom />} />
              <Route path="assistants" element={<Assistants />} />
              <Route path="assistants/new" element={<CreateWizard />} />
              <Route path="approvals" element={<Approvals />} />
              <Route path="activity" element={<ActivityLog />} />
              <Route path="connectors" element={<Connectors />} />
              <Route path="assistants/:id" element={<AssistantDetail />} />
              <Route path="marketplace" element={<Marketplace />} />
              <Route path="settings" element={<Settings />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

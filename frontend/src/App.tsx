import { lazy, Suspense } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "@/components/layout/AppLayout";

const Dashboard = lazy(() => import("@/pages/Dashboard"));
const CatRoom = lazy(() => import("@/pages/CatRoom"));
const Assistants = lazy(() => import("@/pages/Assistants"));
const CreateWizard = lazy(() => import("@/pages/CreateWizard"));
const Approvals = lazy(() => import("@/pages/Approvals"));
const ActivityLog = lazy(() => import("@/pages/ActivityLog"));
const Connectors = lazy(() => import("@/pages/Connectors"));

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
          <Route element={<AppLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="cat-room" element={<CatRoom />} />
            <Route path="assistants" element={<Assistants />} />
            <Route path="assistants/new" element={<CreateWizard />} />
            <Route path="approvals" element={<Approvals />} />
            <Route path="activity" element={<ActivityLog />} />
            <Route path="connectors" element={<Connectors />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

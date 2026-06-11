import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { LoginPage } from "./pages/Login";
import { DashboardPage } from "./pages/Dashboard";
import { ApprovalInboxPage } from "./pages/ApprovalInbox";
import { HistoryPage, HistoryDetailPage } from "./pages/History";
import { NewAssistantPage } from "./pages/NewAssistant";
import { AssistantDetailPage } from "./pages/AssistantDetail";
import { CatRoomPage } from "./pages/CatRoom";

function RequireAuth({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem("access_token");
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <RequireAuth>
      <Layout>{children}</Layout>
    </RequireAuth>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route
          path="/"
          element={
            <AppLayout>
              <DashboardPage />
            </AppLayout>
          }
        />
        <Route
          path="/approvals"
          element={
            <AppLayout>
              <ApprovalInboxPage />
            </AppLayout>
          }
        />
        <Route
          path="/history"
          element={
            <AppLayout>
              <HistoryPage />
            </AppLayout>
          }
        />
        <Route
          path="/history/:id"
          element={
            <AppLayout>
              <HistoryDetailPage />
            </AppLayout>
          }
        />
        <Route
          path="/assistants/new"
          element={
            <AppLayout>
              <NewAssistantPage />
            </AppLayout>
          }
        />
        <Route
          path="/assistants/:id"
          element={
            <AppLayout>
              <AssistantDetailPage />
            </AppLayout>
          }
        />
        <Route
          path="/cat-room"
          element={
            <AppLayout>
              <CatRoomPage />
            </AppLayout>
          }
        />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

// Pages (stubs — Phase 1+ will fill these in)
const Dashboard = () => (
  <div className="p-8">
    <h1 className="text-2xl font-semibold text-[#0a0a0a]">대시보드</h1>
    <p className="mt-2 text-sm text-[#9a9a9a]">Phase 0 — 기반 구조 완성</p>
  </div>
);

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

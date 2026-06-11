import { BrowserRouter, Route, Routes } from "react-router-dom";

function ComingSoon({ page }: { page: string }) {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <p className="text-gray-400 text-sm">{page} — Phase 2에서 구현됩니다.</p>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ComingSoon page="Dashboard" />} />
        <Route path="/approvals" element={<ComingSoon page="Approvals" />} />
        <Route path="/history" element={<ComingSoon page="History" />} />
        <Route path="/cat-room" element={<ComingSoon page="Cat Room" />} />
        <Route
          path="/assistants/new"
          element={<ComingSoon page="New Assistant" />}
        />
        <Route
          path="/assistants/:id"
          element={<ComingSoon page="Assistant Detail" />}
        />
      </Routes>
    </BrowserRouter>
  );
}

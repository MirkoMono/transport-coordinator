import { Navigate, Route, Routes } from "react-router-dom";
import CoordinatorView from "./CoordinatorView";
import DriverView from "./DriverView";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<CoordinatorView />} />
      <Route path="/driver" element={<DriverView />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

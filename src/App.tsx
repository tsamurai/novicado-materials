import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import LandingPage from "./components/LandingPage";
import NotFound from "./components/NotFound";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Layout>
  );
}

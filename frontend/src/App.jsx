import { useState } from "react";
import SessionChoice from "./pages/SessionChoice";
import Sidebar from "./components/Sidebar";
import TopBar from "./components/TopBar";
import DataImport from "./pages/DataImport";
import DescriptiveStats from "./pages/DescriptiveStats";
import AssumptionChecker from "./pages/AssumptionChecker";
import RunAnalysis from "./pages/RunAnalysis";
import HypothesisManager from "./pages/HypothesisManager";
import QualitativeAnalysis from "./pages/QualitativeAnalysis";
import ReportExport from "./pages/ReportExport";
import AdminDashboard from "./pages/AdminDashboard";
import EphemeralExportReminder from "./components/EphemeralExportReminder";

export default function App() {
  const [sessionMode, setSessionMode] = useState(null); // null | "ephemeral" | "standard"
  const [sessionToken, setSessionToken] = useState(null);
  const [dataset, setDataset] = useState(null);
  const [aiEnabled, setAiEnabled] = useState(false);
  const [aiDisclaimerAccepted, setAiDisclaimerAccepted] = useState(false);
  const [alpha, setAlpha] = useState(0.05);
  const [page, setPage] = useState("import");
  const [hasResults, setHasResults] = useState(false);

  if (!sessionMode) {
    return <SessionChoice onChoice={(mode, token) => {
      setSessionMode(mode);
      setSessionToken(token);
    }} />;
  }

  const apiHeaders = {
    "session-token": sessionToken,
    "mode": sessionMode,
  };

  return (
    <div style={{ display: "flex", height: "100vh", fontFamily: "'Inter', system-ui, sans-serif", background: "#f8fafc" }}>
      <Sidebar page={page} setPage={setPage} sessionMode={sessionMode} />
      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        <TopBar
          dataset={dataset}
          sessionMode={sessionMode}
          aiEnabled={aiEnabled}
          setAiEnabled={setAiEnabled}
          aiDisclaimerAccepted={aiDisclaimerAccepted}
          setAiDisclaimerAccepted={setAiDisclaimerAccepted}
          alpha={alpha}
          setAlpha={setAlpha}
          apiHeaders={apiHeaders}
        />
        <main style={{ flex: 1, overflow: "auto", padding: "1.5rem" }}>
          {page === "import" && (
            <DataImport apiHeaders={apiHeaders} setDataset={setDataset} />
          )}
          {page === "descriptive" && (
            <DescriptiveStats apiHeaders={apiHeaders} dataset={dataset} />
          )}
          {page === "assumptions" && (
            <AssumptionChecker apiHeaders={apiHeaders} dataset={dataset} aiEnabled={aiEnabled} />
          )}
          {page === "analysis" && (
            <RunAnalysis apiHeaders={apiHeaders} dataset={dataset} alpha={alpha}
              aiEnabled={aiEnabled} onResult={() => setHasResults(true)} />
          )}
          {page === "hypotheses" && (
            <HypothesisManager apiHeaders={apiHeaders} dataset={dataset} alpha={alpha} />
          )}
          {page === "qualitative" && (
            <QualitativeAnalysis apiHeaders={apiHeaders} dataset={dataset} aiEnabled={aiEnabled} />
          )}
          {page === "reports" && (
            <ReportExport apiHeaders={apiHeaders} sessionMode={sessionMode} />
          )}
          {page === "admin" && <AdminDashboard />}
        </main>
      </div>
      {sessionMode === "ephemeral" && hasResults && (
        <EphemeralExportReminder apiHeaders={apiHeaders} />
      )}
    </div>
  );
}
useEffect(() => {
  const ping = () => fetch(`${process.env.REACT_APP_API_URL}/health`);
  const id = setInterval(ping, 14 * 60 * 1000);
  return () => clearInterval(id);
}, []);

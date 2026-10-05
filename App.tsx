import { NavLink, Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Scenario from "./pages/Scenario";
import Prediction from "./pages/Prediction";
import Optimize from "./pages/Optimize";
import Benchmarks from "./pages/Benchmarks";
import Robustness from "./pages/Robustness";
import Constraints from "./pages/Constraints";
import Reproducibility from "./pages/Reproducibility";

const NAV = [
  ["/", "Dashboard"], ["/scenario", "Scenario"], ["/prediction", "Prediction"], ["/optimize", "Optimize"],
  ["/benchmarks", "Benchmarks"], ["/robustness", "Robustness"], ["/constraints", "Constraints"], ["/reproducibility", "Reproducibility"],
] as const;

export default function App() {
  return (
    <div className="min-h-screen flex flex-col md:flex-row">
      <aside className="md:w-56 bg-navy-950 border-r border-navy-700 p-4 shrink-0">
        <h1 className="text-lg font-bold text-accent">Q-Green Fleet Twin</h1>
        <p className="text-xs text-slate-400 mb-4">Scenario-robust, quantum-inspired fleet decarbonisation planning</p>
        <nav className="flex md:flex-col gap-1 flex-wrap">
          {NAV.map(([to, label]) => (
            <NavLink key={to} to={to} end={to === "/"}
              className={({ isActive }) => `px-3 py-1.5 rounded text-sm ${isActive ? "bg-navy-700 text-accent" : "hover:bg-navy-800"}`}>
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="flex-1 p-6 max-w-6xl">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/scenario" element={<Scenario />} />
          <Route path="/prediction" element={<Prediction />} />
          <Route path="/optimize" element={<Optimize />} />
          <Route path="/benchmarks" element={<Benchmarks />} />
          <Route path="/robustness" element={<Robustness />} />
          <Route path="/constraints" element={<Constraints />} />
          <Route path="/reproducibility" element={<Reproducibility />} />
        </Routes>
      </main>
    </div>
  );
}

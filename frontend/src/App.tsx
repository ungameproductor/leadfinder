import { NavLink, Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import SearchPage from "./pages/SearchPage";
import LeadsPage from "./pages/LeadsPage";
import LeadDetailPage from "./pages/LeadDetailPage";

export default function App() {
  return (
    <div className="shell">
      <header className="top">
        <div className="brand">
          <svg className="brand-mark" viewBox="0 0 32 32" aria-hidden="true">
            <rect x="2.5" y="2.5" width="27" height="27" rx="6" fill="none" stroke="currentColor" strokeWidth="2" />
            <path d="M16 8.5 23 16 16 23.5 9 16Z" fill="currentColor" />
          </svg>
          <div>
            <p className="eyebrow">Qualificazione commerciale locale</p>
            <h1>
              Lead Finder <span>Italia</span>
            </h1>
          </div>
        </div>
        <nav>
          <NavLink to="/" end>
            Dashboard
          </NavLink>
          <NavLink to="/ricerca">Ricerca</NavLink>
          <NavLink to="/lead">Lead</NavLink>
        </nav>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/ricerca" element={<SearchPage />} />
          <Route path="/lead" element={<LeadsPage />} />
          <Route path="/lead/:id" element={<LeadDetailPage />} />
        </Routes>
      </main>
    </div>
  );
}

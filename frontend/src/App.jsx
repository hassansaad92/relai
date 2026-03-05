import { Routes, Route } from 'react-router-dom';
import Sidebar from './components/layout/Sidebar';
import OverviewPage from './pages/OverviewPage';
import MechanicsPage from './pages/MechanicsPage';
import ProjectsPage from './pages/ProjectsPage';
import SkillsPage from './pages/SkillsPage';
import GanttPage from './pages/GanttPage';

export default function App() {
  return (
    <>
      <Sidebar />
      <div className="main-content">
        <Routes>
          <Route path="/" element={<OverviewPage />} />
          <Route path="/mechanics" element={<MechanicsPage />} />
          <Route path="/projects" element={<ProjectsPage />} />
          <Route path="/skills" element={<SkillsPage />} />
          <Route path="/gantt" element={<GanttPage />} />
        </Routes>
      </div>
    </>
  );
}

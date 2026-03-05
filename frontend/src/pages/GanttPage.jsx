import { useState } from 'react';
import { useData } from '../hooks/useData';
import Header from '../components/layout/Header';
import GanttChart from '../components/gantt/GanttChart';

const VIEW_MODES = ['Day', 'Week', 'Month'];

export default function GanttPage() {
  const { assignments, lookups, loading, error } = useData();
  const [viewMode, setViewMode] = useState('Week');

  if (loading) return <><Header title="Gantt" /><p>Loading...</p></>;
  if (error) return <><Header title="Gantt" /><p style={{ color: 'red' }}>Error: {error}</p></>;

  return (
    <>
      <Header title="Gantt" />
      <div className="section">
        <h2>Assignment Timeline</h2>
        <div className="gantt-controls">
          {VIEW_MODES.map(mode => (
            <button
              key={mode}
              className={viewMode === mode ? 'active' : ''}
              onClick={() => setViewMode(mode)}
            >
              {mode}
            </button>
          ))}
        </div>
        <div className="gantt-wrapper">
          <GanttChart
            assignments={assignments}
            mechanicsById={lookups.mechanicsById}
            projectsById={lookups.projectsById}
            viewMode={viewMode}
          />
        </div>
      </div>
    </>
  );
}

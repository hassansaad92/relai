import { useEffect, useRef } from 'react';
import Gantt from 'frappe-gantt';
import '../../../node_modules/frappe-gantt/dist/frappe-gantt.css';

const BAR_COLORS = ['#041e42', '#f65275', '#2a6496', '#d9534f', '#5cb85c'];

export default function GanttChart({ assignments, mechanicsById, projectsById, viewMode }) {
  const containerRef = useRef(null);
  const ganttRef = useRef(null);
  const prevDataRef = useRef(null);

  // Build tasks from assignments
  const tasks = assignments.map((a, i) => {
    const mechanic = mechanicsById[a.mechanic_id];
    const project = projectsById[a.project_id];
    return {
      id: `task-${a.id}`,
      name: `${mechanic?.name || 'Unknown'} \u2192 ${project?.name || 'Unknown'}`,
      start: a.start_date,
      end: a.end_date,
      progress: 0,
      custom_class: `gantt-bar-${i % BAR_COLORS.length}`,
    };
  });

  // Create or recreate gantt when data changes
  useEffect(() => {
    if (!containerRef.current || tasks.length === 0) return;

    // Serialize to check if data actually changed
    const dataKey = JSON.stringify(tasks);
    if (dataKey === prevDataRef.current && ganttRef.current) return;
    prevDataRef.current = dataKey;

    // Clear previous instance
    containerRef.current.innerHTML = '';

    // Inject custom bar colors once
    const styleId = 'gantt-bar-colors';
    if (!document.getElementById(styleId)) {
      const style = document.createElement('style');
      style.id = styleId;
      style.textContent = BAR_COLORS.map((c, i) =>
        `.gantt-bar-${i} .bar { fill: ${c} !important; }
         .gantt-bar-${i} .bar-progress { fill: ${c} !important; }`
      ).join('\n');
      document.head.appendChild(style);
    }

    ganttRef.current = new Gantt(containerRef.current, tasks, {
      view_mode: viewMode,
      date_format: 'YYYY-MM-DD',
      language: 'en',
    });
  });

  // Change view mode without recreating the whole chart
  useEffect(() => {
    if (ganttRef.current) {
      ganttRef.current.change_view_mode(viewMode);
    }
  }, [viewMode]);

  return <div className="gantt-mount" ref={containerRef} />;
}

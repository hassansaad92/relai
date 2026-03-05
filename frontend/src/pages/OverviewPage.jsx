import { useData } from '../hooks/useData';
import Header from '../components/layout/Header';
import MechanicMiniCard from '../components/mechanics/MechanicMiniCard';
import ProjectMiniCard from '../components/projects/ProjectMiniCard';

export default function OverviewPage() {
  const { mechanics, projects, lookups, loading, error } = useData();

  if (loading) return <><Header title="Overview" /><p>Loading...</p></>;
  if (error) return <><Header title="Overview" /><p style={{ color: 'red' }}>Error: {error}</p></>;

  return (
    <>
      <Header title="Overview" />
      <div className="container">
        <div className="section">
          <h2>Mechanics</h2>
          {mechanics.map(m => (
            <MechanicMiniCard
              key={m.id}
              mechanic={m}
              currentAssignment={lookups.byMechanic[m.id]?.[1]}
              projectsById={lookups.projectsById}
            />
          ))}
        </div>
        <div className="section">
          <h2>Projects</h2>
          {projects.map(p => (
            <ProjectMiniCard
              key={p.id}
              project={p}
              assignments={lookups.byProject[p.id] || []}
              mechanicsById={lookups.mechanicsById}
            />
          ))}
        </div>
      </div>
    </>
  );
}

import { useState } from 'react';
import { useData } from '../hooks/useData';
import Header from '../components/layout/Header';
import ProjectFullCard from '../components/projects/ProjectFullCard';
import ProjectForm from '../components/projects/ProjectForm';
import Modal from '../components/shared/Modal';

export default function ProjectsPage() {
  const { projects, lookups, loading, error } = useData();
  const [showModal, setShowModal] = useState(false);

  if (loading) return <><Header title="Projects" /><p>Loading...</p></>;
  if (error) return <><Header title="Projects" /><p style={{ color: 'red' }}>Error: {error}</p></>;

  return (
    <>
      <Header title="Projects" />
      <div className="section">
        <h2>All Projects</h2>
        {projects.map(p => (
          <ProjectFullCard
            key={p.id}
            project={p}
            assignments={lookups.byProject[p.id] || []}
            mechanicsById={lookups.mechanicsById}
          />
        ))}
        <button className="add-button" onClick={() => setShowModal(true)}>+ Add Project</button>
      </div>
      {showModal && (
        <Modal title="Add Project" onClose={() => setShowModal(false)}>
          <ProjectForm onClose={() => setShowModal(false)} />
        </Modal>
      )}
    </>
  );
}

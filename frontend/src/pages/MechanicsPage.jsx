import { useState } from 'react';
import { useData } from '../hooks/useData';
import Header from '../components/layout/Header';
import MechanicFullCard from '../components/mechanics/MechanicFullCard';
import MechanicForm from '../components/mechanics/MechanicForm';
import Modal from '../components/shared/Modal';

export default function MechanicsPage() {
  const { mechanics, lookups, loading, error } = useData();
  const [showModal, setShowModal] = useState(false);

  if (loading) return <><Header title="Mechanics" /><p>Loading...</p></>;
  if (error) return <><Header title="Mechanics" /><p style={{ color: 'red' }}>Error: {error}</p></>;

  return (
    <>
      <Header title="Mechanics" />
      <div className="section">
        <h2>All Mechanics</h2>
        {mechanics.map(m => (
          <MechanicFullCard
            key={m.id}
            mechanic={m}
            currentAssignment={lookups.byMechanic[m.id]?.[1]}
            nextAssignment={lookups.byMechanic[m.id]?.[2]}
            projectsById={lookups.projectsById}
          />
        ))}
        <button className="add-button" onClick={() => setShowModal(true)}>+ Add Mechanic</button>
      </div>
      {showModal && (
        <Modal title="Add Mechanic" onClose={() => setShowModal(false)}>
          <MechanicForm onClose={() => setShowModal(false)} />
        </Modal>
      )}
    </>
  );
}

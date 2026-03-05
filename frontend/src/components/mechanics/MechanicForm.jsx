import { useState } from 'react';
import { useData } from '../../hooks/useData';

export default function MechanicForm({ onClose }) {
  const { skills } = useData();
  const [name, setName] = useState('');
  const [selectedSkills, setSelectedSkills] = useState([]);

  function toggleSkill(skill) {
    setSelectedSkills(prev =>
      prev.includes(skill) ? prev.filter(s => s !== skill) : [...prev, skill]
    );
  }

  function handleSubmit(e) {
    e.preventDefault();
    const mechanic = { name, skills: selectedSkills.join(',') };
    console.log('New mechanic:', mechanic);
    alert('Mechanic added! (Currently logged to console - backend integration pending)');
    onClose();
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-group">
        <label>Name *</label>
        <input type="text" value={name} onChange={e => setName(e.target.value)} required />
      </div>
      <div className="form-group">
        <label>Skills *</label>
        <div className="skill-tiles">
          {skills.map(s => {
            const id = `mech-${s.skill.toLowerCase().replace(/\s+/g, '-')}`;
            return (
              <div className="skill-tile" key={s.skill}>
                <input
                  type="checkbox"
                  id={id}
                  checked={selectedSkills.includes(s.skill)}
                  onChange={() => toggleSkill(s.skill)}
                />
                <label htmlFor={id}>{s.skill}</label>
              </div>
            );
          })}
        </div>
      </div>
      <button type="submit" className="submit-button">Add Mechanic</button>
    </form>
  );
}

import { useState } from 'react';
import { useData } from '../../hooks/useData';

export default function ProjectForm({ onClose }) {
  const { skills } = useData();
  const [form, setForm] = useState({
    name: '',
    required_skills: [],
    num_elevators: '',
    start_date: '',
    duration_weeks: '',
    status: 'pending',
  });

  function update(field, value) {
    setForm(prev => ({ ...prev, [field]: value }));
  }

  function handleSubmit(e) {
    e.preventDefault();
    const project = { ...form, required_skills: form.required_skills.join(',') };
    console.log('New project:', project);
    alert('Project added! (Currently logged to console - backend integration pending)');
    onClose();
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-group">
        <label>Building Name *</label>
        <input type="text" value={form.name} onChange={e => update('name', e.target.value)} required />
      </div>
      <div className="form-group">
        <label>Required Skills *</label>
        <select
          multiple
          size={5}
          value={form.required_skills}
          onChange={e => update('required_skills', Array.from(e.target.selectedOptions, o => o.value))}
          required
        >
          {skills.map(s => (
            <option key={s.skill} value={s.skill}>{s.skill}</option>
          ))}
        </select>
        <small style={{ color: '#666', fontSize: 12 }}>Hold Ctrl/Cmd to select multiple skills</small>
      </div>
      <div className="form-group">
        <label>Number of Elevators *</label>
        <input type="number" min="1" value={form.num_elevators} onChange={e => update('num_elevators', e.target.value)} required />
      </div>
      <div className="form-group">
        <label>Start Date *</label>
        <input type="date" value={form.start_date} onChange={e => update('start_date', e.target.value)} required />
      </div>
      <div className="form-group">
        <label>Duration (weeks) *</label>
        <input type="number" min="1" value={form.duration_weeks} onChange={e => update('duration_weeks', e.target.value)} required />
      </div>
      <div className="form-group">
        <label>Status *</label>
        <select value={form.status} onChange={e => update('status', e.target.value)} required>
          <option value="pending">Pending</option>
          <option value="in-progress">In Progress</option>
        </select>
      </div>
      <button type="submit" className="submit-button">Add Project</button>
    </form>
  );
}

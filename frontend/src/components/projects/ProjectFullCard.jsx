import Card from '../shared/Card';
import StatusBadge from '../shared/StatusBadge';
import SkillTag from '../shared/SkillTag';
import { formatDate, calculateTMinus } from '../../utils/dates';

export default function ProjectFullCard({ project, assignments, mechanicsById }) {
  const current = assignments.find(a => a.sequence === '1');
  const mechanic = current ? mechanicsById[current.mechanic_id] : null;
  const skills = project.required_skills ? project.required_skills.split(',').map(s => s.trim()) : [];
  const status = project.status.toLowerCase();

  return (
    <Card status={status}>
      <div className="card-header">
        <div className="card-title">{project.name}</div>
        <StatusBadge status={status} />
      </div>
      <div className="card-detail">
        <strong>Required Skills:</strong>
        <div>{skills.map(s => <SkillTag key={s} skill={s} />)}</div>
      </div>
      <div className="card-detail">
        <strong>Elevators:</strong> <span className="duration">{project.num_elevators}</span>
      </div>
      <div className="card-detail">
        <strong>Start Date:</strong> {formatDate(project.start_date)}
      </div>
      <div className="card-detail">
        <strong>Duration:</strong> <span className="duration">{project.duration_weeks} weeks</span>
      </div>
      <div className="card-detail">
        <strong>Mechanic:</strong> {mechanic ? mechanic.name : 'Unassigned'}
      </div>
      <div className="t-minus">{calculateTMinus(project.start_date)}</div>
    </Card>
  );
}

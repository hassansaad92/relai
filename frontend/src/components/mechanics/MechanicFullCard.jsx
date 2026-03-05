import Card from '../shared/Card';
import StatusBadge from '../shared/StatusBadge';
import SkillTag from '../shared/SkillTag';
import { formatDate } from '../../utils/dates';

export default function MechanicFullCard({ mechanic, currentAssignment, nextAssignment, projectsById }) {
  const status = currentAssignment ? 'assigned' : 'available';
  const currentProject = currentAssignment ? projectsById[currentAssignment.project_id] : null;
  const nextProject = nextAssignment ? projectsById[nextAssignment.project_id] : null;
  const skills = mechanic.skills ? mechanic.skills.split(',').map(s => s.trim()) : [];

  return (
    <Card status={status}>
      <div className="card-header">
        <div className="card-title">{mechanic.name}</div>
        <StatusBadge status={status} />
      </div>
      <div className="card-detail">
        <strong>Skills:</strong>
        <div>{skills.map(s => <SkillTag key={s} skill={s} />)}</div>
      </div>
      <div className="card-detail">
        <strong>Current Project:</strong> {currentProject ? currentProject.name : 'Unassigned'}
        {currentAssignment && (
          <span style={{ color: '#666', fontSize: 12 }}>
            {' — free '}
            <span className="available-date">{formatDate(currentAssignment.end_date)}</span>
          </span>
        )}
      </div>
      {nextProject && (
        <div className="card-detail">
          <strong>Next Project:</strong> {nextProject.name}
          <span style={{ color: '#666', fontSize: 12 }}>
            {' — starts '}{formatDate(nextAssignment.start_date)}
          </span>
        </div>
      )}
    </Card>
  );
}

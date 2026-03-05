import Card from '../shared/Card';
import StatusBadge from '../shared/StatusBadge';
import { formatDate } from '../../utils/dates';

export default function ProjectMiniCard({ project, assignments, mechanicsById }) {
  const current = assignments.find(a => a.sequence === '1');
  const mechanic = current ? mechanicsById[current.mechanic_id] : null;
  const status = project.status.toLowerCase();

  return (
    <Card status={status}>
      <div className="card-header">
        <div className="card-title">{project.name}</div>
        <StatusBadge status={status} />
      </div>
      <div className="card-detail">
        <strong>Start Date:</strong> {formatDate(project.start_date)}
      </div>
      <div className="card-detail">
        <strong>Mechanic:</strong> {mechanic ? mechanic.name : 'Unassigned'}
      </div>
    </Card>
  );
}

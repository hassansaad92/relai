import Card from '../shared/Card';
import StatusBadge from '../shared/StatusBadge';
import { formatDate } from '../../utils/dates';

export default function MechanicMiniCard({ mechanic, currentAssignment, projectsById }) {
  const status = currentAssignment ? 'assigned' : 'available';
  const currentProject = currentAssignment ? projectsById[currentAssignment.project_id] : null;
  const freeDate = currentAssignment ? formatDate(currentAssignment.end_date) : 'Now';

  return (
    <Card status={status}>
      <div className="card-header">
        <div className="card-title">{mechanic.name}</div>
        <StatusBadge status={status} />
      </div>
      <div className="card-detail">
        <strong>Current:</strong> {currentProject ? currentProject.name : 'Unassigned'}
      </div>
      <div className="card-detail">
        <strong>Free:</strong> <span className="available-date">{freeDate}</span>
      </div>
    </Card>
  );
}

export default function StatusBadge({ status }) {
  const label = status.replace('-', ' ');
  return <span className={`card-status ${status}`}>{label}</span>;
}

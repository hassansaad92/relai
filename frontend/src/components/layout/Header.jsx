import { useData } from '../../hooks/useData';
import { getCurrentDate, formatDateLong } from '../../utils/dates';

export default function Header({ title }) {
  const { refresh, loading } = useData();

  return (
    <div className="header">
      <h1>{title}</h1>
      <div className="header-right">
        <button
          className={`refresh-button${loading ? ' loading' : ''}`}
          onClick={refresh}
          disabled={loading}
          title="Refresh data"
        >
          <span className="refresh-icon">↻</span>
        </button>
        <div className="current-date">{formatDateLong(getCurrentDate())}</div>
      </div>
    </div>
  );
}

import { useData } from '../hooks/useData';
import Header from '../components/layout/Header';
import SkillCard from '../components/skills/SkillCard';

export default function SkillsPage() {
  const { skills, loading, error } = useData();

  if (loading) return <><Header title="Skills" /><p>Loading...</p></>;
  if (error) return <><Header title="Skills" /><p style={{ color: 'red' }}>Error: {error}</p></>;

  return (
    <>
      <Header title="Skills" />
      <div className="section">
        <h2>Skills Management</h2>
        {skills.map(s => <SkillCard key={s.skill} skill={s} />)}
      </div>
    </>
  );
}

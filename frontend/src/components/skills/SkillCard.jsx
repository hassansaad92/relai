import Card from '../shared/Card';

export default function SkillCard({ skill }) {
  return (
    <Card>
      <div className="card-title">{skill.skill}</div>
    </Card>
  );
}

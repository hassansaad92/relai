export function buildAssignmentLookups(assignments, mechanics, projects) {
  const mechanicsById = Object.fromEntries(mechanics.map(m => [m.id, m]));
  const projectsById = Object.fromEntries(projects.map(p => [p.id, p]));

  const byMechanic = {};
  const byProject = {};

  for (const a of assignments) {
    if (!byMechanic[a.mechanic_id]) byMechanic[a.mechanic_id] = {};
    byMechanic[a.mechanic_id][a.sequence] = a;

    if (!byProject[a.project_id]) byProject[a.project_id] = [];
    byProject[a.project_id].push(a);
  }

  return { byMechanic, byProject, mechanicsById, projectsById };
}

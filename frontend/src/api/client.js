const BASE = '/api';

async function fetchJSON(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export const getMechanics = () => fetchJSON('/mechanics');
export const getProjects = () => fetchJSON('/projects');
export const getSkills = () => fetchJSON('/skills');
export const getAssignments = () => fetchJSON('/assignments');

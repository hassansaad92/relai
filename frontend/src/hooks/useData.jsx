import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { getMechanics, getProjects, getSkills, getAssignments } from '../api/client';
import { buildAssignmentLookups } from '../utils/lookups';

const DataContext = createContext(null);

export function DataProvider({ children }) {
  const [mechanics, setMechanics] = useState([]);
  const [projects, setProjects] = useState([]);
  const [skills, setSkills] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [lookups, setLookups] = useState({ byMechanic: {}, byProject: {}, mechanicsById: {}, projectsById: {} });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [m, p, s, a] = await Promise.all([
        getMechanics(),
        getProjects(),
        getSkills(),
        getAssignments(),
      ]);
      setMechanics(m);
      setProjects(p);
      setSkills(s);
      setAssignments(a);
      setLookups(buildAssignmentLookups(a, m, p));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  return (
    <DataContext.Provider value={{ mechanics, projects, skills, assignments, lookups, loading, error, refresh }}>
      {children}
    </DataContext.Provider>
  );
}

export function useData() {
  const ctx = useContext(DataContext);
  if (!ctx) throw new Error('useData must be used within DataProvider');
  return ctx;
}

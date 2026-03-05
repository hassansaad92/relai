import { format, differenceInCalendarDays, parseISO } from 'date-fns';

const CURRENT_DATE = new Date('2026-03-01T00:00:00');

export function getCurrentDate() {
  return CURRENT_DATE;
}

export function formatDate(dateStr) {
  return format(parseISO(dateStr), 'M/d/yyyy');
}

export function formatDateLong(date) {
  return format(date, 'EEEE, MMMM d, yyyy');
}

export function calculateTMinus(startDateStr) {
  const start = parseISO(startDateStr);
  const diffDays = differenceInCalendarDays(start, CURRENT_DATE);

  if (diffDays < 0) return 'STARTED';
  if (diffDays === 0) return 'Starts in: T-0 (TODAY)';
  return `Starts in: T-${diffDays} days`;
}

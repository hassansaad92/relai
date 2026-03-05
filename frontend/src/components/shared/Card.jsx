export default function Card({ status, children }) {
  return (
    <div className={`card ${status || ''}`}>
      {children}
    </div>
  );
}

// components/AlertBanner.jsx
export default function AlertBanner({ message, onClose }) {
  return (
    <div className="alert-banner">
      <span>🚨 {message}</span>
      <button onClick={onClose}>✕</button>
    </div>
  );
}

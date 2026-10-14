import "./PageHeader.css";

// Titolo di pagina con, a destra, un elemento facoltativo (bottone, avatar...)
export default function PageHeader({ title, subtitle, right }) {
  return (
    <header className="page-header">
      <div>
        <h1>{title}</h1>
        {subtitle && <p className="muted">{subtitle}</p>}
      </div>
      {right}
    </header>
  );
}

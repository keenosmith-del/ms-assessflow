import { AlertCircle, ArrowUpRight, LoaderCircle } from "lucide-react";
import "./UI.css";
export const titleCase = (value) =>
  (value || "").replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
export function Badge({ status }) {
  return <span className={`badge badge-${status}`}>{titleCase(status)}</span>;
}
export function PageHeading({
  eyebrow = "WORKSPACE",
  title,
  description,
  children,
}) {
  return (
    <header className="page-heading">
      <div>
        <span className="eyebrow">{eyebrow}</span>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      <div className="heading-actions">{children}</div>
    </header>
  );
}
export function Notice({ children }) {
  return (
    <div role="alert" className="notice">
      <AlertCircle size={18} />
      <span>{children}</span>
    </div>
  );
}
export function DataState({ loading, error, children }) {
  if (loading)
    return (
      <div role="status" className="loading">
        <LoaderCircle size={20} /> Loading workspace…
      </div>
    );
  if (error) return <Notice>{error}</Notice>;
  return children;
}
export function Empty({ title = "Nothing here yet", children }) {
  return (
    <div className="empty">
      <ArrowUpRight size={25} />
      <h3>{title}</h3>
      <p>{children}</p>
    </div>
  );
}
export function Field({ label, children }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
    </label>
  );
}
export function Panel({ title, children, aside }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>{title}</h2>
        {aside}
      </div>
      {children}
    </section>
  );
}

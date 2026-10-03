import { Icon, type IconName } from "./Icon";

interface NavItem {
  label: string;
  icon: IconName;
  active?: boolean;
  soon?: boolean;
}

const NAV: NavItem[] = [
  { label: "Home", icon: "home", soon: true },
  { label: "Personas", icon: "users", active: true },
  { label: "Listening", icon: "music", soon: true },
  { label: "Catalogue", icon: "disc", soon: true },
  { label: "Reports", icon: "chart", soon: true },
];

export function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-mark">V</span>
        <span className="brand-name">Vibeout</span>
      </div>
      <nav aria-label="Main">
        <ul className="nav">
          {NAV.map((item) => (
            <li key={item.label}>
              <a
                href="#"
                className={`nav-item${item.active ? " active" : ""}`}
                aria-current={item.active ? "page" : undefined}
                aria-disabled={item.soon || undefined}
                onClick={(e) => e.preventDefault()}
              >
                <Icon name={item.icon} />
                {item.label}
                {item.soon && <span className="soon">Soon</span>}
              </a>
            </li>
          ))}
        </ul>
      </nav>
      <p className="sidebar-note">Synthetic data · Personas simulation</p>
    </aside>
  );
}

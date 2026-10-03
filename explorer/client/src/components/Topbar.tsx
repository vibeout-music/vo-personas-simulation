import { useEffect, useRef } from "react";
import { Icon } from "./Icon";

interface TopbarProps {
  search: string;
  onSearchChange: (value: string) => void;
}

export function Topbar({ search, onSearchChange }: TopbarProps) {
  // useRef gives direct access to the DOM node without causing re-renders.
  const inputRef = useRef<HTMLInputElement>(null);

  // Press "/" anywhere to jump to the search box (like Stripe and GitHub).
  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      const typing = event.target instanceof HTMLElement && ["INPUT", "SELECT", "TEXTAREA"].includes(event.target.tagName);
      if (event.key === "/" && !typing) {
        event.preventDefault();
        inputRef.current?.focus();
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown); // never leak listeners
  }, []);

  return (
    <header className="topbar">
      <label className="search">
        <Icon name="search" />
        <input
          ref={inputRef}
          type="search"
          placeholder="Search personas, occupations, genres…"
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          aria-label="Search personas"
        />
        <kbd>/</kbd>
      </label>
      <div className="topbar-actions">
        <span className="test-badge">Test data</span>
        <button type="button" className="icon-button" aria-label="Help">
          <Icon name="help" />
        </button>
        <button type="button" className="icon-button" aria-label="Notifications">
          <Icon name="bell" />
        </button>
        <span className="me" aria-label="Signed in as Pol">P</span>
      </div>
    </header>
  );
}

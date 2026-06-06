import { NavLink } from "react-router-dom";

export default function RoleSwitch() {
  return (
    <nav className="role-switch" aria-label="Switch interface">
      <NavLink
        to="/"
        end
        className={({ isActive }) => `role-switch-btn ${isActive ? "active" : ""}`}
      >
        Coordinator
      </NavLink>
      <NavLink
        to="/driver"
        className={({ isActive }) => `role-switch-btn ${isActive ? "active" : ""}`}
      >
        Driver
      </NavLink>
    </nav>
  );
}

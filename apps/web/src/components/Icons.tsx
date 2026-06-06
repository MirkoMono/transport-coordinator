import type { ReactNode } from "react";

type IconProps = {
  size?: number;
  className?: string;
};

const defaults = { size: 20, className: "icon" };

function Svg({
  size,
  className,
  children,
  viewBox = "0 0 24 24",
}: IconProps & { children: ReactNode; viewBox?: string }) {
  return (
    <svg
      width={size ?? defaults.size}
      height={size ?? defaults.size}
      viewBox={viewBox}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className ?? defaults.className}
      aria-hidden
    >
      {children}
    </svg>
  );
}

export function IconMap({ size, className }: IconProps) {
  return (
    <Svg size={size} className={className}>
      <path
        d="M12 21s7-4.5 7-11a7 7 0 1 0-14 0c0 6.5 7 11 7 11Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <circle cx="12" cy="10" r="2" stroke="currentColor" strokeWidth="1.5" />
    </Svg>
  );
}

export function IconRoutes({ size, className }: IconProps) {
  return (
    <Svg size={size} className={className}>
      <path d="M8 6h13M8 12h13M8 18h13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="4" cy="6" r="1" fill="currentColor" />
      <circle cx="4" cy="12" r="1" fill="currentColor" />
      <circle cx="4" cy="18" r="1" fill="currentColor" />
    </Svg>
  );
}

export function IconFleet({ size, className }: IconProps) {
  return (
    <Svg size={size} className={className}>
      <path
        d="M3 12h1.5l1.5-4h9l1.5 4H19M5 16h1M18 16h1"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <rect x="6" y="12" width="12" height="5" rx="1" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="8" cy="17" r="1.25" stroke="currentColor" strokeWidth="1.25" />
      <circle cx="16" cy="17" r="1.25" stroke="currentColor" strokeWidth="1.25" />
    </Svg>
  );
}

export function IconClock({ size, className }: IconProps) {
  return (
    <Svg size={size} className={className}>
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.5" />
      <path d="M12 7v5l3 2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </Svg>
  );
}

export function IconUsers({ size, className }: IconProps) {
  return (
    <Svg size={size} className={className}>
      <circle cx="9" cy="8" r="3" stroke="currentColor" strokeWidth="1.5" />
      <path
        d="M3 19c0-3 2.5-5 6-5s6 2 6 5"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
      <path
        d="M16 8.5a2.5 2.5 0 0 1 0 5M19 19c0-2.2-1.5-3.5-3-4"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </Svg>
  );
}

export const TAB_ICONS = {
  map: IconMap,
  routes: IconRoutes,
  fleet: IconFleet,
  history: IconClock,
} as const;

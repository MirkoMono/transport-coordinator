export type DepotLocation = {
  latitude: number;
  longitude: number;
};

export type ProductionSettings = {
  title: string;
  setAddress: string;
  depot: DepotLocation | null;
};

const STORAGE_KEY = "tc:production";
const LEGACY_TITLE_KEY = "tc:productionTitle";

export const DEFAULT_DEPOT: DepotLocation = {
  latitude: 59.3293,
  longitude: 18.0686,
};

export const DEFAULT_SET_ADDRESS = "Stockholm";

export function loadProductionSettings(): ProductionSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as Partial<ProductionSettings>;
      return {
        title: parsed.title ?? "",
        setAddress: parsed.setAddress ?? DEFAULT_SET_ADDRESS,
        depot: parsed.depot ?? DEFAULT_DEPOT,
      };
    }
    const legacyTitle = localStorage.getItem(LEGACY_TITLE_KEY) ?? "";
    return {
      title: legacyTitle,
      setAddress: DEFAULT_SET_ADDRESS,
      depot: DEFAULT_DEPOT,
    };
  } catch {
    return { title: "", setAddress: DEFAULT_SET_ADDRESS, depot: DEFAULT_DEPOT };
  }
}

export function saveProductionSettings(settings: ProductionSettings): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  } catch {
    /* ignore quota errors */
  }
}

/** @deprecated use loadProductionSettings */
export function loadProductionTitle(): string {
  return loadProductionSettings().title;
}

/** @deprecated use saveProductionSettings */
export function saveProductionTitle(title: string): void {
  const current = loadProductionSettings();
  saveProductionSettings({ ...current, title });
}

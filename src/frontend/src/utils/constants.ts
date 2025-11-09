// Re-export from centralized config for backward compatibility
export { API_CONFIG, APP_CONFIG } from "../config/settings";

// Legacy exports (deprecated - use config/settings instead)
/** @deprecated Use API_CONFIG.BASE_URL instead */
export const API_URL = import.meta.env.VITE_API_URL || "/api/v1";

/** @deprecated Use APP_CONFIG.NAME instead */
export const APP_NAME = import.meta.env.VITE_APP_NAME || "Bank Importer TH";

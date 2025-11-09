/**
 * Frontend application settings and configuration.
 *
 * Centralized configuration for the frontend application.
 * Values can be overridden via environment variables (VITE_*).
 */

// API Configuration
export const API_CONFIG = {
  /** Base API URL - defaults to relative path for production */
  BASE_URL: import.meta.env.VITE_API_URL || "/api/v1",

  /** API endpoints */
  ENDPOINTS: {
    PARSERS: "/parsers",
    PARSE: {
      FILE: "/parse/file",
      FILE_EXPORT: "/parse/file/export",
      FILE_PATH: "/parse/file/path",
    },
    CONFIG: {
      BASE: "/config",
      ACCOUNTS: "/config/accounts",
      TARGETS: "/config/targets",
      SETTINGS: "/config/settings",
    },
    IMPORT: {
      FILES: "/import/files",
      SESSIONS: "/import/sessions",
    },
    EXPORT: {
      BASE: "/export",
      SESSIONS: "/export/sessions",
    },
    TRANSACTIONS: "/transactions",
    STATUS: "/status",
    DATABASE: "/database",
    TRANSLATION: "/translation",
    SYSTEM: {
      HEALTH: "/system/health",
      VERSION: "/system/version",
    },
  },
} as const;

// Application Configuration
export const APP_CONFIG = {
  /** Application name */
  NAME: import.meta.env.VITE_APP_NAME || "Bank Importer TH",

  /** Application version (from package.json) */
  VERSION: "0.1.0",
} as const;

// UI Configuration
export const UI_CONFIG = {
  /** Default page size for tables */
  DEFAULT_PAGE_SIZE: 10,

  /** Maximum page size for tables */
  MAX_PAGE_SIZE: 1000,

  /** Date format */
  DATE_FORMAT: "YYYY-MM-DD",

  /** DateTime format */
  DATETIME_FORMAT: "YYYY-MM-DD HH:mm:ss",
} as const;

// File Upload Configuration
export const UPLOAD_CONFIG = {
  /** Maximum file size in bytes (default: 50MB) */
  MAX_FILE_SIZE: 50 * 1024 * 1024,

  /** Allowed file types */
  ALLOWED_TYPES: [".pdf", ".csv", ".txt", ".json"],

  /** Allowed MIME types */
  ALLOWED_MIME_TYPES: [
    "application/pdf",
    "text/csv",
    "text/plain",
    "application/json",
  ],
} as const;

// Export Configuration
export const EXPORT_CONFIG = {
  /** Available export targets */
  TARGETS: {
    CSV: "csv",
    YAML: "yaml",
  } as const,

  /** Default export target */
  DEFAULT_TARGET: "csv",
} as const;

// Error Messages
export const ERROR_MESSAGES = {
  NETWORK_ERROR: "Network error. Please check your connection.",
  FORBIDDEN: "You don't have permission to perform this action.",
  NOT_FOUND: "Resource not found.",
  SERVER_ERROR: "Server error. Please try again later.",
  VALIDATION_ERROR: "Please check your input and try again.",
  FILE_TOO_LARGE: "File is too large. Maximum size is 50MB.",
  INVALID_FILE_TYPE:
    "Invalid file type. Please upload a PDF, CSV, TXT, or JSON file.",
} as const;

// Success Messages
export const SUCCESS_MESSAGES = {
  FILE_UPLOADED: "File uploaded successfully",
  FILE_PARSED: "File parsed successfully",
  EXPORTED: "File exported successfully",
  SAVED: "Changes saved successfully",
} as const;

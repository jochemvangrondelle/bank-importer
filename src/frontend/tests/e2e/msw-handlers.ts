/**
 * MSW handlers auto-generated from OpenAPI specification.
 *
 * This file uses the OpenAPI spec to generate mock handlers,
 * ensuring mocks stay in sync with the API schema.
 */

import { setupServer } from "msw/node";
import { rest } from "msw";
import { generateHandlersFromOpenAPI } from "./openapi-to-msw";

// Generate handlers from OpenAPI spec
const autoHandlers = generateHandlersFromOpenAPI();

// Add custom handlers for endpoints not in OpenAPI spec or needing special handling
const customHandlers: any[] = [];

// Combine all handlers
const handlers = [...autoHandlers, ...customHandlers];

// Create MSW server for Node.js (Playwright)
export const server = setupServer(...handlers);

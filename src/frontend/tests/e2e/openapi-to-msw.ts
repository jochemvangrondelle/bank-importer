/**
 * Auto-generate MSW handlers from OpenAPI specification.
 *
 * This script reads the OpenAPI spec and generates MSW handlers automatically,
 * ensuring mocks stay in sync with the API schema.
 */

import { readFileSync } from "fs";
import { join } from "path";
import { parse } from "yaml";
import type { OpenAPIV3 } from "openapi-types";
import { rest, type RestHandler } from "msw";

/**
 * Load and parse OpenAPI specification.
 */
function loadOpenAPISpec(): OpenAPIV3.Document {
  const specPath = join(__dirname, "../../../../api/openapi.yaml");
  const specContent = readFileSync(specPath, "utf-8");
  return parse(specContent) as OpenAPIV3.Document;
}

/**
 * Generate mock data from JSON schema.
 * Simple implementation - can be enhanced with json-schema-faker.
 */
function generateMockFromSchema(
  schema: OpenAPIV3.SchemaObject | OpenAPIV3.ReferenceObject | undefined
): unknown {
  if (!schema || "$ref" in schema) {
    return {};
  }

  // Handle examples first
  if (schema.example !== undefined) {
    return schema.example;
  }

  // Handle different schema types
  if (schema.type === "object" && schema.properties) {
    const obj: Record<string, unknown> = {};
    Object.entries(schema.properties).forEach(([key, prop]) => {
      obj[key] = generateMockFromSchema(prop);
    });
    return obj;
  }

  if (schema.type === "array" && schema.items) {
    return [generateMockFromSchema(schema.items)];
  }

  // Return default values based on type
  switch (schema.type) {
    case "string":
      if (schema.format === "date-time") {
        return new Date().toISOString();
      }
      if (schema.format === "date") {
        return new Date().toISOString().split("T")[0];
      }
      return schema.enum?.[0] || "mock-string";
    case "number":
    case "integer":
      return schema.default || 0;
    case "boolean":
      return schema.default || false;
    default:
      return null;
  }
}

/**
 * Generate MSW handler for a single endpoint.
 */
function generateHandlerForEndpoint(
  path: string,
  method: string,
  operation: OpenAPIV3.OperationObject
): RestHandler | null {
  // Support both with and without /api/v1 prefix
  const fullPath = `*/api/v1${path}`;
  const altPath = `*${path}`;

  // Find successful response (200 or 201)
  const successResponse =
    operation.responses?.["200"] ||
    operation.responses?.["201"] ||
    Object.values(operation.responses || {})[0];

  if (!successResponse || "$ref" in successResponse) {
    return null;
  }

  const jsonResponse = successResponse.content?.["application/json"];
  const schema = jsonResponse?.schema;

  // Generate mock data
  const mockData = generateMockFromSchema(schema);

  // Create handler based on HTTP method
  switch (method.toUpperCase()) {
    case "GET":
      // Special handling for auth/status endpoint
      if (path === "/auth/status") {
        return rest.get(fullPath, (_req, res, ctx) => {
          return res(ctx.status(200), ctx.json({ password_configured: false }));
        });
      }
      // Return handler for both path patterns
      const getHandler = rest.get(fullPath, (_req, res, ctx) => {
        return res(ctx.status(200), ctx.json(mockData));
      });
      return getHandler;

    case "POST":
      return rest.post(fullPath, async (req, res, ctx) => {
        // For login endpoint, check password
        if (path === "/auth/login") {
          const body = (await req.json()) as { password?: string };
          if (body.password === "admin" || body.password === "testpassword") {
            return res(
              ctx.status(200),
              ctx.json({
                access_token: "mock-jwt-token-for-testing",
                token_type: "bearer",
              })
            );
          }
          return res(
            ctx.status(401),
            ctx.json({ detail: "Incorrect password" })
          );
        }

        return res(ctx.status(200), ctx.json(mockData));
      });

    case "PUT":
      return rest.put(fullPath, (_req, res, ctx) => {
        return res(ctx.status(200), ctx.json(mockData));
      });

    case "DELETE":
      return rest.delete(fullPath, (_req, res, ctx) => {
        return res(ctx.status(200), ctx.json(mockData));
      });

    default:
      return null;
  }
}

/**
 * Generate all MSW handlers from OpenAPI specification.
 */
export function generateHandlersFromOpenAPI(): RestHandler[] {
  const spec = loadOpenAPISpec();
  const handlers: RestHandler[] = [];

  // Iterate through all paths
  Object.entries(spec.paths || {}).forEach(([path, pathItem]) => {
    if (!pathItem || "$ref" in pathItem) {
      return;
    }

    // Generate handlers for each HTTP method
    ["get", "post", "put", "delete", "patch"].forEach((method) => {
      const operation = pathItem[method as keyof typeof pathItem];
      if (operation && typeof operation === "object") {
        const handler = generateHandlerForEndpoint(
          path,
          method,
          operation as OpenAPIV3.OperationObject
        );
        if (handler) {
          handlers.push(handler);
        }
      }
    });
  });

  return handlers;
}

/**
 * Generate handlers with custom overrides for specific endpoints.
 * Useful for endpoints that need special handling (like authentication).
 */
export function generateHandlersWithOverrides(
  overrides: Record<string, RestHandler>
): RestHandler[] {
  const autoHandlers = generateHandlersFromOpenAPI();

  // Replace handlers with overrides where specified
  const handlerMap = new Map<string, RestHandler>();

  autoHandlers.forEach((handler) => {
    // Extract path from handler (simplified - MSW handlers are functions)
    handlerMap.set("auto", handler);
  });

  // Add overrides
  Object.entries(overrides).forEach(([path, handler]) => {
    handlerMap.set(path, handler);
  });

  return Array.from(handlerMap.values());
}

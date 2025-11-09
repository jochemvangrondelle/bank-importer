# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Build arguments for Vite environment variables
ARG VITE_API_URL=/api/v1
ARG VITE_APP_NAME=Bank Importer TH

# Set as environment variables for build
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_APP_NAME=${VITE_APP_NAME}

# Copy package files (build context is project root, so use src/frontend/ prefix)
COPY src/frontend/package.json src/frontend/package-lock.json* ./

# Install dependencies
RUN npm ci

# Copy OpenAPI spec from build context
# The build context is set to project root in docker-compose.yml
# This file should be generated during backend build or CI
COPY api/openapi.yaml ./api/openapi.yaml

# Copy frontend source code (build context is project root)
COPY src/frontend/ ./src/frontend/
# Move frontend contents to app root
RUN mv src/frontend/* . && rmdir src/frontend 2>/dev/null || true

# Generate API client from OpenAPI spec
RUN echo "Generating API client from OpenAPI spec..." && \
    npx openapi-typescript-codegen --input ./api/openapi.yaml --output ./src/api/generated --client axios

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
# Build context is project root, so use src/frontend/nginx.conf
COPY src/frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 3000
EXPOSE 3000

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

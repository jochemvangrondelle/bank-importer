# Bank Importer TH - Frontend

React-based frontend for Bank Importer TH built with Refine and Ant Design.

## Tech Stack

- **React 18** - UI library
- **Refine** - Admin panel framework
- **Ant Design** - UI component library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Playwright** - E2E testing
- **Axios** - HTTP client

## Development

### Prerequisites

- Node.js 20+ and npm
- Backend API running on port 8000 (or configure `VITE_API_URL`)

### Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at `http://localhost:3000`

### Environment Variables

Create a `.env` file (or copy from `.env.example`):

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_APP_NAME=Bank Importer TH
```

### Generate API Client

The API client can be generated from the OpenAPI spec:

```bash
npm run generate:api
```

This generates TypeScript types and client code from `../../api/openapi.yaml`.

## Quick Start

### Development Mode (Local)

1. **Start Backend API** (from project root):

   ```bash
   docker-compose up api
   # Or run directly: uv run bank-importer-api
   ```

2. **Install Dependencies**:

   ```bash
   npm install
   ```

3. **Start Development Server**:
   ```bash
   npm run dev
   ```
   Frontend will be available at `http://localhost:3000`

### Docker Compose (Full Stack)

```bash
# From project root
docker-compose up --build
```

Access:

- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/api/v1/docs

### First Time Setup

1. **Set API Password** (if not already configured):

   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/set-password \
     -H "Content-Type: application/json" \
     -d '{"password": "your-secure-password"}'
   ```

2. **Login** via the web UI at http://localhost:3000/login

## Testing

### E2E Tests with Playwright

```bash
# Run tests
npm run test:e2e

# Run tests in UI mode
npm run test:e2e:ui

# Run tests in headed mode (see browser)
npm run test:e2e:headed

# Debug tests
npm run test:e2e:debug
```

Tests are located in `tests/e2e/` and cover:

- Authentication flow
- Navigation
- Basic UI interactions
- All pages and components

### Test Coverage

Comprehensive test coverage includes:

- **Authentication** (9 tests) - Login, password validation, loading states
- **Home Page** (6 tests) - Content display, navigation, quick links
- **Status Page** (12 tests) - Statistics, tables, error handling
- **Import Wizard** (19 tests) - File upload, parsing, export
- **Navigation** (5 tests) - Page navigation, sidebar, 404 handling
- **PDF Viewer** (4 tests) - Component rendering, loading states
- **App Integration** (6 tests) - Authentication flow, error handling

**Total: 61 test cases** covering all frontend functionality.

See `docs/development/testing.md` for detailed test documentation.

## Building

```bash
# Build for production
npm run build
```

Output will be in the `dist/` directory.

## Docker

### Build and Run

```bash
# From project root
docker-compose up --build frontend
```

Or build individually:

```bash
cd src/frontend
docker build -t bank-importer-frontend .
docker run -p 3000:3000 bank-importer-frontend
```

## Project Structure

```
src/frontend/
├── src/
│   ├── pages/          # Page components
│   ├── providers/      # Refine providers (auth, data)
│   ├── utils/          # Utilities (axios, constants)
│   └── App.tsx         # Main app component
├── tests/
│   └── e2e/            # Playwright E2E tests
├── public/             # Static assets
└── dist/               # Build output
```

## Features

- ✅ Authentication (JWT-based)
- ✅ Login page
- ✅ Home page
- ✅ Responsive design
- ✅ E2E tests

## Coming Soon

- Configuration wizard
- Import wizard
- Status dashboard
- Transaction browser

## License

PolyForm Noncommercial License 1.0.0 (same as main project)

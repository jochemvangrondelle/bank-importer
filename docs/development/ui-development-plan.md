# Frontend UI Development Plan

## Framework Recommendation: **Refine**

### Why Refine?

After analyzing the project requirements and comparing frameworks (Appsmith, Tooljet, Flowise, Refine), **Refine** is the best fit for this project:

#### ✅ **Perfect Match for Requirements**

- **Built for REST APIs**: Refine is specifically designed for admin panels connecting to REST APIs (like your FastAPI backend)
- **Highly Customizable**: React-based framework allows full control over UI/UX, including custom layouts like the split-view import wizard
- **File Upload Support**: Excellent file upload components with preview capabilities
- **Authentication**: Built-in JWT authentication support matching your API's auth system
- **Form Builders**: Powerful form components perfect for config wizards
- **Data Tables**: Advanced data table components with filtering, sorting, pagination
- **Active Development**: Well-maintained with good documentation and community

#### ❌ **Why Not Others?**

- **Appsmith/Tooljet**: Too limiting for custom UI (split-view would be difficult), less flexible
- **Flowise**: Wrong tool - designed for LLM workflows, not admin panels

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Refine)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │  Login   │  │  Config  │  │  Import  │  │  Status  │ │
│  │   Page   │  │  Wizard  │  │  Wizard  │  │   Page   │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ HTTP/REST
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Backend (FastAPI - Already Exists)              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │   Auth   │  │  Config  │  │  Import  │  │  Status  │ │
│  │  Router  │  │  Router  │  │  Router  │  │  Router  │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Plan

### Phase 1: Project Setup & Authentication

#### 1.1 Initialize Refine Project

- [ ] Create new Refine project: `npx create-refine-app@latest bank-importer-ui`
- [ ] Choose options:
  - Framework: **React + Vite**
  - UI Framework: **Ant Design** (recommended) or **Material UI**
  - Data Provider: **REST API**
  - Authentication: **Custom** (JWT)
- [ ] Configure API base URL: `http://localhost:8000/api/v1`
- [ ] Set up environment variables for API endpoints

#### 1.2 Authentication Implementation

- [ ] Create custom auth provider connecting to `/api/v1/auth/login`
- [ ] Implement login page with password field
- [ ] Store JWT token in localStorage/sessionStorage
- [ ] Add token to all API requests via axios interceptors
- [ ] Implement logout functionality
- [ ] Handle token expiration and refresh
- [ ] Create initial password setup flow (if no password configured)

**API Endpoints to Use:**

- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/status` - Check if password configured
- `POST /api/v1/auth/set-password` - Set initial password

### Phase 2: Configuration Wizard

#### 2.1 Application Settings Page

- [ ] Create settings form with fields:
  - Timezone selector (dropdown)
  - Database URL (read-only display)
  - Output directory path
  - Translation settings:
    - Enable/disable translation
    - Source language (default: TH)
    - Target language (default: en)
    - Translation cache file path
    - Google Translate API key (password field)
- [ ] Add form validation
- [ ] Implement save functionality (`PATCH /api/v1/config/settings`)

**API Endpoints:**

- `GET /api/v1/config/settings` - Get settings
- `PATCH /api/v1/config/settings` - Update settings

#### 2.2 Bank Accounts Management

- [ ] Create accounts list page (data table)
- [ ] Add "Create Account" button
- [ ] Create account form wizard with steps:
  - **Step 1: Basic Info**
    - Account name (required)
    - Bank name (dropdown: Krungsri, SCB, Amex, Generic)
    - Account number
    - Account holder name
    - Branch name
    - Currency (default: THB)
    - Country code (default: TH)
    - Reference
  - **Step 2: Parser Configuration**
    - Parser selection (dropdown based on `/api/v1/parsers`)
    - File path (directory picker or text input)
    - File pattern (e.g., `*.pdf`, `*AcctSt_*.pdf`)
    - Password (for encrypted PDFs, password field)
    - Password file path (optional)
  - **Step 3: Translation Settings**
    - Enable translation (toggle)
    - Source language
    - Target language
    - Use term mapping (toggle)
    - Use API translation (toggle)
    - Preserve original (toggle)
- [ ] Add edit account functionality
- [ ] Add delete account with confirmation
- [ ] Show parser detection results

**API Endpoints:**

- `GET /api/v1/config/accounts` - List accounts
- `POST /api/v1/config/accounts` - Create account
- `GET /api/v1/config/accounts/{account_name}` - Get account
- `PUT /api/v1/config/accounts/{account_name}` - Update account
- `DELETE /api/v1/config/accounts/{account_name}` - Delete account
- `GET /api/v1/parsers` - List available parsers

#### 2.3 Export Targets Management

- [ ] Create targets list page
- [ ] Add "Create Target" button
- [ ] Create target form with:
  - Target name (required)
  - Enabled toggle
  - Output directory (optional override)
  - Target-specific configuration (JSON editor or structured form)
    - CSV: date format, delimiter, Firefly-III options
    - YAML: include summary, group by month
    - Firefly-III: API endpoint, API key, etc.
- [ ] Add edit/delete functionality

**API Endpoints:**

- `GET /api/v1/config/targets` - List targets
- `POST /api/v1/config/targets` - Create target
- `GET /api/v1/config/targets/{target_name}` - Get target
- `PUT /api/v1/config/targets/{target_name}` - Update target
- `DELETE /api/v1/config/targets/{target_name}` - Delete target

### Phase 3: Import Wizard

#### 3.1 File Upload & Selection

- [ ] Create import wizard page with split layout
- [ ] Left panel: File upload/selection
  - File upload component (drag & drop)
  - File browser to select existing files
  - Account selector (dropdown)
  - File preview (PDF viewer or text preview)
  - Show file metadata (size, type, last modified)
- [ ] Right panel: Parsed transactions preview
  - Initially empty/loading state
  - Transaction table with columns:
    - Date
    - Description (original + translated)
    - Amount (with color coding: green for credit, red for debit)
    - Balance
    - Transaction type
    - Reference
  - Pagination for large files
  - Filter/search functionality
- [ ] Add "Detect Parser" button (calls `/api/v1/parsers/detect`)
- [ ] Show parser detection results

#### 3.2 Import Execution

- [ ] Add "Import" button
- [ ] Show import progress (poll `/api/v1/import/sessions/{session_id}`)
- [ ] Display import results:
  - Success count
  - Error count
  - Warnings
- [ ] Show import session details
- [ ] Link to view all transactions from this import

**API Endpoints:**

- `POST /api/v1/import/files` - Start import (async job)
- `GET /api/v1/import/sessions` - List import sessions
- `GET /api/v1/import/sessions/{session_id}` - Get session details
- `GET /api/v1/import/sessions/{session_id}/transactions` - Get transactions
- `POST /api/v1/parsers/detect` - Detect parser for file

### Phase 4: Status & Overview Page

#### 4.1 Dashboard Overview

- [ ] Create dashboard page with cards showing:
  - Total accounts
  - Total transactions
  - Total import sessions
  - Recent activity timeline
- [ ] Add date range filter
- [ ] Show account status cards:
  - Account name
  - Bank name
  - Transaction count
  - Last import date
  - Date range of transactions
  - Status indicator (healthy/warning/error)

#### 4.2 Import Sessions List

- [ ] Create import sessions table with:
  - Session ID
  - Account name
  - File path
  - Status badge (pending/processing/completed/failed)
  - Transaction count
  - Started at / Completed at
  - Actions: View details, View transactions, Download
- [ ] Add filtering by account, status, date range
- [ ] Add pagination

#### 4.3 Transaction Browser

- [ ] Create transactions list page
- [ ] Add filters:
  - Account name
  - Date range
  - Transaction type
  - Category
  - Amount range
- [ ] Add search by description
- [ ] Show transaction details modal
- [ ] Allow editing transaction (category, memo, translated description)
- [ ] Bulk actions (export selected, translate selected)

**API Endpoints:**

- `GET /api/v1/status` - Get system status
- `GET /api/v1/status/accounts` - Get account status
- `GET /api/v1/status/accounts/{account_name}` - Get account status
- `GET /api/v1/transactions` - List transactions
- `GET /api/v1/transactions/{transaction_id}` - Get transaction
- `PATCH /api/v1/transactions/{transaction_id}` - Update transaction

### Phase 5: Export Functionality

#### 5.1 Export Wizard

- [ ] Create export page
- [ ] Add export options:
  - Target selection (multi-select)
  - Account selection (all or specific)
  - Date range
  - Dry run option
- [ ] Show export progress
- [ ] Display export results
- [ ] Add download links for exported files

**API Endpoints:**

- `POST /api/v1/export` - Start export (async job)
- `GET /api/v1/export/sessions` - List export sessions
- `GET /api/v1/export/sessions/{session_id}` - Get export session
- `GET /api/v1/export/sessions/{session_id}/download` - Download file

### Phase 6: Polish & UX Improvements

#### 6.1 UI/UX Enhancements

- [ ] Add loading states for all async operations
- [ ] Add error handling and user-friendly error messages
- [ ] Add success notifications
- [ ] Implement responsive design (mobile-friendly)
- [ ] Add keyboard shortcuts
- [ ] Add breadcrumb navigation
- [ ] Add help tooltips

#### 6.2 Advanced Features

- [ ] Add transaction translation UI (translate selected transactions)
- [ ] Add bulk transaction editing
- [ ] Add export templates/presets
- [ ] Add import history visualization (charts)
- [ ] Add duplicate detection UI
- [ ] Add file comparison view (before/after parsing)

## Technical Stack

### Frontend

- **Framework**: React 18+ with Vite
- **UI Library**: Ant Design (recommended) or Material UI
- **State Management**: React Query (for server state) + Zustand/Context (for client state)
- **Form Handling**: React Hook Form + Zod validation
- **HTTP Client**: Axios with interceptors
- **Routing**: React Router
- **File Upload**: Ant Design Upload or react-dropzone
- **PDF Viewer**: react-pdf or pdf.js
- **Charts**: Recharts or Chart.js

### Development Tools

- **TypeScript**: Full type safety
- **ESLint + Prettier**: Code quality
- **Vitest**: Unit testing
- **React Testing Library**: Component testing

## Project Structure

```
bank-importer-ui/
├── src/
│   ├── components/
│   │   ├── auth/
│   │   │   ├── LoginForm.tsx
│   │   │   └── PasswordSetup.tsx
│   │   ├── config/
│   │   │   ├── SettingsForm.tsx
│   │   │   ├── AccountForm.tsx
│   │   │   └── TargetForm.tsx
│   │   ├── import/
│   │   │   ├── ImportWizard.tsx
│   │   │   ├── FileUpload.tsx
│   │   │   ├── FilePreview.tsx
│   │   │   └── TransactionPreview.tsx
│   │   ├── status/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── AccountStatus.tsx
│   │   │   └── ImportSessions.tsx
│   │   └── common/
│   │       ├── Layout.tsx
│   │       ├── Navigation.tsx
│   │       └── ErrorBoundary.tsx
│   ├── pages/
│   │   ├── Login.tsx
│   │   ├── Config.tsx
│   │   ├── Import.tsx
│   │   └── Status.tsx
│   ├── providers/
│   │   ├── AuthProvider.tsx
│   │   └── RefineProvider.tsx
│   ├── api/
│   │   ├── client.ts
│   │   ├── auth.ts
│   │   ├── config.ts
│   │   ├── import.ts
│   │   └── transactions.ts
│   ├── hooks/
│   │   └── useAuth.ts
│   ├── utils/
│   │   ├── formatters.ts
│   │   └── validators.ts
│   └── App.tsx
├── public/
└── package.json
```

## Getting Started

### Quick Start Commands

```bash
# 1. Create Refine project
npx create-refine-app@latest bank-importer-ui

# 2. Navigate to project
cd bank-importer-ui

# 3. Install additional dependencies (if needed)
npm install axios react-pdf recharts

# 4. Start development server
npm run dev

# 5. Start backend API (in separate terminal)
cd /path/to/bank-importer
uv run bank-importer-api
```

### Environment Variables

Create `.env` file:

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_APP_NAME=Bank Importer TH
```

## API Integration Notes

### Authentication Flow

1. Check if password is configured: `GET /api/v1/auth/status`
2. If not configured, show password setup form
3. If configured, show login form
4. On login, store JWT token
5. Include token in all requests: `Authorization: Bearer <token>`

### Error Handling

- Handle 401 (Unauthorized) → Redirect to login
- Handle 403 (Forbidden) → Show error message
- Handle 500 (Server Error) → Show generic error with retry option
- Handle network errors → Show connection error

### File Upload

- Use `multipart/form-data` for file uploads
- Show upload progress
- Handle large files (chunked upload if needed)
- Validate file types before upload

## Future Enhancements

- [ ] Real-time updates via WebSockets
- [ ] Dark mode
- [ ] Multi-language UI (i18n)
- [ ] Export/import configuration
- [ ] Transaction categorization AI suggestions
- [ ] Integration with Firefly-III API (direct import)
- [ ] Mobile app (React Native)

## Resources

- [Refine Documentation](https://refine.dev/docs/)
- [Ant Design Components](https://ant.design/components/overview/)
- [React Query](https://tanstack.com/query/latest)
- [FastAPI Backend API Docs](http://localhost:8000/api/v1/docs)

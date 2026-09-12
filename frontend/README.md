# RAGVault Frontend

React + TypeScript + Vite + Tailwind single-page client for the RAGVault API.

## Running

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # type-check + production bundle
npm run lint
```

The backend must be reachable and allow the dev origin via CORS
(`http://localhost:5173` — already configured in `backend/app/main.py`).

### API base URL

Defaults to `http://localhost:8000/api/v1`. Override with an env var:

```bash
# .env.local
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## Features

- **Auth**: login by username or email, OTP-verified registration, forgot/reset
  password, change password, logout. Access + refresh tokens are persisted and
  401s transparently refresh (with a single shared in-flight refresh) and retry.
- **Documents**: paginated list, drag-and-drop upload (`.txt` / `.csv` / `.md`,
  50 MB max, idempotency keyed), delete with confirmation, and a paginated text
  viewer.

## Structure

```
src/
  api/        fetch client, token store, auth + document endpoints
  context/    AuthProvider (session) and ToastProvider (notifications)
  components/ auth forms, document list/viewer/upload, UI primitives
  pages/      LoginRegister and Dashboard
  types/      request/response contracts
  utils/      validation mirrors + formatting
```

---

# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])

```

You can also install [eslint-plugin-react-x](https://npmx.dev/package/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://npmx.dev/package/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])

```

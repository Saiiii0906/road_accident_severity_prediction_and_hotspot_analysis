# Vantage — Frontend Application

This directory contains the client-side single-page application for **Vantage**—an AI-powered road safety intelligence and traffic risk analysis platform.

---

## Technology Stack

- **Framework:** [TanStack Start](https://tanstack.com/start) (Full-stack React framework on Vite & Nitro)
- **UI Library:** React 19 (`react@^19.2.0`, `react-dom@^19.2.0`)
- **Routing:** `@tanstack/react-router` (Type-safe, file-based routing)
- **Styling:** Tailwind CSS v4 (`tailwindcss@^4.2.1`)
- **Components:** Radix UI primitives (`@radix-ui/react-*`), Lucide React icons
- **State Management:** `@tanstack/react-query` (`^5.101.1`)
- **Mapping:** Leaflet
- **Document Generation:** `jspdf` & `jspdf-autotable`

---

## Local Development

### 1. Install Dependencies

```bash
npm install
```

### 2. Start Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:5173`.

### 3. Production Build

```bash
npm run build
```

---

## Documentation

For a comprehensive guide to the frontend architecture, component layout, route structure, client-side history persistence, and PDF export system, please refer to:

- [**Frontend Architecture Documentation**](../docs/frontend.md)
- [**Frontend Design System**](../docs/design-system.md)
- [**Root Repository Documentation**](../docs/README.md)

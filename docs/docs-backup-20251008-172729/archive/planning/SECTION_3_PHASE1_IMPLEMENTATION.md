# Section 3: Phase 1 Implementation (Foundation)

**Document**: Modern Web Interface Development Plan
**Section**: 3 of 10
**Focus**: Foundation Phase - Development Environment & Core Infrastructure

---

## 🎯 **PHASE 1 OBJECTIVES**

### **Primary Goals**
- Establish robust development environment and toolchain
- Create foundational project structure and architecture
- Implement core infrastructure components
- Set up automated testing and quality assurance pipeline
- Build basic UI framework and design system
- Create initial routing and navigation structure

### **Success Criteria**
- ✅ Development environment fully configured and documented
- ✅ CI/CD pipeline operational with automated testing
- ✅ Basic application structure with routing functional
- ✅ Design system components library created
- ✅ Core infrastructure services implemented
- ✅ Development workflow established and team-ready

### **Timeline Estimation**
- **Duration**: 2-3 weeks
- **Effort**: 60-80 hours
- **Team Size**: 1-2 developers + 1 designer (optional)

---

## 🏗️ **IMPLEMENTATION ROADMAP**

### **Week 1: Environment Setup & Project Foundation**

#### **Days 1-2: Development Environment Setup**

**Task 1.1: Project Initialization**
```bash
# Create new React project with Vite
npm create vite@latest omics-oracle-web -- --template react-ts
cd omics-oracle-web

# Install core dependencies
npm install react@^18.2.0 react-dom@^18.2.0
npm install @types/react@^18.2.0 @types/react-dom@^18.2.0
npm install typescript@^5.0.0 vite@^4.3.0

# Install routing and state management
npm install react-router-dom@^6.11.0
npm install zustand@^4.3.0 immer@^10.0.0

# Install UI framework
npm install tailwindcss@^3.3.0 autoprefixer@^3.0.0 postcss@^8.4.0
npm install @headlessui/react@^1.7.0 @heroicons/react@^2.0.0
npm install clsx@^1.2.0 tailwind-merge@^1.12.0

# Install data fetching
npm install @tanstack/react-query@^4.29.0 axios@^1.4.0

# Install development dependencies
npm install -D @types/node@^20.3.0
npm install -D eslint@^8.42.0 @typescript-eslint/parser@^5.59.0
npm install -D prettier@^2.8.0 eslint-config-prettier@^8.8.0
npm install -D husky@^8.0.0 lint-staged@^13.2.0
```

**Task 1.2: Configuration Files Setup**

**Vite Configuration** (`vite.config.ts`):
```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
      '@components': path.resolve(__dirname, 'src/components'),
      '@pages': path.resolve(__dirname, 'src/pages'),
      '@hooks': path.resolve(__dirname, 'src/hooks'),
      '@utils': path.resolve(__dirname, 'src/utils'),
      '@types': path.resolve(__dirname, 'src/types'),
      '@api': path.resolve(__dirname, 'src/api'),
      '@store': path.resolve(__dirname, 'src/store')
    }
  },
  server: {
    port: 3000,
    open: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
    }
  },
  build: {
    target: 'es2020',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          router: ['react-router-dom'],
          ui: ['@headlessui/react', '@heroicons/react'],
          utils: ['axios', 'clsx', 'tailwind-merge']
        }
      }
    }
  }
});
```

**TypeScript Configuration** (`tsconfig.json`):
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@components/*": ["src/components/*"],
      "@pages/*": ["src/pages/*"],
      "@hooks/*": ["src/hooks/*"],
      "@utils/*": ["src/utils/*"],
      "@types/*": ["src/types/*"],
      "@api/*": ["src/api/*"],
      "@store/*": ["src/store/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

**Tailwind Configuration** (`tailwind.config.js`):
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        gray: {
          50: '#f9fafb',
          100: '#f3f4f6',
          200: '#e5e7eb',
          300: '#d1d5db',
          400: '#9ca3af',
          500: '#6b7280',
          600: '#4b5563',
          700: '#374151',
          800: '#1f2937',
          900: '#111827',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'monospace']
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem'
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    require('@tailwindcss/aspect-ratio')
  ],
}
```

#### **Days 3-4: Project Structure & Core Infrastructure**

**Task 1.3: Directory Structure Setup**
```
src/
├── api/                 # API clients and endpoints
│   ├── client.ts
│   ├── search.ts
│   ├── export.ts
│   └── types.ts
├── components/          # Reusable components
│   ├── ui/             # Base UI components
│   │   ├── Button/
│   │   ├── Input/
│   │   ├── Modal/
│   │   └── index.ts
│   ├── layout/         # Layout components
│   │   ├── Header/
│   │   ├── Sidebar/
│   │   ├── Footer/
│   │   └── PageLayout/
│   └── features/       # Feature-specific components
│       ├── search/
│       ├── results/
│       └── export/
├── hooks/              # Custom React hooks
│   ├── useSearch.ts
│   ├── useDebounce.ts
│   └── useLocalStorage.ts
├── pages/              # Page components
│   ├── SearchPage/
│   ├── ResultsPage/
│   ├── ExportPage/
│   └── NotFoundPage/
├── store/              # State management
│   ├── slices/
│   │   ├── searchSlice.ts
│   │   ├── uiSlice.ts
│   │   └── userSlice.ts
│   ├── index.ts
│   └── types.ts
├── types/              # TypeScript type definitions
│   ├── api.ts
│   ├── search.ts
│   └── global.ts
├── utils/              # Utility functions
│   ├── api.ts
│   ├── format.ts
│   ├── validation.ts
│   └── constants.ts
├── styles/             # Global styles
│   ├── globals.css
│   └── components.css
├── App.tsx
├── main.tsx
└── vite-env.d.ts
```

**Task 1.4: Core Infrastructure Implementation**

**API Client Setup** (`src/api/client.ts`):
```typescript
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

class APIClient {
  private instance: AxiosInstance;

  constructor(baseURL: string = '/api') {
    this.instance = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // Request interceptor
    this.instance.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.instance.interceptors.response.use(
      (response: AxiosResponse) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.get<T>(url, config);
    return response.data;
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.post<T>(url, data, config);
    return response.data;
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.put<T>(url, data, config);
    return response.data;
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.delete<T>(url, config);
    return response.data;
  }
}

export const apiClient = new APIClient();
export default APIClient;
```

**Error Boundary Implementation** (`src/components/ErrorBoundary.tsx`):
```typescript
import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    this.props.onError?.(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="flex items-center justify-center min-h-screen bg-gray-50">
          <div className="text-center">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              Something went wrong
            </h2>
            <p className="text-gray-600 mb-6">
              We're sorry, but something unexpected happened.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
```

#### **Days 5-7: Testing Setup & Quality Assurance Pipeline**

**Task 1.5: Testing Framework Setup**
```bash
# Install testing dependencies
npm install -D vitest@^0.31.0 @vitest/ui@^0.31.0
npm install -D @testing-library/react@^14.0.0 @testing-library/jest-dom@^5.16.0
npm install -D @testing-library/user-event@^14.4.0
npm install -D jsdom@^22.1.0

# Install E2E testing
npm install -D playwright@^1.35.0 @playwright/test@^1.35.0
```

**Vitest Configuration** (`vitest.config.ts`):
```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: true,
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
      '@components': path.resolve(__dirname, 'src/components'),
      '@pages': path.resolve(__dirname, 'src/pages'),
      '@hooks': path.resolve(__dirname, 'src/hooks'),
      '@utils': path.resolve(__dirname, 'src/utils'),
      '@types': path.resolve(__dirname, 'src/types'),
      '@api': path.resolve(__dirname, 'src/api'),
      '@store': path.resolve(__dirname, 'src/store')
    }
  }
});
```

**Test Setup File** (`src/test/setup.ts`):
```typescript
import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
global.localStorage = localStorageMock;

// Mock sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
global.sessionStorage = sessionStorageMock;

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});
```

**Task 1.6: ESLint and Prettier Configuration**

**ESLint Configuration** (`.eslintrc.json`):
```json
{
  "env": {
    "browser": true,
    "es2020": true
  },
  "extends": [
    "eslint:recommended",
    "@typescript-eslint/recommended",
    "plugin:react/recommended",
    "plugin:react-hooks/recommended",
    "plugin:@typescript-eslint/recommended",
    "prettier"
  ],
  "parser": "@typescript-eslint/parser",
  "parserOptions": {
    "ecmaFeatures": {
      "jsx": true
    },
    "ecmaVersion": "latest",
    "sourceType": "module"
  },
  "plugins": [
    "react",
    "react-hooks",
    "@typescript-eslint"
  ],
  "rules": {
    "react/react-in-jsx-scope": "off",
    "react/prop-types": "off",
    "@typescript-eslint/no-unused-vars": ["error", { "argsIgnorePattern": "^_" }],
    "@typescript-eslint/explicit-function-return-type": "off",
    "@typescript-eslint/explicit-module-boundary-types": "off",
    "@typescript-eslint/no-explicit-any": "warn"
  },
  "settings": {
    "react": {
      "version": "detect"
    }
  }
}
```

**Prettier Configuration** (`.prettierrc`):
```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 80,
  "tabWidth": 2,
  "useTabs": false,
  "bracketSpacing": true,
  "arrowParens": "avoid",
  "endOfLine": "lf"
}
```

---

### **Week 2: UI Framework & Design System**

#### **Days 8-10: Base UI Components Library**

**Task 2.1: Button Component**

**Button Implementation** (`src/components/ui/Button/Button.tsx`):
```typescript
import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/utils/cn';

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none ring-offset-background',
  {
    variants: {
      variant: {
        default: 'bg-primary-600 text-white hover:bg-primary-700',
        destructive: 'bg-red-600 text-white hover:bg-red-700',
        outline: 'border border-gray-300 bg-white hover:bg-gray-50 hover:text-gray-900',
        secondary: 'bg-gray-100 text-gray-900 hover:bg-gray-200',
        ghost: 'hover:bg-gray-100 hover:text-gray-900',
        link: 'underline-offset-4 hover:underline text-primary-600',
      },
      size: {
        default: 'h-10 py-2 px-4',
        sm: 'h-9 px-3 rounded-md',
        lg: 'h-11 px-8 rounded-md',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  loading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, loading, disabled, children, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={disabled || loading}
        {...props}
      >
        {loading && (
          <svg
            className="animate-spin -ml-1 mr-2 h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        )}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';
```

**Button Tests** (`src/components/ui/Button/Button.test.tsx`):
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Button } from './Button';

describe('Button', () => {
  it('renders with default props', () => {
    render(<Button>Click me</Button>);
    const button = screen.getByRole('button', { name: /click me/i });
    expect(button).toBeInTheDocument();
    expect(button).toHaveClass('bg-primary-600');
  });

  it('handles click events', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);

    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('shows loading state', () => {
    render(<Button loading>Loading</Button>);
    const button = screen.getByRole('button');

    expect(button).toBeDisabled();
    expect(screen.getByRole('button')).toContainElement(
      screen.getByRole('img', { hidden: true })
    );
  });

  it('applies variant classes correctly', () => {
    render(<Button variant="outline">Outline Button</Button>);
    const button = screen.getByRole('button');

    expect(button).toHaveClass('border');
    expect(button).toHaveClass('bg-white');
  });

  it('applies size classes correctly', () => {
    render(<Button size="lg">Large Button</Button>);
    const button = screen.getByRole('button');

    expect(button).toHaveClass('h-11');
    expect(button).toHaveClass('px-8');
  });
});
```

**Task 2.2: Input Component**

**Input Implementation** (`src/components/ui/Input/Input.tsx`):
```typescript
import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/utils/cn';

const inputVariants = cva(
  'flex w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm ring-offset-white file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-gray-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
  {
    variants: {
      size: {
        default: 'h-10',
        sm: 'h-9 px-2 text-xs',
        lg: 'h-11 px-4',
      },
      variant: {
        default: 'border-gray-300',
        error: 'border-red-500 focus-visible:ring-red-500',
      },
    },
    defaultVariants: {
      size: 'default',
      variant: 'default',
    },
  }
);

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement>,
    VariantProps<typeof inputVariants> {
  label?: string;
  error?: string;
  helpText?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, size, variant, label, error, helpText, id, ...props }, ref) => {
    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;
    const hasError = !!error;

    return (
      <div className="space-y-2">
        {label && (
          <label
            htmlFor={inputId}
            className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
          >
            {label}
          </label>
        )}
        <input
          type={type}
          className={cn(
            inputVariants({
              size,
              variant: hasError ? 'error' : variant,
              className
            })
          )}
          ref={ref}
          id={inputId}
          {...props}
        />
        {(error || helpText) && (
          <p className={cn(
            'text-sm',
            error ? 'text-red-600' : 'text-gray-500'
          )}>
            {error || helpText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
```

#### **Days 11-14: Layout Components & Navigation**

**Task 2.3: Header Component**

**Header Implementation** (`src/components/layout/Header/Header.tsx`):
```typescript
import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { cn } from '@/utils/cn';
import { Button } from '@components/ui/Button/Button';
import {
  MagnifyingGlassIcon,
  DocumentArrowDownIcon,
  ChartBarIcon,
  Bars3Icon,
  XMarkIcon
} from '@heroicons/react/24/outline';

const navigation = [
  { name: 'Search', href: '/search', icon: MagnifyingGlassIcon },
  { name: 'Results', href: '/results', icon: ChartBarIcon },
  { name: 'Export', href: '/export', icon: DocumentArrowDownIcon },
];

export const Header: React.FC = () => {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-primary-600 rounded-md flex items-center justify-center">
                <span className="text-white font-bold text-sm">OO</span>
              </div>
              <span className="font-semibold text-gray-900 text-lg">
                OmicsOracle
              </span>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex space-x-8">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    'inline-flex items-center px-1 pt-1 text-sm font-medium border-b-2 transition-colors',
                    isActive
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  )}
                >
                  <item.icon className="w-4 h-4 mr-2" />
                  {item.name}
                </Link>
              );
            })}
          </nav>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? (
                <XMarkIcon className="w-6 h-6" />
              ) : (
                <Bars3Icon className="w-6 h-6" />
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Mobile Navigation */}
      {mobileMenuOpen && (
        <div className="md:hidden">
          <div className="pt-2 pb-3 space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    'block pl-3 pr-4 py-2 text-base font-medium border-l-4 transition-colors',
                    isActive
                      ? 'bg-primary-50 border-primary-500 text-primary-700'
                      : 'border-transparent text-gray-600 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-800'
                  )}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <div className="flex items-center">
                    <item.icon className="w-5 h-5 mr-3" />
                    {item.name}
                  </div>
                </Link>
              );
            })}
          </div>
        </div>
      )}
    </header>
  );
};
```

**Task 2.4: Page Layout Component**

**PageLayout Implementation** (`src/components/layout/PageLayout/PageLayout.tsx`):
```typescript
import React from 'react';
import { Header } from '../Header/Header';
import { ErrorBoundary } from '@components/ErrorBoundary';

interface PageLayoutProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  actions?: React.ReactNode;
}

export const PageLayout: React.FC<PageLayoutProps> = ({
  children,
  title,
  subtitle,
  actions,
}) => {
  React.useEffect(() => {
    if (title) {
      document.title = `${title} - OmicsOracle`;
    }
  }, [title]);

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <ErrorBoundary>
        <main className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
          {(title || subtitle || actions) && (
            <div className="mb-8 sm:flex sm:items-center sm:justify-between">
              <div>
                {title && (
                  <h1 className="text-3xl font-bold leading-tight text-gray-900">
                    {title}
                  </h1>
                )}
                {subtitle && (
                  <p className="mt-2 text-sm text-gray-600">{subtitle}</p>
                )}
              </div>
              {actions && (
                <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
                  {actions}
                </div>
              )}
            </div>
          )}
          {children}
        </main>
      </ErrorBoundary>
    </div>
  );
};
```

---

## 📋 **IMPLEMENTATION CHECKLIST**

### **Development Environment**
- [ ] Project initialized with Vite + React + TypeScript
- [ ] All core dependencies installed and configured
- [ ] Path aliases set up for clean imports
- [ ] Development server configured with API proxy
- [ ] Build configuration optimized with code splitting

### **Code Quality & Testing**
- [ ] ESLint configuration with TypeScript and React rules
- [ ] Prettier configuration for consistent formatting
- [ ] Husky pre-commit hooks configured
- [ ] Vitest testing framework set up with jsdom
- [ ] Testing utilities and mocks configured
- [ ] Playwright E2E testing framework installed

### **UI Framework & Design System**
- [ ] Tailwind CSS configured with custom theme
- [ ] Base UI components implemented (Button, Input)
- [ ] Component library structure established
- [ ] Responsive design system in place
- [ ] Accessibility considerations implemented

### **Core Infrastructure**
- [ ] API client with interceptors and error handling
- [ ] Error boundary components implemented
- [ ] Global error handling strategy
- [ ] Type definitions for API responses
- [ ] Utility functions for common operations

### **Navigation & Layout**
- [ ] React Router configured with route structure
- [ ] Header component with responsive navigation
- [ ] Page layout component with consistent structure
- [ ] Mobile-responsive navigation menu
- [ ] Loading states and error boundaries

---

## 🎯 **DELIVERABLES & NEXT STEPS**

### **Phase 1 Deliverables**
1. **Fully configured development environment** with all tools and dependencies
2. **Project structure** following best practices and scalability patterns
3. **Core UI component library** with Button, Input, and layout components
4. **Testing infrastructure** with unit and E2E testing capabilities
5. **API client architecture** ready for backend integration
6. **Navigation system** with responsive design and accessibility

### **Handoff to Phase 2**
- Development environment documented and ready for team collaboration
- Core infrastructure components tested and validated
- Design system foundation established for consistent UI development
- CI/CD pipeline ready for automated testing and deployment
- Project structure scalable for feature development

### **Success Validation**
- [ ] Development server starts without errors
- [ ] All tests pass (unit and integration)
- [ ] Build process completes successfully
- [ ] Navigation works across all breakpoints
- [ ] Core components render and function correctly
- [ ] API client can communicate with backend (mock or real)

---

**Next Section**: [Section 4: Phase 2 Implementation (Core Features)](./SECTION_4_PHASE2_IMPLEMENTATION.md)

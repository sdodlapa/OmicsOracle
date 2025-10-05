# Frontend Integration Plan - OmicsOracle v2

**Date:** October 5, 2025
**Status:** 📋 PLANNING
**Target:** v2.2.0 Release
**Timeline:** 4-6 weeks
**Dependencies:** v2 API (91% tested, production-ready)

---

## 🎯 Executive Summary

This plan outlines the complete frontend integration strategy for OmicsOracle v2, transforming the API-first backend into a full-stack application with a modern, responsive web interface.

### Objectives

1. **User Interface:** Build intuitive, responsive web UI for all v2 features
2. **Real-time Features:** Implement WebSocket-based live updates
3. **State Management:** Efficient client-side state handling
4. **API Integration:** Seamless backend communication
5. **Authentication Flow:** Secure user login/registration UI
6. **Performance:** Fast, optimized frontend with code splitting

---

## 📊 Current State Analysis

### Backend Ready ✅
- **API Completeness:** 90% (all major endpoints available)
- **Test Coverage:** 91% pass rate
- **Discoverable API:** List endpoints for agents/workflows
- **Authentication:** JWT-based auth fully functional
- **WebSocket:** Server-side implementation ready
- **Documentation:** Comprehensive API docs available

### Frontend Status ❌
- **UI Framework:** Not selected
- **API Client:** Not implemented
- **Components:** None created
- **Authentication UI:** Not built
- **Real-time Updates:** Not implemented
- **Deployment:** Not configured

---

## 🏗️ Technology Stack Selection

### Frontend Framework Decision

**Recommended: React 18+ with TypeScript**

**Rationale:**
1. **Ecosystem:** Largest component library ecosystem
2. **TypeScript:** Strong typing for API integration
3. **Performance:** React 18 concurrent features
4. **Developer Experience:** Excellent tooling (Vite)
5. **Community:** Massive community, easy to hire developers
6. **Server-Side Rendering:** Next.js option for SEO

**Alternative Considered:**
- **Vue 3:** Simpler learning curve, but smaller ecosystem
- **Svelte:** Better performance, but less mature ecosystem

### Complete Tech Stack

```yaml
Core Framework:
  - React: 18.2+
  - TypeScript: 5.0+
  - Vite: 4.0+ (build tool)

State Management:
  - Zustand: 4.0+ (lightweight, simple)
  - TanStack Query: 5.0+ (server state, caching)

Routing:
  - React Router: 6.0+

UI Components:
  - Shadcn/ui: (Radix UI + Tailwind CSS)
  - Tailwind CSS: 3.0+
  - Lucide React: (icons)

API Communication:
  - Axios: 1.0+ (HTTP client)
  - Socket.IO Client: 4.0+ (WebSocket)

Forms & Validation:
  - React Hook Form: 7.0+
  - Zod: 3.0+ (schema validation)

Data Visualization:
  - Recharts: 2.0+ (charts/graphs)
  - React Table: 8.0+ (data tables)

Testing:
  - Vitest: 0.34+ (unit tests)
  - Testing Library: 14.0+ (component tests)
  - Playwright: 1.38+ (E2E tests)

Code Quality:
  - ESLint: 8.0+
  - Prettier: 3.0+
  - Husky: 8.0+ (git hooks)
```

---

## 📁 Project Structure

```
frontend/
├── public/
│   ├── favicon.ico
│   └── robots.txt
├── src/
│   ├── api/                      # API client layer
│   │   ├── client.ts             # Axios instance, interceptors
│   │   ├── auth.ts               # Auth API calls
│   │   ├── agents.ts             # Agent API calls
│   │   ├── workflows.ts          # Workflow API calls
│   │   ├── batch.ts              # Batch processing API
│   │   ├── quotas.ts             # Quota management API
│   │   ├── websocket.ts          # WebSocket client
│   │   └── types.ts              # API type definitions
│   │
│   ├── components/               # Reusable components
│   │   ├── ui/                   # Base UI components (shadcn)
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── card.tsx
│   │   │   ├── dialog.tsx
│   │   │   └── ...
│   │   ├── layout/               # Layout components
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Footer.tsx
│   │   │   └── MainLayout.tsx
│   │   ├── auth/                 # Auth components
│   │   │   ├── LoginForm.tsx
│   │   │   ├── RegisterForm.tsx
│   │   │   ├── PasswordReset.tsx
│   │   │   └── ProtectedRoute.tsx
│   │   ├── agents/               # Agent-specific components
│   │   │   ├── AgentCard.tsx
│   │   │   ├── AgentList.tsx
│   │   │   ├── QueryAgentForm.tsx
│   │   │   ├── SearchAgentForm.tsx
│   │   │   └── AgentResults.tsx
│   │   ├── workflows/            # Workflow components
│   │   │   ├── WorkflowCard.tsx
│   │   │   ├── WorkflowList.tsx
│   │   │   ├── WorkflowBuilder.tsx
│   │   │   └── WorkflowProgress.tsx
│   │   ├── batch/                # Batch processing
│   │   │   ├── JobList.tsx
│   │   │   ├── JobStatus.tsx
│   │   │   └── JobDetails.tsx
│   │   └── shared/               # Shared components
│   │       ├── LoadingSpinner.tsx
│   │       ├── ErrorBoundary.tsx
│   │       ├── DataTable.tsx
│   │       └── Chart.tsx
│   │
│   ├── features/                 # Feature-based modules
│   │   ├── auth/
│   │   │   ├── hooks/
│   │   │   ├── store/
│   │   │   └── utils/
│   │   ├── agents/
│   │   │   ├── hooks/
│   │   │   ├── store/
│   │   │   └── utils/
│   │   └── workflows/
│   │       ├── hooks/
│   │       ├── store/
│   │       └── utils/
│   │
│   ├── hooks/                    # Custom React hooks
│   │   ├── useAuth.ts
│   │   ├── useWebSocket.ts
│   │   ├── useAgents.ts
│   │   ├── useWorkflows.ts
│   │   ├── useQuota.ts
│   │   └── useBatchJobs.ts
│   │
│   ├── stores/                   # Zustand stores
│   │   ├── authStore.ts
│   │   ├── agentStore.ts
│   │   ├── workflowStore.ts
│   │   └── uiStore.ts
│   │
│   ├── pages/                    # Page components (routes)
│   │   ├── Home.tsx
│   │   ├── Login.tsx
│   │   ├── Register.tsx
│   │   ├── Dashboard.tsx
│   │   ├── Agents.tsx
│   │   ├── Workflows.tsx
│   │   ├── BatchJobs.tsx
│   │   ├── Profile.tsx
│   │   └── NotFound.tsx
│   │
│   ├── utils/                    # Utility functions
│   │   ├── auth.ts
│   │   ├── formatting.ts
│   │   ├── validation.ts
│   │   └── constants.ts
│   │
│   ├── types/                    # TypeScript types
│   │   ├── api.ts
│   │   ├── models.ts
│   │   └── index.ts
│   │
│   ├── styles/                   # Global styles
│   │   ├── globals.css
│   │   └── tailwind.css
│   │
│   ├── App.tsx                   # Root component
│   ├── main.tsx                  # Entry point
│   ├── router.tsx                # Route configuration
│   └── vite-env.d.ts             # Vite types
│
├── tests/
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── e2e/                      # E2E tests
│
├── .env.development              # Dev environment vars
├── .env.production               # Prod environment vars
├── .eslintrc.json                # ESLint config
├── .prettierrc                   # Prettier config
├── index.html                    # HTML entry point
├── package.json                  # Dependencies
├── tsconfig.json                 # TypeScript config
├── vite.config.ts                # Vite config
└── tailwind.config.js            # Tailwind config
```

---

## 🔧 Phase 1: Foundation (Week 1)

### Task 1.1: Project Setup (Day 1-2)

**Objective:** Initialize React + TypeScript + Vite project

```bash
# Create Vite project
npm create vite@latest omicsoracle-frontend -- --template react-ts

# Install core dependencies
npm install react-router-dom zustand @tanstack/react-query axios
npm install socket.io-client react-hook-form zod

# Install UI dependencies
npm install tailwindcss postcss autoprefixer
npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu
npm install lucide-react class-variance-authority clsx tailwind-merge

# Install dev dependencies
npm install -D @types/node vitest @testing-library/react
npm install -D @testing-library/jest-dom playwright
npm install -D eslint prettier husky
```

**Configuration Files:**

**vite.config.ts:**
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
})
```

**tailwind.config.js:**
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        // ... shadcn color system
      },
    },
  },
  plugins: [],
}
```

**Deliverables:**
- ✅ Vite + React + TypeScript project initialized
- ✅ Tailwind CSS configured
- ✅ ESLint + Prettier configured
- ✅ Basic folder structure created
- ✅ Development server running on port 3000

---

### Task 1.2: API Client Layer (Day 3-4)

**Objective:** Create type-safe API client with authentication

**src/api/client.ts:**
```typescript
import axios, { AxiosInstance, AxiosError } from 'axios'
import { authStore } from '@/stores/authStore'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor - add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = authStore.getState().token
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // Response interceptor - handle errors
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Token expired, logout
          authStore.getState().logout()
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )
  }

  getInstance(): AxiosInstance {
    return this.client
  }
}

export const apiClient = new ApiClient().getInstance()
```

**src/api/auth.ts:**
```typescript
import { apiClient } from './client'
import type {
  LoginRequest,
  RegisterRequest,
  AuthResponse,
  User
} from '@/types/api'

export const authApi = {
  // Register new user
  register: async (data: RegisterRequest): Promise<AuthResponse> => {
    const response = await apiClient.post('/api/v2/auth/register', data)
    return response.data
  },

  // Login user
  login: async (data: LoginRequest): Promise<AuthResponse> => {
    const response = await apiClient.post('/api/v2/auth/login', data)
    return response.data
  },

  // Get current user
  getMe: async (): Promise<User> => {
    const response = await apiClient.get('/api/v2/users/me')
    return response.data
  },

  // Logout (client-side only, clear token)
  logout: async (): Promise<void> => {
    // Optional: call backend logout endpoint if exists
    // await apiClient.post('/api/v2/auth/logout')
  },
}
```

**src/api/agents.ts:**
```typescript
import { apiClient } from './client'
import type { Agent, AgentExecuteRequest, AgentResult } from '@/types/api'

export const agentsApi = {
  // List all available agents
  listAgents: async (): Promise<Agent[]> => {
    const response = await apiClient.get('/api/v1/agents')
    return response.data
  },

  // Execute Query Agent
  executeQueryAgent: async (data: AgentExecuteRequest): Promise<AgentResult> => {
    const response = await apiClient.post('/api/v1/agents/query', data)
    return response.data
  },

  // Execute Search Agent
  executeSearchAgent: async (data: AgentExecuteRequest): Promise<AgentResult> => {
    const response = await apiClient.post('/api/v1/agents/search', data)
    return response.data
  },

  // Execute Data Agent
  executeDataAgent: async (data: AgentExecuteRequest): Promise<AgentResult> => {
    const response = await apiClient.post('/api/v1/agents/data', data)
    return response.data
  },

  // Execute Report Agent
  executeReportAgent: async (data: AgentExecuteRequest): Promise<AgentResult> => {
    const response = await apiClient.post('/api/v1/agents/report', data)
    return response.data
  },
}
```

**src/api/workflows.ts:**
```typescript
import { apiClient } from './client'
import type { Workflow, WorkflowExecuteRequest, WorkflowResult } from '@/types/api'

export const workflowsApi = {
  // List all available workflows
  listWorkflows: async (): Promise<Workflow[]> => {
    const response = await apiClient.get('/api/v1/workflows')
    return response.data
  },

  // Execute workflow
  executeWorkflow: async (data: WorkflowExecuteRequest): Promise<WorkflowResult> => {
    const response = await apiClient.post('/api/v1/workflows/execute', data)
    return response.data
  },
}
```

**src/types/api.ts:**
```typescript
// Authentication types
export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  username: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export interface User {
  id: string
  email: string
  username: string
  is_active: boolean
  tier: 'free' | 'pro' | 'enterprise'
  created_at: string
}

// Agent types
export interface Agent {
  id: string
  name: string
  description: string
  category: string
  capabilities: string[]
  input_types: string[]
  output_types: string[]
  endpoint: string
}

export interface AgentExecuteRequest {
  query: string
  parameters?: Record<string, any>
}

export interface AgentResult {
  success: boolean
  data: any
  execution_time_ms: number
  timestamp: string
}

// Workflow types
export interface Workflow {
  type: string
  name: string
  description: string
  agents: string[]
  use_case: string
}

export interface WorkflowExecuteRequest {
  query: string
  workflow_type: string
  max_results?: number
  report_type?: string
}

export interface WorkflowResult {
  success: boolean
  workflow_type: string
  query: string
  final_report: string
  total_datasets_found: number
  execution_time_ms: number
  timestamp: string
}
```

**Deliverables:**
- ✅ Type-safe API client with interceptors
- ✅ Authentication API methods
- ✅ Agents API methods
- ✅ Workflows API methods
- ✅ TypeScript type definitions for all API models

---

### Task 1.3: State Management (Day 5)

**Objective:** Implement Zustand stores for global state

**src/stores/authStore.ts:**
```typescript
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '@/types/api'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (token: string, user: User) => void
  logout: () => void
  updateUser: (user: User) => void
}

export const authStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      login: (token, user) =>
        set({ token, user, isAuthenticated: true }),

      logout: () =>
        set({ token: null, user: null, isAuthenticated: false }),

      updateUser: (user) =>
        set({ user }),
    }),
    {
      name: 'auth-storage',
    }
  )
)
```

**src/stores/uiStore.ts:**
```typescript
import { create } from 'zustand'

interface UiState {
  sidebarOpen: boolean
  theme: 'light' | 'dark'
  toggleSidebar: () => void
  setTheme: (theme: 'light' | 'dark') => void
}

export const uiStore = create<UiState>((set) => ({
  sidebarOpen: true,
  theme: 'light',

  toggleSidebar: () =>
    set((state) => ({ sidebarOpen: !state.sidebarOpen })),

  setTheme: (theme) =>
    set({ theme }),
}))
```

**src/hooks/useAuth.ts:**
```typescript
import { authStore } from '@/stores/authStore'
import { authApi } from '@/api/auth'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

export function useAuth() {
  const navigate = useNavigate()
  const { user, token, isAuthenticated, login, logout } = authStore()

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: (data) => {
      login(data.access_token, data.user)
      navigate('/dashboard')
    },
  })

  // Register mutation
  const registerMutation = useMutation({
    mutationFn: authApi.register,
    onSuccess: (data) => {
      login(data.access_token, data.user)
      navigate('/dashboard')
    },
  })

  // Logout function
  const handleLogout = async () => {
    await authApi.logout()
    logout()
    navigate('/login')
  }

  // Get current user query
  const { data: currentUser } = useQuery({
    queryKey: ['user', 'me'],
    queryFn: authApi.getMe,
    enabled: isAuthenticated,
  })

  return {
    user: currentUser || user,
    token,
    isAuthenticated,
    login: loginMutation.mutate,
    register: registerMutation.mutate,
    logout: handleLogout,
    isLoading: loginMutation.isPending || registerMutation.isPending,
  }
}
```

**Deliverables:**
- ✅ Auth store with persistence
- ✅ UI store for app-wide UI state
- ✅ useAuth hook for authentication operations
- ✅ TanStack Query integration for server state

---

## 🎨 Phase 2: Core UI Components (Week 2)

### Task 2.1: Layout Components (Day 1-2)

**Objective:** Build main layout structure

**Components to Create:**
1. **Header.tsx** - Top navigation bar
   - Logo
   - Navigation links
   - User menu (profile, logout)
   - Theme toggle

2. **Sidebar.tsx** - Side navigation
   - Agent links
   - Workflow links
   - Batch jobs link
   - Profile link

3. **MainLayout.tsx** - Main wrapper
   - Header + Sidebar + Content area
   - Responsive (mobile hamburger menu)

4. **Footer.tsx** - Footer component
   - Copyright
   - Links
   - Version info

**Example: MainLayout.tsx:**
```typescript
import { Header } from './Header'
import { Sidebar } from './Sidebar'
import { Footer } from './Footer'
import { uiStore } from '@/stores/uiStore'

export function MainLayout({ children }: { children: React.ReactNode }) {
  const { sidebarOpen } = uiStore()

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <div className="flex flex-1">
        {sidebarOpen && <Sidebar />}
        <main className="flex-1 p-6 bg-gray-50">
          {children}
        </main>
      </div>
      <Footer />
    </div>
  )
}
```

**Deliverables:**
- ✅ Responsive layout components
- ✅ Navigation structure
- ✅ Mobile-friendly design

---

### Task 2.2: Authentication UI (Day 3-4)

**Objective:** Build login/register forms

**Components to Create:**

**LoginForm.tsx:**
```typescript
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useAuth } from '@/hooks/useAuth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
})

type LoginFormData = z.infer<typeof loginSchema>

export function LoginForm() {
  const { login, isLoading } = useAuth()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = (data: LoginFormData) => {
    login(data)
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <Input
          type="email"
          placeholder="Email"
          {...register('email')}
        />
        {errors.email && (
          <p className="text-red-500 text-sm mt-1">{errors.email.message}</p>
        )}
      </div>

      <div>
        <Input
          type="password"
          placeholder="Password"
          {...register('password')}
        />
        {errors.password && (
          <p className="text-red-500 text-sm mt-1">{errors.password.message}</p>
        )}
      </div>

      <Button type="submit" disabled={isLoading} className="w-full">
        {isLoading ? 'Logging in...' : 'Login'}
      </Button>
    </form>
  )
}
```

**RegisterForm.tsx:**
```typescript
// Similar structure to LoginForm
// Additional fields: username, confirmPassword
// Validation with Zod schema
```

**ProtectedRoute.tsx:**
```typescript
import { Navigate } from 'react-router-dom'
import { authStore } from '@/stores/authStore'

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = authStore()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}
```

**Deliverables:**
- ✅ Login form with validation
- ✅ Register form with validation
- ✅ Protected route component
- ✅ Password reset flow (basic)

---

### Task 2.3: Agent Components (Day 5)

**Objective:** Build agent discovery and execution UI

**Components:**

1. **AgentList.tsx** - Display all available agents
2. **AgentCard.tsx** - Individual agent card
3. **QueryAgentForm.tsx** - Form for Query Agent
4. **AgentResults.tsx** - Display agent results

**Example: AgentList.tsx:**
```typescript
import { useQuery } from '@tanstack/react-query'
import { agentsApi } from '@/api/agents'
import { AgentCard } from './AgentCard'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'

export function AgentList() {
  const { data: agents, isLoading } = useQuery({
    queryKey: ['agents'],
    queryFn: agentsApi.listAgents,
  })

  if (isLoading) return <LoadingSpinner />

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {agents?.map((agent) => (
        <AgentCard key={agent.id} agent={agent} />
      ))}
    </div>
  )
}
```

**Deliverables:**
- ✅ Agent list page
- ✅ Agent execution forms
- ✅ Results display components

---

## 🚀 Phase 3: Advanced Features (Week 3)

### Task 3.1: WebSocket Integration (Day 1-2)

**Objective:** Implement real-time updates

**src/api/websocket.ts:**
```typescript
import { io, Socket } from 'socket.io-client'

class WebSocketClient {
  private socket: Socket | null = null
  private token: string | null = null

  connect(token: string) {
    this.token = token
    this.socket = io('ws://localhost:8000', {
      auth: { token },
      transports: ['websocket'],
    })

    this.socket.on('connect', () => {
      console.log('WebSocket connected')
    })

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected')
    })

    return this.socket
  }

  disconnect() {
    this.socket?.disconnect()
  }

  on(event: string, callback: (data: any) => void) {
    this.socket?.on(event, callback)
  }

  emit(event: string, data: any) {
    this.socket?.emit(event, data)
  }
}

export const wsClient = new WebSocketClient()
```

**src/hooks/useWebSocket.ts:**
```typescript
import { useEffect } from 'react'
import { authStore } from '@/stores/authStore'
import { wsClient } from '@/api/websocket'

export function useWebSocket(event: string, handler: (data: any) => void) {
  const { token } = authStore()

  useEffect(() => {
    if (!token) return

    const socket = wsClient.connect(token)
    socket.on(event, handler)

    return () => {
      socket.off(event, handler)
    }
  }, [event, handler, token])
}
```

**Deliverables:**
- ✅ WebSocket client implementation
- ✅ useWebSocket hook
- ✅ Real-time batch job updates
- ✅ Real-time workflow progress

---

### Task 3.2: Workflow UI (Day 3-4)

**Objective:** Build workflow execution interface

**Components:**

1. **WorkflowList.tsx** - List available workflows
2. **WorkflowBuilder.tsx** - Configure workflow parameters
3. **WorkflowProgress.tsx** - Real-time progress display
4. **WorkflowResults.tsx** - Display final results

**Features:**
- Workflow selection
- Parameter configuration
- Real-time progress updates (WebSocket)
- Stage-by-stage progress visualization
- Final report display

**Deliverables:**
- ✅ Workflow discovery UI
- ✅ Workflow execution UI
- ✅ Real-time progress tracking
- ✅ Results visualization

---

### Task 3.3: Batch Processing UI (Day 5)

**Objective:** Build batch job management interface

**Components:**

1. **BatchJobList.tsx** - List all jobs
2. **CreateBatchJob.tsx** - Create new batch job
3. **BatchJobDetails.tsx** - Job details and logs
4. **BatchJobStatus.tsx** - Real-time status updates

**Deliverables:**
- ✅ Job creation form
- ✅ Job list with filters
- ✅ Job status tracking
- ✅ Real-time updates via WebSocket

---

## 📊 Phase 4: Data Visualization (Week 4)

### Task 4.1: Charts and Graphs

**Objective:** Visualize agent/workflow results

**Components:**

1. **ResultsChart.tsx** - Generic chart component
2. **DatasetDistribution.tsx** - Dataset stats charts
3. **QualityMetrics.tsx** - Quality score visualization
4. **TrendAnalysis.tsx** - Temporal trend charts

**Using Recharts:**
```typescript
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts'

export function DatasetDistribution({ data }: { data: any[] }) {
  return (
    <BarChart width={600} height={400} data={data}>
      <XAxis dataKey="name" />
      <YAxis />
      <Tooltip />
      <Legend />
      <Bar dataKey="count" fill="#8884d8" />
    </BarChart>
  )
}
```

**Deliverables:**
- ✅ Chart components for all result types
- ✅ Interactive data visualization
- ✅ Export chart functionality

---

### Task 4.2: Data Tables

**Objective:** Display tabular data with sorting/filtering

**Using React Table:**
```typescript
import { useReactTable, getCoreRowModel } from '@tanstack/react-table'

export function DataTable({ data, columns }: TableProps) {
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  })

  // Render table with sorting, filtering, pagination
}
```

**Deliverables:**
- ✅ Sortable data tables
- ✅ Filterable columns
- ✅ Pagination
- ✅ Export to CSV functionality

---

## 🧪 Phase 5: Testing (Week 5)

### Task 5.1: Unit Tests (Day 1-3)

**Objective:** Test individual components

```typescript
// Example: LoginForm.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { LoginForm } from './LoginForm'

describe('LoginForm', () => {
  it('renders login form', () => {
    render(<LoginForm />)
    expect(screen.getByPlaceholderText('Email')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Password')).toBeInTheDocument()
  })

  it('validates email format', async () => {
    render(<LoginForm />)
    const emailInput = screen.getByPlaceholderText('Email')
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } })
    fireEvent.blur(emailInput)
    expect(await screen.findByText('Invalid email address')).toBeInTheDocument()
  })

  // More tests...
})
```

**Coverage Target:** >80%

**Deliverables:**
- ✅ Component unit tests
- ✅ Hook unit tests
- ✅ Store unit tests
- ✅ Utility function tests

---

### Task 5.2: Integration Tests (Day 4)

**Objective:** Test feature flows

```typescript
// Example: auth-flow.test.tsx
describe('Authentication Flow', () => {
  it('allows user to register and login', async () => {
    // 1. Visit register page
    // 2. Fill registration form
    // 3. Submit form
    // 4. Verify redirect to dashboard
    // 5. Verify user data displayed
  })
})
```

**Deliverables:**
- ✅ Auth flow tests
- ✅ Agent execution flow tests
- ✅ Workflow execution flow tests

---

### Task 5.3: E2E Tests (Day 5)

**Objective:** Test complete user journeys

**Using Playwright:**
```typescript
import { test, expect } from '@playwright/test'

test('complete workflow execution', async ({ page }) => {
  // 1. Login
  await page.goto('/login')
  await page.fill('[placeholder="Email"]', 'test@example.com')
  await page.fill('[placeholder="Password"]', 'password123')
  await page.click('button[type="submit"]')

  // 2. Navigate to workflows
  await page.click('text=Workflows')

  // 3. Select workflow
  await page.click('text=Full Analysis')

  // 4. Enter query
  await page.fill('[placeholder="Enter query"]', 'cancer research')

  // 5. Execute workflow
  await page.click('text=Execute Workflow')

  // 6. Wait for results
  await expect(page.locator('text=Workflow Complete')).toBeVisible({
    timeout: 60000,
  })

  // 7. Verify results displayed
  await expect(page.locator('.workflow-results')).toBeVisible()
})
```

**Deliverables:**
- ✅ 10+ E2E test scenarios
- ✅ Critical path coverage
- ✅ Cross-browser testing

---

## 🚀 Phase 6: Deployment (Week 6)

### Task 6.1: Build Optimization

**Objective:** Optimize production build

**Techniques:**
1. **Code Splitting** - Dynamic imports for routes
2. **Tree Shaking** - Remove unused code
3. **Minification** - Compress JavaScript/CSS
4. **Asset Optimization** - Optimize images, fonts
5. **Lazy Loading** - Load components on demand

**vite.config.ts optimizations:**
```typescript
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'router': ['react-router-dom'],
          'ui': ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu'],
        },
      },
    },
    chunkSizeWarningLimit: 1000,
  },
})
```

**Deliverables:**
- ✅ Optimized production build
- ✅ Bundle size analysis
- ✅ Performance metrics (Lighthouse score >90)

---

### Task 6.2: Docker Configuration

**Objective:** Containerize frontend

**Dockerfile:**
```dockerfile
# Build stage
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**nginx.conf:**
```nginx
server {
  listen 80;
  server_name _;

  root /usr/share/nginx/html;
  index index.html;

  # SPA routing
  location / {
    try_files $uri $uri/ /index.html;
  }

  # API proxy
  location /api {
    proxy_pass http://backend:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }

  # WebSocket proxy
  location /ws {
    proxy_pass http://backend:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
  }
}
```

**Deliverables:**
- ✅ Production Dockerfile
- ✅ Nginx configuration
- ✅ Docker Compose integration

---

### Task 6.3: CI/CD Pipeline

**Objective:** Automated deployment

**.github/workflows/frontend-ci.yml:**
```yaml
name: Frontend CI/CD

on:
  push:
    branches: [main, develop]
    paths:
      - 'frontend/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: cd frontend && npm ci
      - name: Run tests
        run: cd frontend && npm test
      - name: Run E2E tests
        run: cd frontend && npm run test:e2e

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker image
        run: |
          cd frontend
          docker build -t omicsoracle-frontend:${{ github.sha }} .
      - name: Push to registry
        run: |
          docker tag omicsoracle-frontend:${{ github.sha }} \
            ghcr.io/${{ github.repository }}/frontend:latest
          docker push ghcr.io/${{ github.repository }}/frontend:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to production
        run: |
          # Deployment commands
```

**Deliverables:**
- ✅ CI pipeline for tests
- ✅ CD pipeline for deployment
- ✅ Environment-specific builds

---

## 📝 Success Criteria

### Functionality ✅
- [ ] User can register and login
- [ ] User can view all available agents
- [ ] User can execute agents with custom queries
- [ ] User can view agent results
- [ ] User can view all available workflows
- [ ] User can execute workflows
- [ ] User can view real-time workflow progress
- [ ] User can view workflow results
- [ ] User can create batch jobs
- [ ] User can view batch job status
- [ ] User can view batch job results

### Performance ✅
- [ ] Lighthouse score >90
- [ ] First Contentful Paint <1.5s
- [ ] Time to Interactive <3s
- [ ] Bundle size <500KB (gzipped)

### Quality ✅
- [ ] >80% test coverage
- [ ] Zero ESLint errors
- [ ] Zero TypeScript errors
- [ ] Accessible (WCAG 2.1 Level AA)
- [ ] Mobile responsive

### User Experience ✅
- [ ] Intuitive navigation
- [ ] Clear error messages
- [ ] Loading states
- [ ] Success confirmations
- [ ] Real-time updates

---

## 📊 Timeline Summary

```
Week 1: Foundation
├── Day 1-2: Project setup
├── Day 3-4: API client layer
└── Day 5: State management

Week 2: Core UI
├── Day 1-2: Layout components
├── Day 3-4: Authentication UI
└── Day 5: Agent components

Week 3: Advanced Features
├── Day 1-2: WebSocket integration
├── Day 3-4: Workflow UI
└── Day 5: Batch processing UI

Week 4: Data Visualization
├── Day 1-3: Charts and graphs
└── Day 4-5: Data tables

Week 5: Testing
├── Day 1-3: Unit tests
├── Day 4: Integration tests
└── Day 5: E2E tests

Week 6: Deployment
├── Day 1-2: Build optimization
├── Day 3-4: Docker configuration
└── Day 5: CI/CD pipeline
```

---

## 🔄 Next Steps After Frontend

1. **User Feedback** - Gather user feedback, iterate
2. **Mobile App** - Consider React Native version
3. **Advanced Features** - Add more visualizations, export options
4. **Performance Tuning** - Further optimization based on usage
5. **Documentation** - User guides, API docs

---

## 📚 Resources

### Documentation
- React: https://react.dev
- TypeScript: https://www.typescriptlang.org
- Vite: https://vitejs.dev
- Tailwind CSS: https://tailwindcss.com
- shadcn/ui: https://ui.shadcn.com
- TanStack Query: https://tanstack.com/query
- Zustand: https://github.com/pmndrs/zustand

### Tools
- ESLint: https://eslint.org
- Prettier: https://prettier.io
- Vitest: https://vitest.dev
- Playwright: https://playwright.dev

---

**Status:** Ready for implementation
**Next Action:** Begin Phase 1, Task 1.1 (Project Setup)

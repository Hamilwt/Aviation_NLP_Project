import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number;
}

interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  activeTab: string;
  notifications: Notification[];
  setSidebarOpen: (open: boolean) => void;
  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
  setActiveTab: (tab: string) => void;
  addNotification: (notification: Omit<Notification, 'id'>) => void;
  removeNotification: (id: string) => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      theme: 'light',
      activeTab: 'overview',
      notifications: [],
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setTheme: (theme) => set({ theme }),
      setActiveTab: (tab) => set({ activeTab: tab }),
      addNotification: (notification) => {
        const id = Math.random().toString(36).substr(2, 9);
        set((state) => ({
          notifications: [...state.notifications, { ...notification, id }],
        }));
        if (notification.duration !== 0) {
          setTimeout(() => {
            set((state) => ({
              notifications: state.notifications.filter((n) => n.id !== id),
            }));
          }, notification.duration || 5000);
        }
      },
      removeNotification: (id) =>
        set((state) => ({
          notifications: state.notifications.filter((n) => n.id !== id),
        })),
    }),
    {
      name: 'ui-store',
      partialize: (state) => ({ theme: state.theme, sidebarOpen: state.sidebarOpen }),
    }
  )
);

interface DataState {
  overview: any | null;
  modelPerformance: any | null;
  alerts: any | null;
  systemStatus: any | null;
  loading: Record<string, boolean>;
  error: Record<string, string | null>;
  setOverview: (data: any) => void;
  setModelPerformance: (data: any) => void;
  setAlerts: (data: any) => void;
  setSystemStatus: (data: any) => void;
  setLoading: (key: string, loading: boolean) => void;
  setError: (key: string, error: string | null) => void;
  clearError: (key: string) => void;
}

export const useDataStore = create<DataState>((set, get) => ({
  overview: null,
  modelPerformance: null,
  alerts: null,
  systemStatus: null,
  loading: {},
  error: {},
  setOverview: (data) => set({ overview: data, error: { ...get().error, overview: null } }),
  setModelPerformance: (data) => set({ modelPerformance: data, error: { ...get().error, modelPerformance: null } }),
  setAlerts: (data) => set({ alerts: data, error: { ...get().error, alerts: null } }),
  setSystemStatus: (data) => set({ systemStatus: data, error: { ...get().error, systemStatus: null } }),
  setLoading: (key, loading) =>
    set((state) => ({ loading: { ...state.loading, [key]: loading } })),
  setError: (key, error) =>
    set((state) => ({ error: { ...state.error, [key]: error }, loading: { ...state.loading, [key]: false } })),
  clearError: (key) =>
    set((state) => ({ error: { ...state.error, [key]: null } })),
}));
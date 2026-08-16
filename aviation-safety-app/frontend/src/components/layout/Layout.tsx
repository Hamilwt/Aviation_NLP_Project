import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { cn } from '@/utils/helpers';
import { useUIStore } from '@/store';
import { Toaster } from 'react-hot-toast';

interface LayoutProps {
  children?: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const { sidebarOpen } = useUIStore();

  return (
    <div className={cn('min-h-screen bg-cream-100', 'flex')}>
      <Sidebar />
      <div className={cn(
        'flex-1 flex flex-col min-w-0',
        sidebarOpen ? 'lg:ml-64' : 'lg:ml-0',
      )}>
        <Header />
        <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-auto">
          {children ?? <Outlet />}
        </main>
      </div>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#FFFDF9',
            color: '#3E2F1F',
            border: '1px solid #D9C5B2',
            borderRadius: '0.75rem',
            padding: '1rem',
            boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)',
          },
          success: {
            iconTheme: {
              primary: '#22C55E',
              secondary: '#FFFDF9',
            },
          },
          error: {
            iconTheme: {
              primary: '#EF4444',
              secondary: '#FFFDF9',
            },
          },
        }}
      />
    </div>
  );
}
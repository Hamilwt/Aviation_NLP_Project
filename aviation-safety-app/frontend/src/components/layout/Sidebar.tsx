import { NavLink, useLocation } from 'react-router-dom';
import { cn } from '@/utils/helpers';
import {
  LayoutDashboard,
  BarChart2,
  Search,
  ClipboardList,
  AlertTriangle,
  Settings,
  ChevronLeft,
  ChevronRight,
  Shield,
} from 'lucide-react';
import { useUIStore } from '@/store';

const navigation = [
  { name: 'Overview', href: '/', icon: LayoutDashboard },
  { name: 'Model Performance', href: '/performance', icon: BarChart2 },
  { name: 'RAG Explorer', href: '/rag', icon: Search },
  { name: 'Data Assistant', href: '/assistant', icon: ClipboardList },
  { name: 'Live Alerts', href: '/alerts', icon: AlertTriangle },
  { name: 'System Control', href: '/system', icon: Settings },
];

export function Sidebar() {
  const { sidebarOpen, toggleSidebar, theme } = useUIStore();
  const location = useLocation();

  return (
    <>
      <button
        onClick={toggleSidebar}
        className={cn(
          'fixed top-4 left-4 z-50 p-2 rounded-lg bg-white border-cream-300',
          'hover:bg-cream-100 transition-colors shadow-md',
          'lg:hidden'
        )}
        aria-label={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
      >
        {sidebarOpen ? <ChevronLeft className="w-5 h-5 text-brown-700" /> : <ChevronRight className="w-5 h-5 text-brown-700" />}
      </button>

      <aside
        className={cn(
          'fixed lg:static inset-y-0 left-0 z-40',
          'bg-white border-r border-cream-300',
          'transition-all duration-300 ease-in-out',
          'flex flex-col',
          sidebarOpen ? 'w-64 translate-x-0' : '-translate-x-full lg:translate-x-0 lg:w-64',
        )}
        aria-label="Main navigation"
      >
        <div className="flex items-center justify-between h-16 px-6 border-b border-cream-300">
          <NavLink to="/" className="flex items-center gap-2" aria-label="Safety NLP Pipeline Home">
            <Shield className="w-6 h-6 text-brown-700" />
            <span className="font-semibold text-brown-800 text-lg hidden sm:block">Safety NLP</span>
          </NavLink>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto" aria-label="Main navigation">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href || 
              (item.href !== '/' && location.pathname.startsWith(item.href));
            
            return (
              <NavLink
                key={item.name}
                to={item.href}
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg',
                  'text-sm font-medium transition-colors',
                  'focus:outline-none focus:ring-2 focus:ring-brown-500 focus:ring-offset-2',
                  isActive
                    ? 'bg-brown-50 text-brown-800 border-l-4 border-brown-700'
                    : 'text-brown-600 hover:bg-cream-100 hover:text-brown-800'
                )}
                aria-current={isActive ? 'page' : undefined}
              >
                <item.icon className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
        </nav>

        <div className="p-3 border-t border-cream-300">
          <div className="flex items-center justify-between px-3 py-2 text-xs text-brown-500">
            <span>v2.0.0</span>
            <span className="flex items-center gap-1">
              <span className={cn('w-2 h-2 rounded-full', theme === 'dark' ? 'bg-gray-400' : 'bg-brown-300')} />
              <span>{theme}</span>
            </span>
          </div>
        </div>
      </aside>

      {!sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/20 lg:hidden"
          onClick={toggleSidebar}
          aria-hidden="true"
        />
      )}
    </>
  );
}
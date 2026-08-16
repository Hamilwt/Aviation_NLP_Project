import { cn } from '@/utils/helpers';
import { Moon, Sun, Bell, Menu, Shield } from 'lucide-react';
import { useUIStore } from '@/store';

export function Header() {
  const { sidebarOpen, toggleSidebar, theme, setTheme, notifications, removeNotification } = useUIStore();

  return (
    <header className={cn(
      'sticky top-0 z-30',
      'bg-white/80 backdrop-blur-sm border-b border-cream-300',
      'lg:ml-64',
      'transition-all duration-300'
    )}>
      <div className="flex items-center justify-between h-16 px-4 sm:px-6">
        <div className="flex items-center gap-4">
          <button
            onClick={toggleSidebar}
            className="lg:hidden p-2 rounded-lg text-brown-600 hover:bg-cream-100"
            aria-label={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
          >
            <Menu className="w-5 h-5" />
          </button>
          
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-cream-100 rounded-lg">
            <Shield className="w-4 h-4 text-brown-700" />
            <span className="text-sm font-medium text-brown-700">Safety NLP Pipeline</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
            className="p-2 rounded-lg text-brown-600 hover:bg-cream-100 transition-colors"
            aria-label={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
          >
            {theme === 'light' ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
          </button>

          <div className="relative">
            <button
              className="p-2 rounded-lg text-brown-600 hover:bg-cream-100 transition-colors relative"
              aria-label={`Notifications ${notifications.length > 0 ? `(${notifications.length})` : ''}`}
            >
              <Bell className="w-5 h-5" />
              {notifications.length > 0 && (
                <span className="absolute -top-1 -right-1 w-5 h-5 bg-risk-critical text-white text-xs font-medium rounded-full flex items-center justify-center">
                  {notifications.length > 9 ? '9+' : notifications.length}
                </span>
              )}
            </button>

            {notifications.length > 0 && (
              <div className="absolute right-0 mt-2 w-80 bg-white border-cream-300 rounded-xl shadow-lg py-2 z-50">
                <div className="px-4 py-2 border-b border-cream-300">
                  <h4 className="text-sm font-semibold text-brown-800">Notifications</h4>
                </div>
                <div className="max-h-64 overflow-y-auto">
                  {notifications.slice().reverse().map((notification) => (
                    <div
                      key={notification.id}
                      className={cn(
                        'px-4 py-3 hover:bg-cream-50 border-b border-cream-200 last:border-0',
                        'flex items-start gap-3'
                      )}
                    >
                      <div className={cn(
                        'w-2 h-2 mt-1.5 rounded-full flex-shrink-0',
                        notification.type === 'success' && 'bg-risk-medium',
                        notification.type === 'error' && 'bg-risk-critical',
                        notification.type === 'warning' && 'bg-risk-high',
                        notification.type === 'info' && 'bg-teal-500'
                      )} />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-brown-800">{notification.message}</p>
                      </div>
                      <button
                        onClick={() => removeNotification(notification.id)}
                        className="text-brown-400 hover:text-brown-600 p-1"
                        aria-label="Dismiss notification"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
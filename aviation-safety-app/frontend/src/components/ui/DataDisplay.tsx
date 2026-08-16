import { ReactNode } from 'react';
import { cn } from '@/utils/helpers';

interface CardProps {
  children: ReactNode;
  className?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hover?: boolean;
}

export function Card({ 
  children, 
  className, 
  padding = 'md', 
  hover = false 
}: CardProps) {
  const paddingClasses = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  };

  return (
    <div
      className={cn(
        'bg-cream-50 border border-cream-300 rounded-xl',
        'shadow-sm',
        paddingClasses[padding],
        hover && 'transition-shadow hover:shadow-md cursor-pointer',
        className
      )}
    >
      {children}
    </div>
  );
}

interface CardHeaderProps {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  className?: string;
}

export function CardHeader({ title, subtitle, action, className }: CardHeaderProps) {
  return (
    <div className={cn('flex items-start justify-between mb-4', className)}>
      <div>
        <h3 className="text-brown-700 font-semibold text-lg">{title}</h3>
        {subtitle && <p className="text-brown-500 text-sm mt-0.5">{subtitle}</p>}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}

interface MetricCardProps {
  label: string;
  value: string | number;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  icon?: ReactNode;
  color?: string;
  className?: string;
}

export function MetricCard({ 
  label, 
  value, 
  change, 
  changeType = 'neutral', 
  icon, 
  color = '#5C4033',
  className 
}: MetricCardProps) {
  return (
    <Card className={cn('flex flex-col', className)}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-brown-500 text-sm font-medium">{label}</p>
          <p className="text-2xl font-bold mt-1" style={{ color }}>{value}</p>
        </div>
        {icon && <div className="text-brown-300">{icon}</div>}
      </div>
      {change && (
        <div className="mt-3 flex items-center gap-1">
          <span className={cn(
            'text-xs font-medium',
            changeType === 'positive' && 'text-green-600',
            changeType === 'negative' && 'text-red-600',
            changeType === 'neutral' && 'text-brown-500'
          )}>
            {change}
          </span>
        </div>
      )}
    </Card>
  );
}

interface BadgeProps {
  children: ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info' | 'critical' | 'high' | 'medium';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function Badge({ children, variant = 'default', size = 'md', className }: BadgeProps) {
  const variantClasses = {
    default: 'bg-cream-200 text-brown-700 border-cream-300',
    success: 'bg-green-100 text-green-700 border-green-200',
    warning: 'bg-yellow-100 text-yellow-700 border-yellow-200',
    error: 'bg-red-100 text-red-700 border-red-200',
    info: 'bg-blue-100 text-blue-700 border-blue-200',
    critical: 'bg-red-100 text-red-700 border-red-200',
    high: 'bg-orange-100 text-orange-700 border-orange-200',
    medium: 'bg-green-100 text-green-700 border-green-200',
  };

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
    lg: 'px-3 py-1.5 text-base',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center font-medium rounded-full border',
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
    >
      {children}
    </span>
  );
}

interface ProgressBarProps {
  value: number; // 0-100
  color?: string;
  height?: number;
  showLabel?: boolean;
  className?: string;
}

export function ProgressBar({ value, color = '#5C4033', height = 8, showLabel = false, className }: ProgressBarProps) {
  return (
    <div className={cn('w-full', className)}>
      <div className="h-1.5 bg-cream-200 rounded-full overflow-hidden" style={{ height }}>
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${Math.min(100, Math.max(0, value))}%`, backgroundColor: color }}
        />
      </div>
      {showLabel && (
        <p className="text-xs text-brown-500 mt-1 text-right">{Math.round(value)}%</p>
      )}
    </div>
  );
}

interface TableProps<T> {
  columns: { key: string; header: string; render?: (row: T) => ReactNode; className?: string }[];
  data: T[];
  keyExtractor: (row: T) => string;
  striped?: boolean;
  hoverable?: boolean;
  emptyMessage?: string;
  className?: string;
}

export function Table<T>({ columns, data, keyExtractor, striped = true, hoverable = true, emptyMessage = 'No data available', className }: TableProps<T>) {
  return (
    <div className={cn('overflow-x-auto', className)}>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-cream-300 bg-cream-100">
            {columns.map((col) => (
              <th key={col.key} className={cn('text-left py-3 px-4 font-medium text-brown-600', col.className)}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="py-8 text-center text-brown-500">
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((row, idx) => (
              <tr key={keyExtractor(row)} className={cn(
                'border-b border-cream-200 last:border-0',
                striped && idx % 2 === 0 && 'bg-cream-50',
                hoverable && 'hover:bg-cream-100'
              )}>
                {columns.map((col) => (
                  <td key={col.key} className={cn('py-3 px-4 text-brown-800', col.className)}>
                    {col.render ? col.render(row) : (row as any)[col.key]}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

interface StatGridProps {
  children: ReactNode;
  columns?: 1 | 2 | 3 | 4;
  className?: string;
}

export function StatGrid({ children, columns = 4, className }: StatGridProps) {
  const gridCols = {
    1: 'grid-cols-1',
    2: 'grid-cols-1 sm:grid-cols-2',
    3: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4',
  };
  
  return (
    <div className={cn('grid gap-4', gridCols[columns], className)}>
      {children}
    </div>
  );
}

interface SectionProps {
  title: string;
  subtitle?: string;
  children: ReactNode;
  action?: ReactNode;
  className?: string;
}

export function Section({ title, subtitle, children, action, className }: SectionProps) {
  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-brown-800">{title}</h2>
          {subtitle && <p className="text-brown-500 mt-0.5">{subtitle}</p>}
        </div>
        {action && <div>{action}</div>}
      </div>
      <div>{children}</div>
    </div>
  );
}
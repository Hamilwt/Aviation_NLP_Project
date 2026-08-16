import { ReactNode } from 'react';
import { cn } from '@/utils/helpers';

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
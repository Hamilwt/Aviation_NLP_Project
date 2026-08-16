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
  className?: string;
}

export function MetricCard({ 
  label, 
  value, 
  change, 
  changeType = 'neutral', 
  icon, 
  className 
}: MetricCardProps) {
  return (
    <Card className={cn('flex flex-col', className)}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-brown-500 text-sm font-medium">{label}</p>
          <p className="text-brown-800 text-2xl font-bold mt-1">{value}</p>
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
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function Badge({ children, variant = 'default', size = 'md', className }: BadgeProps) {
  const variantClasses = {
    default: 'bg-cream-200 text-brown-700 border-cream-300',
    success: 'bg-risk-medium/10 text-risk-medium border-risk-medium/20',
    warning: 'bg-risk-high/10 text-risk-high border-risk-high/20',
    error: 'bg-risk-critical/10 text-risk-critical border-risk-critical/20',
    info: 'bg-teal-100 text-teal-700 border-teal-200',
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
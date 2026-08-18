import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNumber(num: number): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
}

export function formatPercent(value: number): string {
  return (value * 100).toFixed(1) + '%';
}

export function getRiskColor(risk: string): string {
  switch (risk.toLowerCase()) {
    case 'critical':
      return 'text-risk-critical bg-risk-critical/10 border-risk-critical/20';
    case 'high':
      return 'text-risk-high bg-risk-high/10 border-risk-high/20';
    case 'medium':
      return 'text-risk-medium bg-risk-medium/10 border-risk-medium/20';
    default:
      return 'text-gray-600 bg-gray-100 border-gray-200';
  }
}

export function getRiskBadgeColor(risk: string): string {
  switch (risk.toLowerCase()) {
    case 'critical':
      return 'bg-risk-critical text-white';
    case 'high':
      return 'bg-risk-high text-white';
    case 'medium':
      return 'bg-risk-medium text-white';
    default:
      return 'bg-gray-100 text-gray-700';
  }
}

export function truncate(text: string, length: number): string {
  if (text.length <= length) return text;
  return text.slice(0, length) + '...';
}

export function basename(path: string): string {
  if (!path) return path;
  return path.split(/[\\/]/).pop() || path;
}

export function formatDate(dateString: string): string {
  try {
    const date = new Date(dateString);
    return date.toLocaleString();
  } catch {
    return dateString;
  }
}

export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
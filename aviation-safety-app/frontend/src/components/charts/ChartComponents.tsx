import { cn } from '@/utils/helpers';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
  PieChart, Pie, Sector,
  LineChart, Line, AreaChart, Area,
  ComposedChart,
  Legend,
  LabelList,
} from 'recharts';
import { ReactNode } from 'react';

const COLORS = [
  '#5C4033', '#8B6B4D', '#A98467', '#C9B099', '#D9C5B2',
  '#0F766E', '#14B8A6', '#2DD4BF', '#5EEAD4', '#99F6E4',
  '#EF4444', '#F97316', '#F59E0B', '#22C55E', '#3B82F6',
];

const CHART_CONFIG = {
  margin: { top: 20, right: 30, left: 20, bottom: 20 },
  gridColor: '#D9C5B2',
  textColor: '#8B7355',
  background: '#FFFDF9',
  tooltipBg: '#FFFDF9',
  tooltipBorder: '#D9C5B2',
};

export function BarChartComponent({
  data,
  xKey,
  yKeys,
  labels,
  colors = COLORS,
  height = 300,
  horizontal = false,
  showValue = true,
  className,
}: {
  data: Record<string, any>[];
  xKey: string;
  yKeys: string | string[];
  labels?: Record<string, string>;
  colors?: string[];
  height?: number;
  horizontal?: boolean;
  showValue?: boolean;
  className?: string;
}) {
  const keys = Array.isArray(yKeys) ? yKeys : [yKeys];
  const isMulti = keys.length > 1;

  return (
    <div className={cn('w-full', className)} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        {horizontal ? (
          <BarChart data={data} layout="vertical" margin={CHART_CONFIG.margin}>
            <CartesianGrid strokeDasharray="3 3" stroke={CHART_CONFIG.gridColor} />
            <XAxis type="number" stroke={CHART_CONFIG.textColor} fontSize={11} />
            <YAxis
              type="category"
              dataKey={xKey}
              stroke={CHART_CONFIG.textColor}
              fontSize={11}
              width={160}
              tickMargin={8}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: CHART_CONFIG.tooltipBg,
                border: `1px solid ${CHART_CONFIG.tooltipBorder}`,
                borderRadius: '8px',
              }}
              formatter={(value: number, name: string) => [value, labels?.[name] || name]}
            />
            <Legend />
            {keys.map((key, i) => (
              <Bar
                key={key}
                dataKey={key}
                name={labels?.[key] || key}
                fill={colors[i % colors.length]}
                radius={[0, 4, 4, 0]}
                maxBarSize={30}
              >
                {showValue && <LabelList dataKey={key} position="insideRight" offset={5} fontSize={10} fill="#FFFDF9" />}
              </Bar>
            ))}
          </BarChart>
        ) : (
          <BarChart data={data} margin={CHART_CONFIG.margin}>
            <CartesianGrid strokeDasharray="3 3" stroke={CHART_CONFIG.gridColor} />
            <XAxis
              dataKey={xKey}
              stroke={CHART_CONFIG.textColor}
              fontSize={11}
              tickMargin={8}
              tick={{ fill: CHART_CONFIG.textColor }}
            />
            <YAxis stroke={CHART_CONFIG.textColor} fontSize={11} tick={{ fill: CHART_CONFIG.textColor }} />
            <Tooltip
              contentStyle={{
                backgroundColor: CHART_CONFIG.tooltipBg,
                border: `1px solid ${CHART_CONFIG.tooltipBorder}`,
                borderRadius: '8px',
              }}
              formatter={(value: number, name: string) => [value, labels?.[name] || name]}
            />
            <Legend />
            {keys.map((key, i) => (
              <Bar
                key={key}
                dataKey={key}
                name={labels?.[key] || key}
                fill={colors[i % colors.length]}
                radius={[4, 4, 0, 0]}
                maxBarSize={40}
              >
                {showValue && <LabelList dataKey={key} position="insideTop" offset={-5} fontSize={10} fill="#FFFDF9" />}
              </Bar>
            ))}
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}

export function PieChartComponent({
  data,
  dataKey = 'value',
  nameKey = 'name',
  height = 300,
  innerRadius = 60,
  className,
  showPercent = true,
}: {
  data: Record<string, any>[];
  dataKey?: string;
  nameKey?: string;
  height?: number;
  innerRadius?: number;
  className?: string;
  showPercent?: boolean;
}) {
  return (
    <div className={cn('w-full', className)} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={innerRadius}
            outerRadius={Math.min(200, Math.floor((height - 40) / 2))}
            paddingAngle={2}
            dataKey={dataKey}
            nameKey={nameKey}
            label={({ name, percent }) => `${name}${showPercent ? ` ${(percent * 100).toFixed(1)}%` : ''}`}
            labelLine={false}
            fill="#8884d8"
          >
            {data.map((entry, i) => (
              <Cell key={`cell-${i}`} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: CHART_CONFIG.tooltipBg,
              border: `1px solid ${CHART_CONFIG.tooltipBorder}`,
              borderRadius: '8px',
            }}
            formatter={(value: number) => [value, '']}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

export function LineChartComponent({
  data,
  xKey,
  yKeys,
  labels,
  colors = COLORS,
  height = 300,
  className,
}: {
  data: Record<string, any>[];
  xKey: string;
  yKeys: string | string[];
  labels?: Record<string, string>;
  colors?: string[];
  height?: number;
  className?: string;
}) {
  const keys = Array.isArray(yKeys) ? yKeys : [yKeys];

  return (
    <div className={cn('w-full', className)} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={CHART_CONFIG.margin}>
          <CartesianGrid strokeDasharray="3 3" stroke={CHART_CONFIG.gridColor} />
          <XAxis
            dataKey={xKey}
            stroke={CHART_CONFIG.textColor}
            fontSize={11}
            tick={{ fill: CHART_CONFIG.textColor }}
          />
          <YAxis stroke={CHART_CONFIG.textColor} fontSize={11} tick={{ fill: CHART_CONFIG.textColor }} />
          <Tooltip
            contentStyle={{
              backgroundColor: CHART_CONFIG.tooltipBg,
              border: `1px solid ${CHART_CONFIG.tooltipBorder}`,
              borderRadius: '8px',
            }}
            formatter={(value: number, name: string) => [value, labels?.[name] || name]}
          />
          <Legend />
          {keys.map((key, i) => (
            <Line
              key={key}
              type="monotone"
              dataKey={key}
              name={labels?.[key] || key}
              stroke={colors[i % colors.length]}
              strokeWidth={2}
              dot={{ fill: colors[i % colors.length], strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, fill: colors[i % colors.length] }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function ConfusionMatrixChart({
  matrix,
  labels,
  height = 400,
  className,
}: {
  matrix: number[][];
  labels: string[];
  height?: number;
  className?: string;
}) {
  // Flatten matrix for heatmap
  const heatmapData = matrix.flatMap((row, i) =>
    row.map((value, j) => ({
      x: labels[j] || j,
      y: labels[i] || i,
      value: Math.round(value * 100) / 100,
    }))
  );

  return (
    <div className={cn('w-full', className)} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={heatmapData} margin={CHART_CONFIG.margin}>
          <CartesianGrid strokeDasharray="3 3" stroke={CHART_CONFIG.gridColor} />
          <XAxis
            type="category"
            dataKey="x"
            stroke={CHART_CONFIG.textColor}
            fontSize={10}
            tickMargin={8}
          />
          <YAxis
            type="category"
            dataKey="y"
            stroke={CHART_CONFIG.textColor}
            fontSize={10}
            width={140}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: CHART_CONFIG.tooltipBg,
              border: `1px solid ${CHART_CONFIG.tooltipBorder}`,
              borderRadius: '8px',
            }}
          />
          {/* Custom cell rendering would need a different approach */}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

export function MetricCardChart({
  value,
  label,
  trend,
  trendLabel,
  color = '#5C4033',
  height = 80,
  className,
}: {
  value: string | number;
  label: string;
  trend?: number;
  trendLabel?: string;
  color?: string;
  height?: number;
  className?: string;
}) {
  return (
    <div className={cn('p-4 rounded-xl bg-cream-50 border border-cream-300', className)}>
      <div className="flex items-end justify-between">
        <div>
          <p className="text-brown-500 text-sm font-medium">{label}</p>
          <p className="text-2xl font-bold text-brown-800 mt-1" style={{ color }}>{value}</p>
        </div>
        {trend !== undefined && (
          <div className="flex items-center gap-1 text-sm">
            <span className={cn('font-medium', trend >= 0 ? 'text-green-600' : 'text-red-600')}>
              {trend >= 0 ? '↑' : '↓'} {Math.abs(trend).toFixed(1)}%
            </span>
            {trendLabel && <span className="text-brown-500">{trendLabel}</span>}
          </div>
        )}
      </div>
      <div className="mt-2 h-1.5 bg-cream-200 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: '75%', backgroundColor: color }}
        />
      </div>
    </div>
  );
}
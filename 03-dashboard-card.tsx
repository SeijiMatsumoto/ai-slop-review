// AI-generated PR — review this code
// Description: "Added analytics dashboard card component with real-time data"

import React, { useState, useEffect } from "react";

interface MetricData {
  label: string;
  value: number;
  change: number;
  trend: "up" | "down" | "flat";
}

interface DashboardCardProps {
  title: string;
  metrics: MetricData[];
  refreshInterval?: number;
  onMetricClick?: (metric: MetricData) => void;
}

export function DashboardCard({
  title,
  metrics,
  refreshInterval = 5000,
  onMetricClick,
}: DashboardCardProps) {
  const [data, setData] = useState<MetricData[]>(metrics);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  useEffect(() => {
    const interval = setInterval(async () => {
      const response = await fetch("/api/metrics");
      const freshData = await response.json();
      setData(freshData);
      setLastUpdated(new Date());
    }, refreshInterval);

    return () => clearInterval(interval);
  }, []);

  const formatChange = (change: number) => {
    return change > 0 ? `+${change.toFixed(1)}%` : `${change.toFixed(1)}%`;
  };

  const getTrendColor = (trend: string) => {
    if (trend === "up") return "text-green-500";
    if (trend === "down") return "text-red-500";
    return "text-gray-500";
  };

  return (
    <div className="rounded-lg border bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">{title}</h3>
        <span className="text-xs text-gray-400">
          Updated {lastUpdated.toLocaleTimeString()}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-4">
        {data.map((metric) => (
          <div
            key={metric.label}
            className="cursor-pointer hover:bg-gray-50 p-3 rounded"
            onClick={() => onMetricClick(metric)}
          >
            <p className="text-sm text-gray-600">{metric.label}</p>
            <p className="text-2xl font-bold">{metric.value.toLocaleString()}</p>
            <p className={getTrendColor(metric.trend)}>
              {formatChange(metric.change)}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

export function DashboardGrid({ cards }: { cards: DashboardCardProps[] }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {cards.map((card) => (
        <DashboardCard {...card} />
      ))}
    </div>
  );
}

"use client";

import { useAuth } from "@/hooks/useAuth";
import { Card } from "@/components/ui";

const stats = [
  {
    label: "Compliance Score",
    value: "73%",
    color: "text-warning",
    bgColor: "bg-warning/10",
    description: "Across active frameworks",
    progress: 73,
  },
  {
    label: "Open Risks",
    value: "12",
    color: "text-error",
    bgColor: "bg-error/10",
    description: "Requiring treatment",
  },
  {
    label: "Active Vulnerabilities",
    value: "47",
    color: "text-orange-500",
    bgColor: "bg-orange-50",
    description: "Across all assets",
  },
  {
    label: "Evidence Items",
    value: "156",
    color: "text-success",
    bgColor: "bg-success/10",
    description: "Collected this quarter",
  },
];

const recentActivity = [
  { action: "SOC 2 control CC6.1 marked as implemented", time: "2 hours ago" },
  { action: "AWS security scan completed — 3 new findings", time: "4 hours ago" },
  { action: "Evidence uploaded for access review policy", time: "Yesterday" },
  { action: "Risk R-2024-008 treatment plan approved", time: "Yesterday" },
  { action: "Trivy vulnerability scan completed", time: "2 days ago" },
];

export default function DashboardPage() {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-neutral">
          Welcome back{user?.full_name ? `, ${user.full_name.split(" ")[0]}` : ""}
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Here&apos;s your security and compliance overview.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.label} padding="md">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">{stat.label}</p>
                <p className={`mt-1 text-3xl font-bold ${stat.color}`}>
                  {stat.value}
                </p>
                <p className="mt-1 text-xs text-gray-400">{stat.description}</p>
              </div>
              <div className={`rounded-lg p-2 ${stat.bgColor}`}>
                <div className={`h-5 w-5 ${stat.color}`}>
                  {stat.label === "Compliance Score" && (
                    <svg viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" /></svg>
                  )}
                  {stat.label === "Open Risks" && (
                    <svg viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" /></svg>
                  )}
                  {stat.label === "Active Vulnerabilities" && (
                    <svg viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" /></svg>
                  )}
                  {stat.label === "Evidence Items" && (
                    <svg viewBox="0 0 20 20" fill="currentColor"><path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" /></svg>
                  )}
                </div>
              </div>
            </div>
            {stat.progress !== undefined && (
              <div className="mt-3">
                <progress
                  className="progress progress-warning w-full"
                  value={stat.progress}
                  max={100}
                />
              </div>
            )}
          </Card>
        ))}
      </div>

      <Card>
        <h2 className="mb-4 text-lg font-semibold text-neutral">Recent Activity</h2>
        <div className="divide-y divide-base-200">
          {recentActivity.map((item, i) => (
            <div key={i} className="flex items-center justify-between py-3">
              <p className="text-sm text-gray-700">{item.action}</p>
              <span className="shrink-0 text-xs text-gray-400">{item.time}</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

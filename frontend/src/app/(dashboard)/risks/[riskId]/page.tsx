"use client";

import { useParams } from "next/navigation";
import { Card, Badge } from "@/components/ui";
import { getRisk } from "@/lib/mock-data";
import type { RiskStatusType, RiskCategory } from "@/types/grc";
import Link from "next/link";

const statusVariant: Record<RiskStatusType, "warning" | "info" | "success" | "neutral"> = {
  open: "warning",
  mitigating: "info",
  closed: "success",
  accepted: "neutral",
};

const categoryVariant: Record<RiskCategory, "info" | "warning" | "error" | "neutral" | "success"> = {
  operational: "warning",
  technical: "error",
  compliance: "info",
  strategic: "neutral",
  financial: "warning",
  reputational: "error",
};

function scoreColor(score: number): string {
  if (score >= 20) return "text-error";
  if (score >= 12) return "text-orange-500";
  if (score >= 8) return "text-warning";
  return "text-success";
}

const mockReviewHistory = [
  { date: "2024-11-15", action: "Residual score updated to 5", by: "Maria Garcia" },
  { date: "2024-10-20", action: "Treatment plan updated", by: "Sarah Chen" },
  { date: "2024-09-15", action: "Risk assessment reviewed", by: "James Wilson" },
  { date: "2024-08-01", action: "Risk created", by: "Sarah Chen" },
];

const mockRelatedControls = [
  { code: "CC6.1", title: "Logical and physical access controls" },
  { code: "CC6.3", title: "Role-based access and least privilege" },
  { code: "A.8.3", title: "Information access restriction" },
];

export default function RiskDetailPage() {
  const params = useParams();
  const risk = getRisk(params.riskId as string);

  if (!risk) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-gray-500">Risk not found.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Link href="/risks" className="hover:text-primary">
          Risk Register
        </Link>
        <span>/</span>
        <span className="text-neutral">{risk.title}</span>
      </div>

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-neutral">{risk.title}</h1>
          <div className="mt-2 flex items-center gap-3">
            <Badge variant={categoryVariant[risk.category]} size="sm">
              {risk.category.charAt(0).toUpperCase() + risk.category.slice(1)}
            </Badge>
            <Badge variant={statusVariant[risk.status]} size="sm">
              {risk.status.charAt(0).toUpperCase() + risk.status.slice(1)}
            </Badge>
          </div>
        </div>
      </div>

      <Card>
        <p className="text-sm leading-relaxed text-gray-600">{risk.description}</p>
      </Card>

      {/* Scoring */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Card>
          <h3 className="mb-3 text-sm font-semibold text-gray-500">Inherent Risk</h3>
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-sm">
                <span className="text-gray-500">Likelihood:</span>{" "}
                <span className="font-medium capitalize">{risk.likelihood.replace("_", " ")}</span>
              </p>
              <p className="text-sm">
                <span className="text-gray-500">Impact:</span>{" "}
                <span className="font-medium capitalize">{risk.impact.replace("_", " ")}</span>
              </p>
            </div>
            <span className={`text-4xl font-bold ${scoreColor(risk.inherent_score)}`}>
              {risk.inherent_score}
            </span>
          </div>
        </Card>

        <Card>
          <h3 className="mb-3 text-sm font-semibold text-gray-500">Treatment</h3>
          <p className="text-lg font-semibold capitalize text-neutral">
            {risk.treatment ?? "Not determined"}
          </p>
          {risk.due_date && (
            <p className="mt-2 text-sm text-gray-500">
              Due: {new Date(risk.due_date).toLocaleDateString()}
            </p>
          )}
        </Card>

        <Card>
          <h3 className="mb-3 text-sm font-semibold text-gray-500">Residual Risk</h3>
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">After treatment</p>
            <span
              className={`text-4xl font-bold ${
                risk.residual_score != null
                  ? scoreColor(risk.residual_score)
                  : "text-gray-300"
              }`}
            >
              {risk.residual_score ?? "—"}
            </span>
          </div>
          {risk.residual_score != null && risk.inherent_score > 0 && (
            <p className="mt-2 text-sm text-success">
              {Math.round(((risk.inherent_score - risk.residual_score) / risk.inherent_score) * 100)}% reduction
            </p>
          )}
        </Card>
      </div>

      {/* Owner */}
      <Card>
        <h3 className="mb-2 text-sm font-semibold text-gray-500">Owner</h3>
        <p className="text-base font-medium text-neutral">
          {risk.owner_name ?? "Unassigned"}
        </p>
      </Card>

      {/* Related Controls */}
      <Card>
        <h3 className="mb-3 text-sm font-semibold text-gray-500">
          Related Controls
        </h3>
        <div className="space-y-2">
          {mockRelatedControls.map((ctrl) => (
            <div
              key={ctrl.code}
              className="flex items-center gap-3 rounded-lg border border-base-200 px-4 py-2"
            >
              <span className="font-mono text-sm font-semibold text-gray-600">
                {ctrl.code}
              </span>
              <span className="text-sm">{ctrl.title}</span>
            </div>
          ))}
        </div>
      </Card>

      {/* Review History */}
      <Card>
        <h3 className="mb-3 text-sm font-semibold text-gray-500">
          Review History
        </h3>
        <div className="relative ml-4 border-l-2 border-base-200 pl-6">
          {mockReviewHistory.map((entry, i) => (
            <div key={i} className="relative mb-4 last:mb-0">
              <div className="absolute -left-[31px] top-1 h-3 w-3 rounded-full border-2 border-primary bg-base-100" />
              <p className="text-sm font-medium text-neutral">{entry.action}</p>
              <p className="text-xs text-gray-400">
                {entry.by} &middot; {entry.date}
              </p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

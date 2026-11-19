"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { Card, Badge, Button } from "@/components/ui";
import {
  getFramework,
  getControls,
  getControlCategories,
  getFrameworkComplianceScore,
} from "@/lib/mock-data";
import type { ControlWithStatus, ControlStatus, ControlEffectiveness } from "@/types/grc";
import Link from "next/link";

const statusVariant: Record<ControlStatus, "success" | "warning" | "info" | "error" | "neutral"> = {
  implemented: "success",
  in_progress: "warning",
  not_started: "neutral",
  not_applicable: "info",
  failed: "error",
};

const statusLabel: Record<ControlStatus, string> = {
  implemented: "Implemented",
  in_progress: "In Progress",
  not_started: "Not Started",
  not_applicable: "N/A",
  failed: "Failed",
};

const effectivenessLabel: Record<ControlEffectiveness, string> = {
  none: "None",
  partial: "Partial",
  full: "Full",
};

function StatusBadge({ status }: { status: ControlStatus }) {
  return <Badge variant={statusVariant[status]} size="sm">{statusLabel[status]}</Badge>;
}

function ControlDetail({ control }: { control: ControlWithStatus }) {
  const ts = control.tenant_status;
  return (
    <div className="mt-3 space-y-3 rounded-lg bg-base-200/50 p-4">
      <p className="text-sm text-gray-600">{control.description}</p>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div>
          <p className="text-xs font-medium text-gray-400">Status</p>
          <StatusBadge status={ts?.status ?? "not_started"} />
        </div>
        <div>
          <p className="text-xs font-medium text-gray-400">Effectiveness</p>
          <p className="text-sm font-medium">
            {ts?.effectiveness ? effectivenessLabel[ts.effectiveness] : "—"}
          </p>
        </div>
        <div>
          <p className="text-xs font-medium text-gray-400">Owner</p>
          <p className="text-sm">{ts?.owner_name ?? "Unassigned"}</p>
        </div>
        <div>
          <p className="text-xs font-medium text-gray-400">Evidence</p>
          <p className={`text-sm font-medium ${(ts?.evidence_count ?? 0) > 0 ? "text-success" : "text-gray-400"}`}>
            {ts?.evidence_count ?? 0} items
          </p>
        </div>
      </div>
      {ts?.notes && (
        <div>
          <p className="text-xs font-medium text-gray-400">Notes</p>
          <p className="text-sm text-gray-600">{ts.notes}</p>
        </div>
      )}
      {ts?.last_assessed_at && (
        <p className="text-xs text-gray-400">
          Last assessed: {new Date(ts.last_assessed_at).toLocaleDateString()}
        </p>
      )}
    </div>
  );
}

export default function FrameworkDetailPage() {
  const params = useParams();
  const frameworkId = params.frameworkId as string;
  const [expandedControl, setExpandedControl] = useState<string | null>(null);

  const framework = getFramework(frameworkId);
  const versionId = frameworkId === "fw-soc2" ? "fv-soc2-2017" : "fv-iso27001-2022";
  const controls = getControls(versionId);
  const categories = getControlCategories(controls);
  const score = getFrameworkComplianceScore(versionId);

  if (!framework) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-gray-500">Framework not found.</p>
      </div>
    );
  }

  const [collapsedCategories, setCollapsedCategories] = useState<Set<string>>(new Set());

  const toggleCategory = (cat: string) => {
    setCollapsedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(cat)) next.delete(cat);
      else next.add(cat);
      return next;
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Link href="/compliance" className="hover:text-primary">
          Compliance
        </Link>
        <span>/</span>
        <span className="text-neutral">{framework.name}</span>
      </div>

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-neutral">{framework.name}</h1>
          <p className="mt-1 text-sm text-gray-500">{framework.description}</p>
          <div className="mt-2 flex items-center gap-4 text-sm text-gray-500">
            <span>{framework.organization}</span>
            <span>{controls.length} controls</span>
          </div>
        </div>
        <div className="text-right">
          <span
            className={`text-4xl font-bold ${
              score >= 70 ? "text-success" : score >= 50 ? "text-warning" : "text-error"
            }`}
          >
            {score}%
          </span>
          <p className="text-sm text-gray-500">compliant</p>
        </div>
      </div>

      {categories.map((category) => {
        const catControls = controls.filter((c) => c.category === category);
        const isCollapsed = collapsedCategories.has(category);
        const implemented = catControls.filter(
          (c) => c.tenant_status?.status === "implemented",
        ).length;

        return (
          <Card key={category} padding="sm">
            <button
              className="flex w-full items-center justify-between px-2 py-2"
              onClick={() => toggleCategory(category)}
            >
              <div className="flex items-center gap-3">
                <svg
                  className={`h-4 w-4 text-gray-400 transition-transform ${isCollapsed ? "" : "rotate-90"}`}
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z"
                    clipRule="evenodd"
                  />
                </svg>
                <h3 className="text-base font-semibold text-neutral">
                  {category}
                </h3>
                <span className="text-sm text-gray-400">
                  {catControls.length} controls
                </span>
              </div>
              <span className="text-sm font-medium text-gray-500">
                {implemented}/{catControls.length} implemented
              </span>
            </button>

            {!isCollapsed && (
              <div className="mt-2 space-y-1 px-2">
                {catControls.map((control) => (
                  <div key={control.id}>
                    <button
                      className="flex w-full items-center justify-between rounded-lg px-3 py-2 text-left transition-colors hover:bg-base-200"
                      onClick={() =>
                        setExpandedControl(
                          expandedControl === control.id ? null : control.id,
                        )
                      }
                    >
                      <div className="flex items-center gap-3">
                        <span className="w-16 font-mono text-sm font-semibold text-gray-600">
                          {control.code}
                        </span>
                        <span className="text-sm">{control.title}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        {(control.tenant_status?.evidence_count ?? 0) > 0 && (
                          <span className="text-xs text-gray-400">
                            {control.tenant_status?.evidence_count} evidence
                          </span>
                        )}
                        <StatusBadge
                          status={control.tenant_status?.status ?? "not_started"}
                        />
                      </div>
                    </button>
                    {expandedControl === control.id && (
                      <ControlDetail control={control} />
                    )}
                  </div>
                ))}
              </div>
            )}
          </Card>
        );
      })}
    </div>
  );
}

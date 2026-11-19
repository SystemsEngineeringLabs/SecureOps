"use client";

import { useState } from "react";
import { Card, Badge, Button, Modal, Input } from "@/components/ui";
import { Table, type ColumnDef } from "@/components/ui/Table";
import { getRisks } from "@/lib/mock-data";
import type { Risk, RiskCategory, RiskLikelihood, RiskImpact, RiskStatusType } from "@/types/grc";
import Link from "next/link";

const likelihoodValues: RiskLikelihood[] = ["very_low", "low", "medium", "high", "very_high"];
const impactValues: RiskImpact[] = ["very_low", "low", "medium", "high", "very_high"];
const likelihoodNum: Record<RiskLikelihood, number> = { very_low: 1, low: 2, medium: 3, high: 4, very_high: 5 };
const impactNum: Record<RiskImpact, number> = { very_low: 1, low: 2, medium: 3, high: 4, very_high: 5 };

const categoryVariant: Record<RiskCategory, "info" | "warning" | "error" | "neutral" | "success"> = {
  operational: "warning",
  technical: "error",
  compliance: "info",
  strategic: "neutral",
  financial: "warning",
  reputational: "error",
};

const statusVariant: Record<RiskStatusType, "warning" | "info" | "success" | "neutral"> = {
  open: "warning",
  mitigating: "info",
  closed: "success",
  accepted: "neutral",
};

function scoreColor(score: number): string {
  if (score >= 20) return "text-error";
  if (score >= 12) return "text-orange-500";
  if (score >= 8) return "text-warning";
  return "text-success";
}

function heatmapColor(count: number, lIdx: number, iIdx: number): string {
  const severity = (lIdx + 1) * (iIdx + 1);
  if (count === 0) return "bg-base-200";
  if (severity >= 16) return "bg-error/80 text-white";
  if (severity >= 9) return "bg-orange-400/80 text-white";
  if (severity >= 4) return "bg-warning/80";
  return "bg-success/60";
}

export default function RisksPage() {
  const [showAddModal, setShowAddModal] = useState(false);
  const [categoryFilter, setCategoryFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");

  const risks = getRisks();

  const filteredRisks = risks.filter((r) => {
    if (categoryFilter && r.category !== categoryFilter) return false;
    if (statusFilter && r.status !== statusFilter) return false;
    return true;
  });

  const totalRisks = risks.length;
  const criticalHigh = risks.filter((r) => r.inherent_score >= 16).length;
  const openCount = risks.filter((r) => r.status === "open" || r.status === "mitigating").length;
  const avgScore = Math.round(risks.reduce((s, r) => s + r.inherent_score, 0) / risks.length);

  // Build heatmap grid
  const heatmap: number[][] = Array.from({ length: 5 }, () => Array(5).fill(0) as number[]);
  risks.forEach((r) => {
    const li = likelihoodNum[r.likelihood] - 1;
    const ii = impactNum[r.impact] - 1;
    heatmap[li][ii]++;
  });

  const columns: ColumnDef<Risk>[] = [
    {
      header: "Title",
      accessor: "title",
      sortable: true,
      render: (_, row) => (
        <Link href={`/risks/${row.id}`} className="font-medium text-primary hover:underline">
          {row.title}
        </Link>
      ),
    },
    {
      header: "Category",
      accessor: "category",
      sortable: true,
      render: (val) => (
        <Badge variant={categoryVariant[val as RiskCategory]} size="sm">
          {(val as string).charAt(0).toUpperCase() + (val as string).slice(1)}
        </Badge>
      ),
      className: "hidden md:table-cell",
    },
    {
      header: "Likelihood",
      accessor: "likelihood",
      sortable: true,
      render: (val) => (
        <span className="text-sm capitalize">{(val as string).replace("_", " ")}</span>
      ),
      className: "hidden lg:table-cell",
    },
    {
      header: "Impact",
      accessor: "impact",
      sortable: true,
      render: (val) => (
        <span className="text-sm capitalize">{(val as string).replace("_", " ")}</span>
      ),
      className: "hidden lg:table-cell",
    },
    {
      header: "Score",
      accessor: "inherent_score",
      sortable: true,
      render: (val) => (
        <span className={`font-bold ${scoreColor(val as number)}`}>
          {String(val)}
        </span>
      ),
      className: "text-center w-20",
    },
    {
      header: "Treatment",
      accessor: (row) => row.treatment ?? "—",
      render: (val) => <span className="text-sm capitalize">{String(val)}</span>,
      className: "hidden md:table-cell",
    },
    {
      header: "Status",
      accessor: "status",
      sortable: true,
      render: (val) => (
        <Badge variant={statusVariant[val as RiskStatusType]} size="sm">
          {(val as string).charAt(0).toUpperCase() + (val as string).slice(1)}
        </Badge>
      ),
    },
    {
      header: "Owner",
      accessor: (row) => row.owner_name ?? "—",
      className: "hidden lg:table-cell",
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-neutral">Risk Register</h1>
          <p className="mt-1 text-sm text-gray-500">
            Identify, assess, and manage organizational risks.
          </p>
        </div>
        <Button onClick={() => setShowAddModal(true)}>Add Risk</Button>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {[
          { label: "Total Risks", value: totalRisks, color: "text-neutral" },
          { label: "Critical/High", value: criticalHigh, color: "text-error" },
          { label: "Open", value: openCount, color: "text-warning" },
          { label: "Avg Score", value: avgScore, color: scoreColor(avgScore) },
        ].map((stat) => (
          <Card key={stat.label} padding="sm">
            <p className="text-sm font-medium text-gray-500">{stat.label}</p>
            <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
          </Card>
        ))}
      </div>

      {/* Risk heat map */}
      <Card>
        <h3 className="mb-4 text-lg font-semibold text-neutral">Risk Heat Map</h3>
        <div className="flex items-end gap-2">
          <div className="flex flex-col items-center gap-1 pr-2">
            <span className="mb-1 -rotate-90 whitespace-nowrap text-xs font-medium text-gray-500">
              Likelihood
            </span>
          </div>
          <div className="w-full">
            <div className="grid grid-cols-5 gap-1">
              {[...likelihoodValues].reverse().map((l, lIdx) => (
                impactValues.map((_, iIdx) => {
                  const realLIdx = 4 - lIdx;
                  const count = heatmap[realLIdx][iIdx];
                  return (
                    <div
                      key={`${l}-${iIdx}`}
                      className={`flex h-12 items-center justify-center rounded text-sm font-bold ${heatmapColor(count, realLIdx, iIdx)}`}
                    >
                      {count > 0 ? count : ""}
                    </div>
                  );
                })
              ))}
            </div>
            <div className="mt-1 grid grid-cols-5 gap-1">
              {impactValues.map((v) => (
                <div key={v} className="text-center text-xs capitalize text-gray-400">
                  {v.replace("_", " ")}
                </div>
              ))}
            </div>
            <p className="mt-1 text-center text-xs font-medium text-gray-500">
              Impact
            </p>
          </div>
        </div>
      </Card>

      {/* Filters and table */}
      <div className="flex flex-wrap items-center gap-3">
        <select
          className="select select-bordered select-sm"
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
        >
          <option value="">All Categories</option>
          {(["operational", "technical", "compliance", "strategic", "financial", "reputational"] as RiskCategory[]).map((c) => (
            <option key={c} value={c}>
              {c.charAt(0).toUpperCase() + c.slice(1)}
            </option>
          ))}
        </select>
        <select
          className="select select-bordered select-sm"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="">All Statuses</option>
          {(["open", "mitigating", "closed", "accepted"] as RiskStatusType[]).map((s) => (
            <option key={s} value={s}>
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </option>
          ))}
        </select>
        <span className="text-sm text-gray-500">
          {filteredRisks.length} risks
        </span>
      </div>

      <Card padding="none">
        <Table
          columns={columns}
          data={filteredRisks}
          rowKey={(row) => row.id}
        />
      </Card>

      {/* Add Risk Modal (placeholder) */}
      <Modal
        open={showAddModal}
        onClose={() => setShowAddModal(false)}
        title="Add New Risk"
        actions={
          <div className="flex gap-2">
            <Button variant="ghost" onClick={() => setShowAddModal(false)}>
              Cancel
            </Button>
            <Button onClick={() => setShowAddModal(false)}>Create Risk</Button>
          </div>
        }
      >
        <div className="space-y-4">
          <Input label="Risk Title" placeholder="e.g., Unauthorized data access" />
          <div className="form-control">
            <label className="label"><span className="label-text font-medium">Category</span></label>
            <select className="select select-bordered w-full">
              <option value="">Select category</option>
              {(["operational", "technical", "compliance", "strategic", "financial", "reputational"] as RiskCategory[]).map((c) => (
                <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
              ))}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="form-control">
              <label className="label"><span className="label-text font-medium">Likelihood</span></label>
              <select className="select select-bordered w-full">
                {likelihoodValues.map((v) => (
                  <option key={v} value={v}>{v.replace("_", " ")}</option>
                ))}
              </select>
            </div>
            <div className="form-control">
              <label className="label"><span className="label-text font-medium">Impact</span></label>
              <select className="select select-bordered w-full">
                {impactValues.map((v) => (
                  <option key={v} value={v}>{v.replace("_", " ")}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="form-control">
            <label className="label"><span className="label-text font-medium">Description</span></label>
            <textarea className="textarea textarea-bordered w-full" rows={3} placeholder="Describe the risk..." />
          </div>
        </div>
      </Modal>
    </div>
  );
}

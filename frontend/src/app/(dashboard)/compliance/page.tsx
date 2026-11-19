"use client";

import { useState } from "react";
import { Card, Badge, Button } from "@/components/ui";
import { Table, type ColumnDef } from "@/components/ui/Table";
import {
  getFrameworks,
  getControls,
  getFrameworkComplianceScore,
  getControlCategories,
  getAllControls,
} from "@/lib/mock-data";
import type { ControlWithStatus, ControlStatus } from "@/types/grc";
import Link from "next/link";

type Tab = "overview" | "frameworks" | "controls" | "gap";

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

function StatusBadge({ status }: { status: ControlStatus }) {
  return <Badge variant={statusVariant[status]} size="sm">{statusLabel[status]}</Badge>;
}

export default function CompliancePage() {
  const [tab, setTab] = useState<Tab>("overview");
  const [controlFilter, setControlFilter] = useState("");

  const frameworks = getFrameworks();
  const soc2Score = getFrameworkComplianceScore("fv-soc2-2017");
  const isoScore = getFrameworkComplianceScore("fv-iso27001-2022");
  const allControls = getAllControls();

  const statusCounts = allControls.reduce(
    (acc, c) => {
      const s = c.tenant_status?.status ?? "not_started";
      acc[s] = (acc[s] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>,
  );

  const filteredControls = controlFilter
    ? allControls.filter(
        (c) =>
          c.code.toLowerCase().includes(controlFilter.toLowerCase()) ||
          c.title.toLowerCase().includes(controlFilter.toLowerCase()) ||
          c.category.toLowerCase().includes(controlFilter.toLowerCase()),
      )
    : allControls;

  const gapControls = allControls.filter(
    (c) =>
      c.tenant_status?.status !== "implemented" &&
      c.tenant_status?.status !== "not_applicable",
  );
  const gapCategories = getControlCategories(gapControls);

  const controlColumns: ColumnDef<ControlWithStatus>[] = [
    { header: "Code", accessor: "code", sortable: true, className: "font-mono font-semibold w-24" },
    { header: "Title", accessor: "title", sortable: true },
    { header: "Category", accessor: "category", sortable: true, className: "hidden lg:table-cell" },
    {
      header: "Status",
      accessor: (row) => row.tenant_status?.status ?? "not_started",
      render: (val) => <StatusBadge status={val as ControlStatus} />,
      sortable: true,
    },
    {
      header: "Owner",
      accessor: (row) => row.tenant_status?.owner_name ?? "—",
      className: "hidden md:table-cell",
    },
    {
      header: "Evidence",
      accessor: (row) => row.tenant_status?.evidence_count ?? 0,
      render: (val) => (
        <span className={`font-medium ${Number(val) > 0 ? "text-success" : "text-gray-400"}`}>
          {String(val)}
        </span>
      ),
      className: "text-center w-20",
    },
  ];

  const tabs: { key: Tab; label: string }[] = [
    { key: "overview", label: "Overview" },
    { key: "frameworks", label: "Frameworks" },
    { key: "controls", label: "Controls" },
    { key: "gap", label: "Gap Assessment" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-neutral">Compliance</h1>
        <p className="mt-1 text-sm text-gray-500">
          Track compliance posture across frameworks and controls.
        </p>
      </div>

      {/* Tab navigation */}
      <div className="tabs tabs-bordered">
        {tabs.map((t) => (
          <button
            key={t.key}
            className={`tab ${tab === t.key ? "tab-active" : ""}`}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {tab === "overview" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {[
              { name: "SOC 2 Type II", score: soc2Score, id: "fw-soc2", versionId: "fv-soc2-2017" },
              { name: "ISO 27001:2022", score: isoScore, id: "fw-iso27001", versionId: "fv-iso27001-2022" },
            ].map((fw) => (
              <Link key={fw.id} href={`/compliance/${fw.id}`}>
                <Card className="transition-shadow hover:shadow-md">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-semibold text-neutral">{fw.name}</h3>
                      <p className="mt-1 text-sm text-gray-500">
                        {getControls(fw.versionId).length} controls
                      </p>
                    </div>
                    <div className="text-right">
                      <span
                        className={`text-3xl font-bold ${
                          fw.score >= 70
                            ? "text-success"
                            : fw.score >= 50
                              ? "text-warning"
                              : "text-error"
                        }`}
                      >
                        {fw.score}%
                      </span>
                    </div>
                  </div>
                  <div className="mt-3">
                    <div className="h-2 w-full rounded-full bg-base-200">
                      <div
                        className={`h-2 rounded-full ${
                          fw.score >= 70
                            ? "bg-success"
                            : fw.score >= 50
                              ? "bg-warning"
                              : "bg-error"
                        }`}
                        style={{ width: `${fw.score}%` }}
                      />
                    </div>
                  </div>
                </Card>
              </Link>
            ))}
          </div>

          <Card>
            <h3 className="mb-4 text-lg font-semibold text-neutral">
              Control Status Summary
            </h3>
            <div className="flex flex-wrap gap-3">
              {(Object.keys(statusLabel) as ControlStatus[]).map((s) => (
                <div
                  key={s}
                  className="flex items-center gap-2 rounded-lg border border-base-200 px-4 py-2"
                >
                  <StatusBadge status={s} />
                  <span className="text-lg font-bold text-neutral">
                    {statusCounts[s] || 0}
                  </span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* Frameworks Tab */}
      {tab === "frameworks" && (
        <Card>
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>Framework</th>
                  <th>Organization</th>
                  <th>Version</th>
                  <th>Controls</th>
                  <th>Compliance</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {frameworks.map((fw) => {
                  const versionId =
                    fw.id === "fw-soc2" ? "fv-soc2-2017" : "fv-iso27001-2022";
                  const score = getFrameworkComplianceScore(versionId);
                  const controls = getControls(versionId);
                  return (
                    <tr key={fw.id} className="hover">
                      <td className="font-semibold">{fw.name}</td>
                      <td className="text-gray-500">{fw.organization}</td>
                      <td>
                        {fw.id === "fw-soc2" ? "2017" : "2022"}
                      </td>
                      <td>{controls.length}</td>
                      <td>
                        <div className="flex items-center gap-2">
                          <div className="h-2 w-20 rounded-full bg-base-200">
                            <div
                              className={`h-2 rounded-full ${
                                score >= 70 ? "bg-success" : score >= 50 ? "bg-warning" : "bg-error"
                              }`}
                              style={{ width: `${score}%` }}
                            />
                          </div>
                          <span className="text-sm font-medium">{score}%</span>
                        </div>
                      </td>
                      <td>
                        <Link
                          href={`/compliance/${fw.id}`}
                          className="btn btn-ghost btn-sm"
                        >
                          View
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Controls Tab */}
      {tab === "controls" && (
        <div className="space-y-4">
          <div className="flex items-center gap-4">
            <input
              type="text"
              placeholder="Search controls by code, title, or category..."
              className="input input-bordered w-full max-w-md"
              value={controlFilter}
              onChange={(e) => setControlFilter(e.target.value)}
            />
            <span className="text-sm text-gray-500">
              {filteredControls.length} controls
            </span>
          </div>
          <Card padding="none">
            <Table
              columns={controlColumns}
              data={filteredControls}
              rowKey={(row) => row.id}
            />
          </Card>
        </div>
      )}

      {/* Gap Assessment Tab */}
      {tab === "gap" && (
        <div className="space-y-4">
          <Card>
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-neutral">
                  Gap Assessment
                </h3>
                <p className="text-sm text-gray-500">
                  {gapControls.length} controls require attention
                </p>
              </div>
              <Badge variant={gapControls.length > 10 ? "error" : "warning"}>
                {gapControls.length} gaps
              </Badge>
            </div>
          </Card>

          {gapCategories.map((category) => {
            const catControls = gapControls.filter(
              (c) => c.category === category,
            );
            return (
              <Card key={category}>
                <h4 className="mb-3 text-base font-semibold text-neutral">
                  {category}{" "}
                  <span className="text-sm font-normal text-gray-400">
                    ({catControls.length})
                  </span>
                </h4>
                <div className="space-y-2">
                  {catControls.map((control) => (
                    <div
                      key={control.id}
                      className="flex items-center justify-between rounded-lg border border-base-200 px-4 py-3"
                    >
                      <div className="flex items-center gap-3">
                        <span className="font-mono text-sm font-semibold text-gray-600">
                          {control.code}
                        </span>
                        <span className="text-sm">{control.title}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <StatusBadge
                          status={
                            control.tenant_status?.status ?? "not_started"
                          }
                        />
                        {control.tenant_status?.owner_name && (
                          <span className="hidden text-xs text-gray-400 sm:inline">
                            {control.tenant_status.owner_name}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

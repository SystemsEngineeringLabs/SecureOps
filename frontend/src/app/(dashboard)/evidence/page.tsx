"use client";

import { useState } from "react";
import { Card, Badge, Button, Modal, Input } from "@/components/ui";
import { Table, type ColumnDef } from "@/components/ui/Table";
import { getEvidence, formatFileSize } from "@/lib/mock-data";
import type { Evidence, EvidenceStatus } from "@/types/grc";

const statusVariant: Record<EvidenceStatus, "warning" | "success" | "error" | "neutral"> = {
  pending: "warning",
  approved: "success",
  rejected: "error",
  expired: "neutral",
};

const statusLabel: Record<EvidenceStatus, string> = {
  pending: "Pending",
  approved: "Approved",
  rejected: "Rejected",
  expired: "Expired",
};

export default function EvidencePage() {
  const [showUpload, setShowUpload] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [search, setSearch] = useState("");

  const allEvidence = getEvidence();

  const filtered = allEvidence.filter((e) => {
    if (statusFilter && e.status !== statusFilter) return false;
    if (
      search &&
      !e.title.toLowerCase().includes(search.toLowerCase()) &&
      !e.file_name.toLowerCase().includes(search.toLowerCase()) &&
      !e.tags.some((t) => t.toLowerCase().includes(search.toLowerCase()))
    )
      return false;
    return true;
  });

  const total = allEvidence.length;
  const pending = allEvidence.filter((e) => e.status === "pending").length;
  const approved = allEvidence.filter((e) => e.status === "approved").length;
  const expiring = allEvidence.filter((e) => {
    if (!e.expires_at) return false;
    const days = (new Date(e.expires_at).getTime() - Date.now()) / (1000 * 60 * 60 * 24);
    return days > 0 && days <= 30;
  }).length;

  const columns: ColumnDef<Evidence>[] = [
    {
      header: "Title",
      accessor: "title",
      sortable: true,
      render: (_, row) => (
        <div>
          <p className="font-medium">{row.title}</p>
          <p className="text-xs text-gray-400">{row.file_name}</p>
        </div>
      ),
    },
    {
      header: "Size",
      accessor: "file_size",
      render: (val) => <span className="text-sm">{formatFileSize(val as number)}</span>,
      className: "hidden md:table-cell w-24",
    },
    {
      header: "Status",
      accessor: "status",
      sortable: true,
      render: (val) => (
        <Badge variant={statusVariant[val as EvidenceStatus]} size="sm">
          {statusLabel[val as EvidenceStatus]}
        </Badge>
      ),
    },
    {
      header: "Uploaded By",
      accessor: "uploaded_by_name",
      className: "hidden lg:table-cell",
    },
    {
      header: "Uploaded",
      accessor: "created_at",
      sortable: true,
      render: (val) => (
        <span className="text-sm">
          {new Date(val as string).toLocaleDateString()}
        </span>
      ),
      className: "hidden md:table-cell",
    },
    {
      header: "Expires",
      accessor: (row) => row.expires_at,
      render: (val) => {
        if (!val) return <span className="text-sm text-gray-400">—</span>;
        const date = new Date(val as string);
        const daysUntil = Math.ceil(
          (date.getTime() - Date.now()) / (1000 * 60 * 60 * 24),
        );
        const isExpiring = daysUntil > 0 && daysUntil <= 30;
        const isExpired = daysUntil <= 0;
        return (
          <span
            className={`text-sm ${isExpired ? "text-error" : isExpiring ? "text-warning" : ""}`}
          >
            {date.toLocaleDateString()}
            {isExpiring && (
              <span className="ml-1 text-xs">({daysUntil}d)</span>
            )}
          </span>
        );
      },
      className: "hidden lg:table-cell",
    },
    {
      header: "Ver",
      accessor: "version",
      render: (val) => <span className="text-sm text-gray-500">v{String(val)}</span>,
      className: "w-14 text-center",
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-neutral">Evidence</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage compliance evidence and audit artifacts.
          </p>
        </div>
        <Button onClick={() => setShowUpload(true)}>Upload Evidence</Button>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {[
          { label: "Total Items", value: total, color: "text-neutral" },
          { label: "Pending Approval", value: pending, color: "text-warning" },
          { label: "Expiring Soon", value: expiring, color: "text-orange-500" },
          { label: "Approved", value: approved, color: "text-success" },
        ].map((stat) => (
          <Card key={stat.label} padding="sm">
            <p className="text-sm font-medium text-gray-500">{stat.label}</p>
            <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
          </Card>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <input
          type="text"
          placeholder="Search by title, filename, or tag..."
          className="input input-bordered input-sm w-full max-w-xs"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          className="select select-bordered select-sm"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="">All Statuses</option>
          {(["pending", "approved", "rejected", "expired"] as EvidenceStatus[]).map((s) => (
            <option key={s} value={s}>
              {statusLabel[s]}
            </option>
          ))}
        </select>
        <span className="text-sm text-gray-500">{filtered.length} items</span>
      </div>

      <Card padding="none">
        <Table columns={columns} data={filtered} rowKey={(row) => row.id} />
      </Card>

      {/* Upload Modal */}
      <Modal
        open={showUpload}
        onClose={() => setShowUpload(false)}
        title="Upload Evidence"
        actions={
          <div className="flex gap-2">
            <Button variant="ghost" onClick={() => setShowUpload(false)}>
              Cancel
            </Button>
            <Button onClick={() => setShowUpload(false)}>Upload</Button>
          </div>
        }
      >
        <div className="space-y-4">
          <Input label="Title" placeholder="e.g., Q4 Access Review Report" />
          <div className="form-control">
            <label className="label">
              <span className="label-text font-medium">Description</span>
            </label>
            <textarea
              className="textarea textarea-bordered w-full"
              rows={2}
              placeholder="Brief description of this evidence..."
            />
          </div>
          <div className="form-control">
            <label className="label">
              <span className="label-text font-medium">File</span>
            </label>
            <input
              type="file"
              className="file-input file-input-bordered w-full"
              accept=".pdf,.doc,.docx,.xlsx,.csv,.json,.txt,.png,.jpg"
            />
            <label className="label">
              <span className="label-text-alt text-gray-400">
                Max 50MB. Accepted: PDF, Office, CSV, JSON, images.
              </span>
            </label>
          </div>
          <div className="form-control">
            <label className="label">
              <span className="label-text font-medium">Map to Control</span>
            </label>
            <select className="select select-bordered w-full">
              <option value="">Select a control (optional)</option>
              <option value="c-cc6.1">CC6.1 — Logical and physical access controls</option>
              <option value="c-cc8.1">CC8.1 — Change management processes</option>
              <option value="c-a5.1">A.5.1 — Policies for information security</option>
              <option value="c-a8.3">A.8.3 — Information access restriction</option>
            </select>
          </div>
          <div className="form-control">
            <label className="label">
              <span className="label-text font-medium">Tags</span>
            </label>
            <input
              type="text"
              className="input input-bordered w-full"
              placeholder="Comma-separated tags (e.g., policy, access-control)"
            />
          </div>
        </div>
      </Modal>
    </div>
  );
}

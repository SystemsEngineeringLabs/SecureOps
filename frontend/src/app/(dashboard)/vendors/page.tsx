"use client";

import { useState } from "react";
import { Card, Badge, Button, Modal, Input } from "@/components/ui";
import { Table, type ColumnDef } from "@/components/ui/Table";
import { getVendors } from "@/lib/mock-data";
import type { Vendor, VendorRiskLevel, VendorStatus } from "@/types/grc";

const riskVariant: Record<VendorRiskLevel, "success" | "warning" | "high" | "critical"> = {
  low: "success",
  medium: "warning",
  high: "high",
  critical: "critical",
};

const riskLabel: Record<VendorRiskLevel, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
  critical: "Critical",
};

const statusVariant: Record<VendorStatus, "success" | "warning" | "neutral" | "error"> = {
  active: "success",
  under_review: "warning",
  inactive: "neutral",
  terminated: "error",
};

const statusLabel: Record<VendorStatus, string> = {
  active: "Active",
  under_review: "Under Review",
  inactive: "Inactive",
  terminated: "Terminated",
};

export default function VendorsPage() {
  const [showAddModal, setShowAddModal] = useState(false);

  const vendors = getVendors();
  const totalVendors = vendors.length;
  const activeVendors = vendors.filter((v) => v.status === "active").length;
  const highCritical = vendors.filter(
    (v) => v.risk_level === "high" || v.risk_level === "critical",
  ).length;

  const columns: ColumnDef<Vendor>[] = [
    {
      header: "Vendor",
      accessor: "name",
      sortable: true,
      render: (_, row) => (
        <div>
          <p className="font-medium">{row.name}</p>
          <p className="text-xs text-gray-400">{row.category}</p>
        </div>
      ),
    },
    {
      header: "Risk Level",
      accessor: (row) => row.risk_level,
      sortable: true,
      render: (val) =>
        val ? (
          <Badge variant={riskVariant[val as VendorRiskLevel]} size="sm">
            {riskLabel[val as VendorRiskLevel]}
          </Badge>
        ) : (
          <span className="text-sm text-gray-400">Not assessed</span>
        ),
    },
    {
      header: "Status",
      accessor: "status",
      sortable: true,
      render: (val) => (
        <Badge variant={statusVariant[val as VendorStatus]} size="sm">
          {statusLabel[val as VendorStatus]}
        </Badge>
      ),
    },
    {
      header: "Contract End",
      accessor: (row) => row.contract_end,
      sortable: true,
      render: (val) => {
        if (!val) return <span className="text-sm text-gray-400">—</span>;
        const date = new Date(val as string);
        const daysUntil = Math.ceil(
          (date.getTime() - Date.now()) / (1000 * 60 * 60 * 24),
        );
        return (
          <span
            className={`text-sm ${daysUntil <= 90 && daysUntil > 0 ? "text-warning" : daysUntil <= 0 ? "text-error" : ""}`}
          >
            {date.toLocaleDateString()}
          </span>
        );
      },
      className: "hidden md:table-cell",
    },
    {
      header: "Last Assessment",
      accessor: (row) => row.last_assessment_at,
      sortable: true,
      render: (val) =>
        val ? (
          <span className="text-sm">
            {new Date(val as string).toLocaleDateString()}
          </span>
        ) : (
          <span className="text-sm text-gray-400">Never</span>
        ),
      className: "hidden lg:table-cell",
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-neutral">Vendors</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage third-party vendors and assess vendor risk.
          </p>
        </div>
        <Button onClick={() => setShowAddModal(true)}>Add Vendor</Button>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: "Total Vendors", value: totalVendors, color: "text-neutral" },
          { label: "Active", value: activeVendors, color: "text-success" },
          { label: "High/Critical Risk", value: highCritical, color: "text-error" },
        ].map((stat) => (
          <Card key={stat.label} padding="sm">
            <p className="text-sm font-medium text-gray-500">{stat.label}</p>
            <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
          </Card>
        ))}
      </div>

      <Card padding="none">
        <Table columns={columns} data={vendors} rowKey={(row) => row.id} />
      </Card>

      {/* Add Vendor Modal */}
      <Modal
        open={showAddModal}
        onClose={() => setShowAddModal(false)}
        title="Add Vendor"
        actions={
          <div className="flex gap-2">
            <Button variant="ghost" onClick={() => setShowAddModal(false)}>
              Cancel
            </Button>
            <Button onClick={() => setShowAddModal(false)}>Add Vendor</Button>
          </div>
        }
      >
        <div className="space-y-4">
          <Input label="Vendor Name" placeholder="e.g., Datadog" />
          <div className="form-control">
            <label className="label">
              <span className="label-text font-medium">Category</span>
            </label>
            <select className="select select-bordered w-full">
              <option value="">Select category</option>
              <option value="Cloud Infrastructure">Cloud Infrastructure</option>
              <option value="Monitoring">Monitoring</option>
              <option value="Identity & Access">Identity & Access</option>
              <option value="Operations">Operations</option>
              <option value="Professional Services">Professional Services</option>
              <option value="Development Tools">Development Tools</option>
            </select>
          </div>
          <div className="form-control">
            <label className="label">
              <span className="label-text font-medium">Description</span>
            </label>
            <textarea
              className="textarea textarea-bordered w-full"
              rows={2}
              placeholder="Brief description of services provided..."
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Input label="Contact Name" placeholder="Account manager" />
            <Input label="Contact Email" placeholder="contact@vendor.com" type="email" />
          </div>
          <Input label="Contract End Date" type="date" />
        </div>
      </Modal>
    </div>
  );
}

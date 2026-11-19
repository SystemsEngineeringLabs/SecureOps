"use client";

import { useState } from "react";
import { Card, Badge, Button, Modal, Input } from "@/components/ui";
import { getPolicies } from "@/lib/mock-data";
import type { PolicyStatus } from "@/types/grc";

const statusVariant: Record<PolicyStatus, "success" | "warning" | "neutral"> = {
  published: "success",
  draft: "warning",
  archived: "neutral",
};

const statusLabel: Record<PolicyStatus, string> = {
  published: "Published",
  draft: "Draft",
  archived: "Archived",
};

export default function PoliciesPage() {
  const [showNewPolicy, setShowNewPolicy] = useState(false);
  const [categoryFilter, setCategoryFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [selectedPolicy, setSelectedPolicy] = useState<string | null>(null);

  const policies = getPolicies();

  const categories = [...new Set(policies.map((p) => p.category))];

  const filtered = policies.filter((p) => {
    if (categoryFilter && p.category !== categoryFilter) return false;
    if (statusFilter && p.status !== statusFilter) return false;
    return true;
  });

  const viewPolicy = policies.find((p) => p.id === selectedPolicy);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-neutral">Policies</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage organizational security and compliance policies.
          </p>
        </div>
        <Button onClick={() => setShowNewPolicy(true)}>New Policy</Button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <select
          className="select select-bordered select-sm"
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
        >
          <option value="">All Categories</option>
          {categories.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        <select
          className="select select-bordered select-sm"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="">All Statuses</option>
          {(["published", "draft", "archived"] as PolicyStatus[]).map((s) => (
            <option key={s} value={s}>
              {statusLabel[s]}
            </option>
          ))}
        </select>
        <span className="text-sm text-gray-500">{filtered.length} policies</span>
      </div>

      {/* Policy cards */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {filtered.map((policy) => (
          <Card
            key={policy.id}
            className="cursor-pointer transition-shadow hover:shadow-md"
          >
            <button
              className="w-full text-left"
              onClick={() => setSelectedPolicy(policy.id)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="font-semibold text-neutral">{policy.title}</h3>
                  <p className="mt-1 text-sm text-gray-500">{policy.category}</p>
                </div>
                <Badge variant={statusVariant[policy.status]} size="sm">
                  {statusLabel[policy.status]}
                </Badge>
              </div>
              <div className="mt-3 flex items-center gap-4 text-xs text-gray-400">
                <span>v{policy.version}</span>
                {policy.effective_date && (
                  <span>
                    Effective: {new Date(policy.effective_date).toLocaleDateString()}
                  </span>
                )}
                {policy.review_date && (
                  <span>
                    Review: {new Date(policy.review_date).toLocaleDateString()}
                  </span>
                )}
              </div>
              {policy.owner_name && (
                <p className="mt-2 text-xs text-gray-400">
                  Owner: {policy.owner_name}
                </p>
              )}
            </button>
          </Card>
        ))}
      </div>

      {/* View Policy Modal */}
      <Modal
        open={!!viewPolicy}
        onClose={() => setSelectedPolicy(null)}
        title={viewPolicy?.title ?? ""}
        actions={
          <div className="flex gap-2">
            <Button variant="ghost" onClick={() => setSelectedPolicy(null)}>
              Close
            </Button>
            <Button variant="outline">Edit</Button>
          </div>
        }
      >
        {viewPolicy && (
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <Badge variant={statusVariant[viewPolicy.status]} size="sm">
                {statusLabel[viewPolicy.status]}
              </Badge>
              <span className="text-sm text-gray-500">
                v{viewPolicy.version} &middot; {viewPolicy.category}
              </span>
            </div>
            {viewPolicy.owner_name && (
              <p className="text-sm text-gray-500">
                Owner: {viewPolicy.owner_name}
              </p>
            )}
            <div className="rounded-lg bg-base-200/50 p-4">
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-gray-600">
                {viewPolicy.content}
              </p>
            </div>
            <div className="flex gap-6 text-xs text-gray-400">
              {viewPolicy.effective_date && (
                <span>
                  Effective:{" "}
                  {new Date(viewPolicy.effective_date).toLocaleDateString()}
                </span>
              )}
              {viewPolicy.review_date && (
                <span>
                  Next Review:{" "}
                  {new Date(viewPolicy.review_date).toLocaleDateString()}
                </span>
              )}
            </div>
          </div>
        )}
      </Modal>

      {/* New Policy Modal */}
      <Modal
        open={showNewPolicy}
        onClose={() => setShowNewPolicy(false)}
        title="Create New Policy"
        actions={
          <div className="flex gap-2">
            <Button variant="ghost" onClick={() => setShowNewPolicy(false)}>
              Cancel
            </Button>
            <Button onClick={() => setShowNewPolicy(false)}>Create</Button>
          </div>
        }
      >
        <div className="space-y-4">
          <Input label="Policy Title" placeholder="e.g., Data Retention Policy" />
          <div className="form-control">
            <label className="label">
              <span className="label-text font-medium">Category</span>
            </label>
            <select className="select select-bordered w-full">
              <option value="">Select category</option>
              <option value="Security">Security</option>
              <option value="Access Control">Access Control</option>
              <option value="Data Protection">Data Protection</option>
              <option value="Operations">Operations</option>
              <option value="General">General</option>
            </select>
          </div>
          <div className="form-control">
            <label className="label">
              <span className="label-text font-medium">Content</span>
            </label>
            <textarea
              className="textarea textarea-bordered w-full"
              rows={6}
              placeholder="Write policy content..."
            />
          </div>
        </div>
      </Modal>
    </div>
  );
}

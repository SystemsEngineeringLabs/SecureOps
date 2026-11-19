// Frameworks
export interface Framework {
  id: string;
  key: string;
  name: string;
  description: string;
  organization: string;
}

export interface FrameworkVersion {
  id: string;
  framework_id: string;
  version: string;
  is_current: boolean;
}

export interface Control {
  id: string;
  framework_version_id: string;
  code: string;
  title: string;
  description: string;
  category: string;
  parent_id: string | null;
  sort_order: number;
}

export interface ControlMapping {
  id: string;
  source_control_id: string;
  target_control_id: string;
  mapping_type: "equivalent" | "partial" | "related";
}

export type ControlStatus =
  | "not_started"
  | "in_progress"
  | "implemented"
  | "not_applicable"
  | "failed";

export type ControlEffectiveness = "none" | "partial" | "full";

export interface TenantControlStatus {
  id: string;
  control_id: string;
  status: ControlStatus;
  effectiveness: ControlEffectiveness | null;
  owner_id: string | null;
  owner_name: string | null;
  notes: string | null;
  last_assessed_at: string | null;
  evidence_count: number;
}

export interface ControlWithStatus extends Control {
  tenant_status: TenantControlStatus | null;
}

// Risks
export type RiskCategory =
  | "operational"
  | "technical"
  | "compliance"
  | "strategic"
  | "financial"
  | "reputational";

export type RiskLikelihood = "very_low" | "low" | "medium" | "high" | "very_high";
export type RiskImpact = "very_low" | "low" | "medium" | "high" | "very_high";
export type RiskTreatment = "accept" | "mitigate" | "transfer" | "avoid";
export type RiskStatusType = "open" | "mitigating" | "closed" | "accepted";

export interface Risk {
  id: string;
  title: string;
  description: string;
  category: RiskCategory;
  likelihood: RiskLikelihood;
  impact: RiskImpact;
  inherent_score: number;
  treatment: RiskTreatment | null;
  residual_score: number | null;
  status: RiskStatusType;
  owner_id: string | null;
  owner_name: string | null;
  due_date: string | null;
  created_at: string;
  updated_at: string;
}

// Evidence
export type EvidenceStatus = "pending" | "approved" | "rejected" | "expired";

export interface Evidence {
  id: string;
  title: string;
  description: string;
  file_name: string;
  file_size: number;
  content_type: string;
  sha256_hash: string;
  version: number;
  status: EvidenceStatus;
  uploaded_by: string;
  uploaded_by_name: string;
  approved_by: string | null;
  expires_at: string | null;
  tags: string[];
  created_at: string;
}

// Policies
export type PolicyStatus = "draft" | "published" | "archived";

export interface Policy {
  id: string;
  title: string;
  content: string;
  category: string;
  version: number;
  status: PolicyStatus;
  owner_name: string | null;
  effective_date: string | null;
  review_date: string | null;
  created_at: string;
}

// Vendors
export type VendorRiskLevel = "low" | "medium" | "high" | "critical";
export type VendorStatus = "active" | "under_review" | "inactive" | "terminated";

export interface Vendor {
  id: string;
  name: string;
  description: string;
  category: string;
  risk_level: VendorRiskLevel | null;
  status: VendorStatus;
  contact_name: string | null;
  contact_email: string | null;
  contract_end: string | null;
  last_assessment_at: string | null;
  created_at: string;
}

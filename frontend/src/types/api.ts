export interface Tenant {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  mfa_enabled: boolean;
}

export interface Membership {
  id: string;
  tenant_id: string;
  user_id: string;
  role: MembershipRole;
}

export type MembershipRole =
  | "super_admin"
  | "org_admin"
  | "security_manager"
  | "engineer"
  | "auditor";

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  tenant_name: string;
}

export interface ApiError {
  detail: string;
  status_code: number;
}

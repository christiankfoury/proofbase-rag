import { API_BASE } from "@/lib/apiBase";

export type SecurityEvent = {
  event_id: string;
  occurred_at: string;
  category: string;
  severity: string;
  action: string;
  outcome: string;
  reason_code: string | null;
  correlation_fingerprint: string | null;
};

export type SecurityAlert = {
  alert_id: string;
  rule_id: string;
  category: string;
  severity: string;
  owner: string;
  event_count: number;
  window_minutes: number;
  notification_status: string;
};

export type SecurityMonitoringSnapshot = {
  status: string;
  events: SecurityEvent[];
  alerts: SecurityAlert[];
  integrity: { valid: boolean; record_count: number; head_hash: string };
  taxonomy: Array<{ category: string; severity: string; threshold: number; window_minutes: number; owner: string }>;
  limitations: string[];
};

export async function getSecurityMonitoring(headers: HeadersInit = {}): Promise<SecurityMonitoringSnapshot | null> {
  const response = await fetch(`${API_BASE}/security/monitoring`, { cache: "no-store", headers });
  if (!response.ok) return null;
  return response.json();
}

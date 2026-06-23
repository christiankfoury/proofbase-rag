const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
export const DEMO_USER_HEADER = "X-Demo-User-Id";
export const DEMO_USER_STORAGE_KEY = "eka-demo-user-id";
export const DEFAULT_DEMO_USER_ID = "00000000-0000-0000-0000-000000002701";
export const DEMO_USER_CHANGED_EVENT = "eka-demo-user-changed";

export type DemoMembership = {
  project_id: string;
  project_name: string;
  membership_level: "viewer" | "contributor" | "owner";
};

export type DemoUser = {
  id: string;
  display_name: string;
  email: string;
  business_role: string;
  is_admin: boolean;
  status: "active" | "disabled";
  memberships: DemoMembership[];
};

export function selectedDemoUserId(): string {
  if (typeof window === "undefined") return DEFAULT_DEMO_USER_ID;
  return window.localStorage.getItem(DEMO_USER_STORAGE_KEY) || DEFAULT_DEMO_USER_ID;
}

export function setSelectedDemoUserId(userId: string) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(DEMO_USER_STORAGE_KEY, userId);
  syncDemoUserCookie(userId);
  window.dispatchEvent(new CustomEvent(DEMO_USER_CHANGED_EVENT, { detail: { userId } }));
}

export function syncDemoUserCookie(userId = selectedDemoUserId()) {
  if (typeof window === "undefined") return;
  window.document.cookie = `${DEMO_USER_STORAGE_KEY}=${encodeURIComponent(userId)}; Path=/; Max-Age=31536000; SameSite=Lax`;
}

export function demoAuthHeaders(userId = selectedDemoUserId()): Record<string, string> {
  return { [DEMO_USER_HEADER]: userId };
}

export async function fetchDemoUsers(): Promise<DemoUser[]> {
  const response = await fetch(`${API_BASE}/auth/demo-users`, { cache: "no-store" });
  if (!response.ok) throw new Error("Demo users are unavailable. Apply the Phase 27 schema first.");
  const payload = (await response.json()) as { users: DemoUser[] };
  return payload.users;
}

export async function fetchCurrentDemoUser(userId = selectedDemoUserId()): Promise<DemoUser> {
  const response = await fetch(`${API_BASE}/auth/me`, {
    cache: "no-store",
    headers: demoAuthHeaders(userId),
  });
  if (!response.ok) throw new Error("Current demo user is unavailable.");
  const payload = (await response.json()) as { user: DemoUser };
  return payload.user;
}

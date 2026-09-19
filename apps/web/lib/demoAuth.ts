import { API_BASE } from "@/lib/apiBase";

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

// Shell and page components load identity together (twice in development
// Strict Mode). Share concurrent lookups without caching completed identities.
const identityRequests = new Map<string, Promise<unknown>>();

function shareIdentityRequest<T>(key: string, request: () => Promise<T>): Promise<T> {
  const pending = identityRequests.get(key);
  if (pending) return pending as Promise<T>;
  const promise = request();
  identityRequests.set(key, promise);
  const clear = () => { identityRequests.delete(key); };
  promise.then(clear, clear);
  return promise;
}

function identityError(response: Response): Error {
  if (response.status === 429) {
    const seconds = Number(response.headers.get("Retry-After"));
    return new Error(Number.isFinite(seconds) && seconds > 0
      ? `Too many identity requests. Retry in ${seconds} seconds.`
      : "Too many identity requests. Wait a moment and refresh.");
  }
  return new Error(`Demo identity is unavailable (HTTP ${response.status}). Check the API and database setup.`);
}

export function fetchDemoUsers(): Promise<DemoUser[]> {
  return shareIdentityRequest("users", loadDemoUsers);
}

async function loadDemoUsers(): Promise<DemoUser[]> {
  const response = await fetch(`${API_BASE}/auth/demo-users`, { cache: "no-store" });
  if (!response.ok) throw identityError(response);
  const payload = (await response.json()) as { users: DemoUser[] };
  return payload.users;
}

export function fetchCurrentDemoUser(userId = selectedDemoUserId()): Promise<DemoUser> {
  return shareIdentityRequest(`user:${userId}`, () => loadCurrentDemoUser(userId));
}

async function loadCurrentDemoUser(userId: string): Promise<DemoUser> {
  const response = await fetch(`${API_BASE}/auth/me`, {
    cache: "no-store",
    headers: demoAuthHeaders(userId),
  });
  if (!response.ok) throw identityError(response);
  const payload = (await response.json()) as { user: DemoUser };
  return payload.user;
}

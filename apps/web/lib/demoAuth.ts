const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
export const DEMO_USER_HEADER = "X-Demo-User-Id";
export const DEMO_USER_STORAGE_KEY = "eka-demo-user-id";
export const DEFAULT_DEMO_USER_ID = "00000000-0000-0000-0000-000000002701";
export const DEMO_USER_CHANGED_EVENT = "eka-demo-user-changed";
const NORTHSTAR_PROJECT_ID = "00000000-0000-0000-0000-000000000019";
const NORTHSTAR_PROJECT_NAME = "Northstar Analytics";

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

const NORTHSTAR_VIEWER: DemoMembership = {
  project_id: NORTHSTAR_PROJECT_ID,
  project_name: NORTHSTAR_PROJECT_NAME,
  membership_level: "viewer",
};

const NORTHSTAR_OWNER: DemoMembership = {
  project_id: NORTHSTAR_PROJECT_ID,
  project_name: NORTHSTAR_PROJECT_NAME,
  membership_level: "owner",
};

export const SEEDED_DEMO_USERS: DemoUser[] = [
  {
    id: DEFAULT_DEMO_USER_ID,
    display_name: "Emma Employee",
    email: "employee@northstar.example",
    business_role: "Employee",
    is_admin: false,
    status: "active",
    memberships: [NORTHSTAR_VIEWER],
  },
  {
    id: "00000000-0000-0000-0000-000000002702",
    display_name: "Sam Sales",
    email: "sales@northstar.example",
    business_role: "Sales Representative",
    is_admin: false,
    status: "active",
    memberships: [NORTHSTAR_VIEWER],
  },
  {
    id: "00000000-0000-0000-0000-000000002703",
    display_name: "Mina Manager",
    email: "manager@northstar.example",
    business_role: "Manager",
    is_admin: false,
    status: "active",
    memberships: [NORTHSTAR_VIEWER],
  },
  {
    id: "00000000-0000-0000-0000-000000002704",
    display_name: "Harper HR Admin",
    email: "hr-admin@northstar.example",
    business_role: "HR Admin",
    is_admin: false,
    status: "active",
    memberships: [NORTHSTAR_VIEWER],
  },
  {
    id: "00000000-0000-0000-0000-000000002705",
    display_name: "Ira IT Admin",
    email: "it-admin@northstar.example",
    business_role: "IT Admin",
    is_admin: false,
    status: "active",
    memberships: [NORTHSTAR_VIEWER],
  },
  {
    id: "00000000-0000-0000-0000-000000002706",
    display_name: "Kai Knowledge Manager",
    email: "knowledge-manager@northstar.example",
    business_role: "Knowledge Manager",
    is_admin: true,
    status: "active",
    memberships: [NORTHSTAR_OWNER],
  },
  {
    id: "00000000-0000-0000-0000-000000002707",
    display_name: "Gus Guest",
    email: "guest@external.example",
    business_role: "Employee",
    is_admin: false,
    status: "active",
    memberships: [],
  },
];

function seededDemoUser(userId = selectedDemoUserId()): DemoUser {
  return SEEDED_DEMO_USERS.find((user) => user.id === userId) ?? SEEDED_DEMO_USERS[0];
}

async function fetchWithTimeout(input: RequestInfo | URL, init: RequestInit = {}, timeoutMs = 3000): Promise<Response> {
  const controller = new AbortController();
  const timeout = globalThis.setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(input, { ...init, signal: controller.signal });
  } finally {
    globalThis.clearTimeout(timeout);
  }
}

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
  try {
    const response = await fetchWithTimeout(`${API_BASE}/auth/demo-users`, { cache: "no-store" });
    if (!response.ok) return SEEDED_DEMO_USERS;
    const payload = (await response.json()) as { users: DemoUser[] };
    return payload.users.length ? payload.users : SEEDED_DEMO_USERS;
  } catch {
    return SEEDED_DEMO_USERS;
  }
}

export async function fetchCurrentDemoUser(userId = selectedDemoUserId()): Promise<DemoUser> {
  try {
    const response = await fetchWithTimeout(`${API_BASE}/auth/me`, {
      cache: "no-store",
      headers: demoAuthHeaders(userId),
    });
    if (!response.ok) return seededDemoUser(userId);
    const payload = (await response.json()) as { user: DemoUser };
    return payload.user;
  } catch {
    return seededDemoUser(userId);
  }
}

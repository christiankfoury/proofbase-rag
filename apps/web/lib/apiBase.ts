const DEFAULT_API_BASE = "http://127.0.0.1:8000";

/**
 * Browser requests use the host-published API URL. Server components running
 * inside Docker use the Compose service URL instead of their own localhost.
 */
export function getApiBase(): string {
  if (typeof window === "undefined") {
    return process.env.API_INTERNAL_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE;
  }

  return process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE;
}

export const API_BASE = getApiBase();

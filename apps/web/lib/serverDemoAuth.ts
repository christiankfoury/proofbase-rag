import { cookies } from "next/headers";
import { DEFAULT_DEMO_USER_ID, DEMO_USER_HEADER, DEMO_USER_STORAGE_KEY } from "@/lib/demoAuth";

export async function serverDemoAuthHeaders(): Promise<Record<string, string>> {
  const cookieStore = await cookies();
  const userId = cookieStore.get(DEMO_USER_STORAGE_KEY)?.value ?? DEFAULT_DEMO_USER_ID;
  return { [DEMO_USER_HEADER]: userId };
}

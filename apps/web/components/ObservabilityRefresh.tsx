"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export function ObservabilityRefresh({ intervalSeconds = 15 }: { intervalSeconds?: number }) {
  const router = useRouter();
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  useEffect(() => {
    const id = setInterval(() => {
      router.refresh();
      setLastUpdated(new Date());
    }, intervalSeconds * 1000);
    return () => clearInterval(id);
  }, [router, intervalSeconds]);

  return (
    <div className="flex items-center gap-3 text-sm text-stone-500">
      <span>Last updated: {lastUpdated.toLocaleTimeString()}</span>
      <button
        onClick={() => {
          router.refresh();
          setLastUpdated(new Date());
        }}
        className="rounded border border-stone-300 bg-white px-2 py-1 text-xs hover:border-moss focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-moss focus-visible:ring-offset-1"
      >
        Refresh
      </button>
    </div>
  );
}

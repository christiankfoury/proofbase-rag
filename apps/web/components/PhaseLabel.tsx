import { formatPhaseLabel, formatRunLabel, getPhaseMeta } from "@/lib/phases";
import type { RunLike } from "@/lib/phases";

export function PhaseLabel({
  phase,
  showRaw = false,
  className = "",
}: {
  phase?: string | number | null;
  showRaw?: boolean;
  className?: string;
}) {
  const meta = getPhaseMeta(phase);
  const raw = phase === null || phase === undefined || phase === "" ? null : String(phase);

  return (
    <span className={className} title={meta?.shortDescription ?? raw ?? undefined}>
      {formatPhaseLabel(phase)}
      {showRaw && raw ? <span className="ml-1 text-xs font-normal text-stone-500">({raw})</span> : null}
    </span>
  );
}

export function RunLabel({
  run,
  showRaw = true,
  className = "",
}: {
  run?: RunLike | string | null;
  showRaw?: boolean;
  className?: string;
}) {
  const raw = typeof run === "string" ? run : run?.run_id ?? null;

  return (
    <span className={className} title={raw ?? undefined}>
      <span>{formatRunLabel(run)}</span>
      {showRaw && raw ? <span className="block text-xs font-normal text-stone-500">{raw}</span> : null}
    </span>
  );
}

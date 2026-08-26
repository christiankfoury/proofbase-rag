import evidence from "../../../data/evaluation/defense/phase55-defense-readiness.json";

export type DefenseStageEvidence = (typeof evidence.stages)[number];
export type DefenseGateEvidence = (typeof evidence.hard_gates)[number];

export const defenseEvidence = evidence;

export function defenseStage(label: string): DefenseStageEvidence {
  const stage = evidence.stages.find((item) => item.stage === label);
  if (!stage) throw new Error(`Missing generated defense evidence for ${label}.`);
  return stage;
}

// Thin typed client over the FastAPI backend.
// Types are generated from backend/app/api/openapi.json by openapi-typescript;
// regenerate after backend contract changes with `npm run generate:api`.

import type { components } from "./types";

export type CritiqueRequest = components["schemas"]["CritiqueRequest"];
export type CritiqueQueued = components["schemas"]["CritiqueQueued"];
export type CritiqueResponse = components["schemas"]["CritiqueResponse"];
export type CritiquePending = components["schemas"]["CritiquePending"];
export type HealthResponse = components["schemas"]["HealthResponse"];
export type ParsedThesis = components["schemas"]["ParsedThesis"];
export type CritiqueSections = components["schemas"]["CritiqueSections"];
export type StructureFinding = components["schemas"]["StructureFinding"];
export type StressTestClaim = components["schemas"]["StressTestClaim"];
export type BiasFinding = components["schemas"]["BiasFinding"];
export type DisconfirmingItem = components["schemas"]["DisconfirmingItem"];
export type BaseRateFinding = components["schemas"]["BaseRateFinding"];
export type SetupCritique = components["schemas"]["SetupCritique"];

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

class ApiError extends Error {
  constructor(public status: number, public body: string) {
    super(`API ${status}: ${body}`);
  }
}

async function jsonOrThrow<T>(res: Response): Promise<T> {
  if (!res.ok) {
    throw new ApiError(res.status, await res.text());
  }
  return (await res.json()) as T;
}

export async function submitCritique(thesis: string): Promise<CritiqueQueued> {
  const res = await fetch(`${API_BASE_URL}/api/v1/critique`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ thesis } satisfies CritiqueRequest),
  });
  return jsonOrThrow<CritiqueQueued>(res);
}

export async function getCritique(
  requestId: string,
): Promise<CritiqueResponse | CritiquePending> {
  const res = await fetch(`${API_BASE_URL}/api/v1/critique/${requestId}`);
  return jsonOrThrow<CritiqueResponse | CritiquePending>(res);
}

export function critiqueStreamUrl(requestId: string): string {
  return `${API_BASE_URL}/api/v1/critique/${requestId}/stream`;
}

export function isPending(
  body: CritiqueResponse | CritiquePending,
): body is CritiquePending {
  return body.status === "pending";
}

export { ApiError };

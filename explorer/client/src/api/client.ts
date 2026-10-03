import type { ApiErrorBody } from "../types/persona";

// An error that carries the HTTP status, so the UI can tell a 400 from a 500.
export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

// Generic helper: GET a URL and return the body typed as T.
export async function getJson<T>(url: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(url, { signal });
  if (!response.ok) {
    // fetch only rejects on network errors; HTTP errors (400, 404, 500) must be checked by hand.
    const body = (await response.json().catch(() => null)) as ApiErrorBody | null;
    throw new ApiError(response.status, body?.error ?? `Request failed with status ${response.status}`);
  }
  return (await response.json()) as T;
}

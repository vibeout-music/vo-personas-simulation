import { useEffect, useState } from "react";
import { getJson } from "../api/client";

// One state at a time: it can never be "loading" and "error" at once.
export type ApiState<T> =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "success"; data: T };

type Settled<T> = Exclude<ApiState<T>, { status: "loading" }>;

// Generic data hook: GET `url` and expose its state. Pass null to fetch nothing.
export function useApi<T>(url: string | null): ApiState<T> {
  // Only finished requests are stored, tagged with the URL they answer.
  const [result, setResult] = useState<{ url: string; state: Settled<T> } | null>(null);

  useEffect(() => {
    if (url === null) return;
    // Cancel the request if the URL changes (or the component unmounts) before it finishes,
    // so a slow, outdated response can never overwrite a newer one.
    const controller = new AbortController();

    getJson<T>(url, controller.signal)
      .then((data) => setResult({ url, state: { status: "success", data } }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return; // cancelled on purpose: not an error
        const message = error instanceof Error ? error.message : "Unknown error";
        setResult({ url, state: { status: "error", message } });
      });

    return () => controller.abort(); // cleanup: runs before the next effect and on unmount
  }, [url]);

  // "Loading" is derived, not stored: if the stored result answers another URL, we are waiting.
  return result !== null && result.url === url ? result.state : { status: "loading" };
}

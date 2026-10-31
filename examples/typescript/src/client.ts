// A small client for the Patternode API. Node 22.18+ runs this file as it is (type stripping);
// no dependencies. It does what every call needs: the key header, the body hash on writes, an
// idempotency key on every POST, and retries that honour retry-after.
import { createHash, randomUUID } from "node:crypto";

const RETRYABLE = new Set([429, 500, 502, 503, 504]);

// Branch on `code`, never on the message.
export class PatternodeError extends Error {
  readonly status: number;
  readonly code: string;
  readonly type: string;
  readonly requestId: string | undefined;
  readonly problems: Array<{ index: number; problem: string }>;

  constructor(status: number, code: string, type: string, requestId: string | undefined,
              problems: Array<{ index: number; problem: string }>, message: string) {
    super(`${status} ${code}: ${message} (request ${requestId})`);
    this.status = status;
    this.code = code;
    this.type = type;
    this.requestId = requestId;
    this.problems = problems;
  }
}

export class Patternode {
  readonly apiKey: string;
  readonly baseUrl: string;
  private readonly maxRetries: number;

  constructor(opts: { apiKey?: string; baseUrl?: string; maxRetries?: number } = {}) {
    const key = opts.apiKey ?? process.env.PATTERNODE_API_KEY;
    if (!key) throw new Error("Set PATTERNODE_API_KEY (from your secret store, never from source code).");
    this.apiKey = key;
    this.baseUrl = (opts.baseUrl ?? process.env.PATTERNODE_BASE_URL ?? "http://127.0.0.1:4010").replace(/\/$/, "");
    this.maxRetries = opts.maxRetries ?? 4;
  }

  get<T = any>(path: string): Promise<T> {
    return this.request("GET", path);
  }

  post<T = any>(path: string, body?: unknown, idempotencyKey: string = randomUUID()): Promise<T> {
    return this.request("POST", path, body, idempotencyKey);
  }

  delete<T = any>(path: string): Promise<T> {
    return this.request("DELETE", path);
  }

  async request<T>(method: string, path: string, body?: unknown, idempotencyKey?: string): Promise<T> {
    const raw = body === undefined ? "" : JSON.stringify(body);
    const headers: Record<string, string> = {
      authorization: `Bearer ${this.apiKey}`,
      accept: "application/json",
      "user-agent": "patternode-example-typescript/1",
    };
    if (["POST", "PUT", "PATCH"].includes(method)) {
      headers["content-type"] = "application/json";
      headers["x-amz-content-sha256"] = createHash("sha256").update(raw).digest("hex");
    }
    if (idempotencyKey) headers["idempotency-key"] = idempotencyKey;

    for (let attempt = 0; ; attempt++) {
      const res = await fetch(this.baseUrl + path, { method, headers, body: method === "GET" ? undefined : raw });
      const text = await res.text();
      const payload = text ? JSON.parse(text) : {};
      if (res.ok) return payload as T;
      if (RETRYABLE.has(res.status) && attempt < this.maxRetries) {
        const after = Number(res.headers.get("retry-after"));
        const wait = Number.isFinite(after) && after > 0 ? after * 1000 : Math.min(2 ** attempt, 30) * 1000 * (0.5 + Math.random() / 2);
        await new Promise((r) => setTimeout(r, Math.min(wait, 60_000)));
        continue;
      }
      const err = payload.error ?? {};
      throw new PatternodeError(res.status, err.details?.error_code ?? "unknown", err.type ?? "api_error",
        payload.request_id, err.details?.problems ?? [], err.message ?? "");
    }
  }
}

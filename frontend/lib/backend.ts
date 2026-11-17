import { z } from "zod";
// Server-only internal service hostname. No Clerk secrets or private addresses in the client bundle.
const origin = process.env.DJANGO_API_INTERNAL_URL ?? "http://main:8000";

export class UpstreamError extends Error {
  constructor(public status: number) {
    super(`Django API returned HTTP ${status}`);
  }
}

export async function readBackend<T>(
  path: string,
  schema: z.ZodType<T>,
): Promise<T> {
  const response = await fetch(new URL(path, origin), {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) throw new UpstreamError(response.status);
  return schema.parse(await response.json());
}

export async function proxyBackend(path: string, options: RequestInit = {}) {
  try {
    const upstream = await fetch(new URL(path, origin), {
      ...options,
      cache: "no-store",
    });
    const text = await upstream.text();
    // Auth service / Django owns all the actual authorization.
    return new Response(text, {
      status: upstream.status,
      headers: {
        "Content-Type":
          upstream.headers.get("Content-Type") ?? "application/json",
        "Cache-Control": "no-store",
      },
    });
  } catch {
    return Response.json(
      { error: "content_service_unavailable" },
      { status: 503 },
    );
  }
}

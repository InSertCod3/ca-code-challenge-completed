import { proxyBackend } from "@/lib/backend";
type Context = { params: Promise<{ slug: string }> };

export async function GET(_request: Request, { params }: Context) {
  const { slug } = await params;
  return proxyBackend(`/api/reviews/${encodeURIComponent(slug)}/`);
}

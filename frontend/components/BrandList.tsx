"use client";
import { useEffect, useState, useCallback } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { z } from "zod";
import { PageSchema, type BrandPage, type Industry } from "@/lib/contracts";
import { BrandCard } from "./BrandCard";

type Sort =
  "-average_rating" | "average_rating" | "-review_count" | "review_count";

type LoadState =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready"; data: BrandPage };

const SORTS: Sort[] = [
  "-average_rating",
  "average_rating",
  "-review_count",
  "review_count",
];

export function BrandList() {
  const router = useRouter(),
    pathname = usePathname(),
    params = useSearchParams();
  const industry = params.get("industry") ?? "";
  const rawSort = params.get("sort") ?? "-average_rating";
  const sort: Sort = SORTS.includes(rawSort as Sort)
    ? (rawSort as Sort)
    : "-average_rating";
  const rawPage = Number(params.get("page") ?? 1);
  const page = Number.isSafeInteger(rawPage) && rawPage > 0 ? rawPage : 1;
  const [status, setStatus] = useState<LoadState>({ kind: "loading" });
  const [industries, setIndustries] = useState<Industry[]>([]);
  const [retry, setRetry] = useState(0);
  const navigate = useCallback(
    (next: { industry: string; sort: Sort; page: number }) => {
      const query = new URLSearchParams();
      if (next.industry) query.set("industry", next.industry);
      if (next.sort !== "-average_rating") query.set("sort", next.sort);
      if (next.page > 1) query.set("page", String(next.page));
      router.push(`${pathname}${query.size ? "?" + query.toString() : ""}`, {
        scroll: false,
      });
    },
    [router, pathname],
  );
  useEffect(() => {
    const controller = new AbortController();
    setStatus({ kind: "loading" });
    const query = new URLSearchParams({ sort, page: String(page) });
    if (industry) query.set("industry", industry);
    void (async () => {
      try {
        const response = await fetch(`/api/brands?${query.toString()}`, {
          signal: controller.signal,
        });
        if (!response.ok)
          throw new Error(
            response.status === 400
              ? "Invalid filters."
              : "Unable to load brands. Please try again.",
          );
        const data = PageSchema.parse(await response.json());
        if (controller.signal.aborted) return;
        setIndustries(data.industries);
        setStatus({ kind: "ready", data });
      } catch (error) {
        if (controller.signal.aborted) return;
        setStatus({
          kind: "error",
          message:
            error instanceof z.ZodError
              ? "Unexpected server data. Please retry."
              : error instanceof Error
                ? error.message
                : "Unable to load the directory.",
        });
      }
    })();
    return () => controller.abort();
  }, [industry, sort, page, retry]);
  const result = status.kind === "ready" ? status.data : null;
  return (
    <section
      className="brand-list"
      aria-label="Brand directory"
    >
      <div className="directory-toolbar">
        <div className="form-field">
          <label htmlFor="industry-filter">Industry</label>
          <select
            id="industry-filter"
            value={industry}
            onChange={(e) =>
              navigate({ industry: e.target.value, sort, page: 1 })
            }
          >
            <option value="">All industries</option>
            {industries.map((item) => (
              <option
                key={item.slug}
                value={item.slug}
              >
                {item.name}
              </option>
            ))}
          </select>
        </div>
        <div className="form-field">
          <label htmlFor="brand-sort">Sort by</label>
          <select
            id="brand-sort"
            value={sort}
            onChange={(e) =>
              navigate({ industry, sort: e.target.value as Sort, page: 1 })
            }
          >
            <option value="-average_rating">Highest rated</option>
            <option value="average_rating">Lowest rated</option>
            <option value="-review_count">Most reviewed</option>
            <option value="review_count">Fewest reviewed</option>
          </select>
        </div>
        {industry && (
          <button
            className="text-button"
            type="button"
            onClick={() => navigate({ industry: "", sort, page: 1 })}
          >
            Clear filter
          </button>
        )}
      </div>
      <div
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="directory-status"
      >
        {status.kind === "loading"
          ? "Loading brands…"
          : status.kind === "error"
            ? status.message
            : `${result?.count} ${result?.count === 1 ? "brand" : "brands"} found`}
      </div>
      {status.kind === "loading" && (
        <div
          className="grid grid--directory"
          aria-hidden="true"
        >
          {[0, 1, 2].map((n) => (
            <div
              key={n}
              className="card skeleton"
            >
              <div className="skeleton__line" />
              <div className="skeleton__line" />
              <div className="skeleton__line" />
            </div>
          ))}
        </div>
      )}
      {status.kind === "error" && (
        <div
          className="empty-panel"
          role="alert"
        >
          <h2>We couldn’t load the directory</h2>
          <p>{status.message}</p>
          <button
            type="button"
            className="button"
            onClick={() => setRetry((n) => n + 1)}
          >
            Try again
          </button>
        </div>
      )}
      {result && result.results.length === 0 && (
        <div className="empty-panel">
          <h2>No brands on this page</h2>
          <p>Try another industry or return to the first page.</p>
          <button
            className="button"
            onClick={() => navigate({ industry: "", sort, page: 1 })}
          >
            Show all brands
          </button>
        </div>
      )}
      {result && result.results.length > 0 && (
        <div className="grid grid--directory">
          {result.results.map((brand) => (
            <BrandCard
              key={brand.slug}
              brand={brand}
            />
          ))}
        </div>
      )}
      {result && result.total_pages > 1 && (
        <nav
          className="pagination"
          aria-label="Brand list pages"
        >
          <button
            className="page-numbers"
            disabled={result.previous === null}
            onClick={() =>
              navigate({ industry, sort, page: result.previous ?? 1 })
            }
          >
            ← Previous
          </button>
          <span
            className="pagination__current"
            aria-current="page"
          >
            Page {result.page} of {result.total_pages}
          </span>
          <button
            className="page-numbers"
            disabled={result.next === null}
            onClick={() =>
              navigate({ industry, sort, page: result.next ?? page })
            }
          >
            Next →
          </button>
        </nav>
      )}
    </section>
  );
}

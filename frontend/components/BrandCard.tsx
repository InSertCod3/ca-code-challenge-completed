import Link from "next/link";
import { Brand } from "@/lib/contracts";
import { Stars } from "./Stars";

export function BrandCard({ brand }: { brand: Brand }) {
  return (
    <article className="card brand-card">
      <div className="card__top">
        <span className="badge">{brand.industry?.name ?? "Uncategorized"}</span>
        <span
          className="card__monogram"
          aria-hidden="true"
        >
          {brand.name[0]}
        </span>
      </div>
      <h3>
        <Link href={`/brand/${brand.slug}/`}>{brand.name}</Link>
      </h3>
      <div className="card__rating">
        <Stars rating={brand.average_rating} />
        <span className="meta">
          {brand.review_count} {brand.review_count === 1 ? "review" : "reviews"}
        </span>
      </div>
      <p className="excerpt">{brand.short_description}</p>
      {brand.top_review_snippet && (
        <blockquote className="brand-card__quote">
          <span className="sr-only">Top customer review: </span>“
          {brand.top_review_snippet}”
        </blockquote>
      )}
      <Link
        className="card__more"
        href={`/brand/${brand.slug}/`}
      >
        Read customer reviews <span aria-hidden="true">→</span>
      </Link>
    </article>
  );
}

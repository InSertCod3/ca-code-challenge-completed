import { notFound } from "next/navigation";
import Link from "next/link";
import { DetailSchema } from "@/lib/contracts";
import { readBackend, UpstreamError } from "@/lib/backend";
import { Stars } from "@/components/Stars";

type Props = { params: Promise<{ slug: string }> };

export default async function BrandDetailPage({ params }: Props) {
  const { slug } = await params;
  let brand;
  try {
    brand = await readBackend(
      `/api/brands/${encodeURIComponent(slug)}/`,
      DetailSchema,
    );
  } catch (error) {
    if (error instanceof UpstreamError && error.status === 404) notFound();
    throw error;
  }
  return (
    <>
      <section className="brand-hero">
        <div className="container">
          <nav
            className="breadcrumbs"
            aria-label="Breadcrumb"
          >
            <Link href="/brand">All brands</Link>
            <span aria-hidden="true">/</span>
            <span>{brand.name}</span>
          </nav>
          <span className="badge">
            {brand.industry?.name ?? "Uncategorized"}
          </span>
          <h1>{brand.name}</h1>
          <p>{brand.short_description}</p>
          <div className="brand-hero__stats">
            <Stars rating={brand.average_rating} />
            <span className="meta">
              Based on {brand.review_count} customer reviews
            </span>
          </div>
          <dl className="brand-meta">
            {brand.headquarters && (
              <div>
                <dt>Headquarters</dt>
                <dd>{brand.headquarters}</dd>
              </div>
            )}
            {brand.founded_year && (
              <div>
                <dt>Founded</dt>
                <dd>{brand.founded_year}</dd>
              </div>
            )}
            {brand.website_url && (
              <div>
                <dt>Official website</dt>
                <dd>
                  <a
                    href={brand.website_url}
                    rel="nofollow noopener noreferrer"
                    target="_blank"
                  >
                    Visit website ↗
                  </a>
                </dd>
              </div>
            )}
          </dl>
        </div>
      </section>
      <section className="brand-body">
        <div className="container">
          <article className="content">
            <span className="eyebrow">ABOUT THE BRAND</span>
            <h2>What to know about {brand.name}</h2>
            <p>{brand.body}</p>
          </article>
        </div>
      </section>
      <section className="reviews-section">
        <div className="container">
          <div className="section-header">
            <h2>
              Customer reviews{" "}
              <span className="meta">({brand.review_count})</span>
            </h2>
          </div>
          {brand.reviews.length ? (
            brand.reviews.map((review) => (
              <article
                className="review-item"
                key={review.slug}
              >
                <div className="review-head">
                  <h3>
                    <Link href={`/review/${review.slug}`}>{review.name}</Link>
                  </h3>
                  <Stars rating={review.rating} />
                </div>
                <p className="review-byline">
                  {review.reviewer_name}
                  {review.reviewer_location
                    ? " · " + review.reviewer_location
                    : ""}{" "}
                  ·{" "}
                  <time dateTime={review.published_at}>
                    {new Date(review.published_at).toLocaleDateString()}
                  </time>
                </p>
                <p className="review-body">{review.body.slice(0, 420)}</p>
                <Link
                  className="text-link"
                  href={`/review/${review.slug}`}
                >
                  Read full review →
                </Link>
              </article>
            ))
          ) : (
            <p>No reviews yet.</p>
          )}
        </div>
      </section>
    </>
  );
}

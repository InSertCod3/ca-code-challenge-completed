import { notFound } from "next/navigation";
import Link from "next/link";
import { ReviewSchema } from "@/lib/contracts";
import { readBackend, UpstreamError } from "@/lib/backend";
import { Stars } from "@/components/Stars";

type Props = { params: Promise<{ slug: string }> };

export default async function ReviewPage({ params }: Props) {
  const { slug } = await params;
  let review;
  try {
    review = await readBackend(
      `/api/reviews/${encodeURIComponent(slug)}/`,
      ReviewSchema,
    );
  } catch (error) {
    if (error instanceof UpstreamError && error.status === 404) notFound();
    throw error;
  }
  return (
    <>
      <section className="review-hero">
        <div className="container">
          <Link
            className="brand-link"
            href={`/brand/${review.brand_slug}`}
          >
            ← Back to {review.brand_name}
          </Link>
          <h1>{review.name}</h1>
          <Stars rating={review.rating} />
          <p className="review-byline">
            By {review.reviewer_name} ·{" "}
            <time dateTime={review.published_at}>
              {new Date(review.published_at).toLocaleDateString()}
            </time>
          </p>
        </div>
      </section>
      <section className="brand-body">
        <div className="container">
          <article className="content">
            <span className="eyebrow">THE FULL EXPERIENCE</span>
            <p>{review.body}</p>
            <Link
              className="text-link"
              href={`/brand/${review.brand_slug}`}
            >
              Explore more {review.brand_name} reviews →
            </Link>
          </article>
        </div>
      </section>
    </>
  );
}

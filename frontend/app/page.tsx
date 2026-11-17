import Link from 'next/link';
import {PageSchema,RecentSchema} from '@/lib/contracts';
import {readBackend} from '@/lib/backend';
import {BrandCard} from '@/components/BrandCard';
import {Stars} from '@/components/Stars';
export default async function Home(){
  const [brands,recent]=await Promise.allSettled([
    readBackend('/api/brands/?page_size=6',PageSchema),
    readBackend('/api/reviews/recent/',RecentSchema)]);
  return <>
    <section className="hero"><div className="container"><span className="eyebrow">THE INDEPENDENT REVIEW DIRECTORY</span><h1>Make your next choice <em>an informed one.</em></h1><p>Real-world experiences from customers across insurance, banking, home services, retail, and internet providers.</p><Link className="button button--light" href="/brand">Explore all brands ↗</Link></div></section>
    <section className="section"><div className="container"><div className="section-header"><div><span className="eyebrow">EDITOR’S INDEX</span><h2>Brands worth exploring</h2></div><Link className="text-link" href="/brand">View all brands →</Link></div>
      {brands.status==='fulfilled'?<div className="grid">{brands.value.results.map(item=><BrandCard key={item.slug} brand={item}/>)}</div>:<p role="status">The brand list is temporarily unavailable.</p>}</div></section>
    <section className="section section--contrast"><div className="container"><div className="section-header"><div><span className="eyebrow">FROM THE COMMUNITY</span><h2>Recently shared experiences</h2></div></div>
      {recent.status==='fulfilled'?<div className="grid">{recent.value.reviews.map(review=><article className="card card--review" key={review.slug}>
        <div className="card__top"><Link className="badge" href={`/brand/${review.brand_slug}`}>{review.brand_name}</Link><time className="meta" dateTime={review.published_at}>{new Date(review.published_at).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'})}</time></div>
        <h3><Link href={`/review/${review.slug}`}>{review.name}</Link></h3><Stars rating={review.rating}/><p className="excerpt">{review.body.slice(0,180)}</p><p className="meta card__author">{review.reviewer_name}</p>
      </article>)}</div>:<p role="status">Recent reviews are temporarily unavailable.</p>}</div></section>
  </>;
}

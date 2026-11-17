export function Stars({rating}:{rating:number|null}){
  if(rating===null)return <span className="meta">Not yet rated</span>;
  return <span className="stars" role="img" aria-label={`${rating.toFixed(1)} out of 5 stars`}>
    <span aria-hidden="true">{Array.from({length:5},(_,i)=><span key={i} className={i<Math.round(rating)?'star-full':'star-empty'}>★</span>)}</span>
    <span className="rating-value" aria-hidden="true">{rating.toFixed(1)}</span>
  </span>;
}

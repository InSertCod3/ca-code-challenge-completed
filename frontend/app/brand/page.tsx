import {Suspense} from 'react';
import {BrandList} from '@/components/BrandList';
export const metadata={title:'Browse brands'};
export default function BrandDirectory(){return <section className="section"><div className="container"><div className="section-header"><div><span className="eyebrow">FIND YOUR NEXT BRAND</span><h1>Brand directory</h1></div></div>
  <Suspense fallback={<p role="status">Loading directory…</p>}><BrandList/></Suspense>
</div></section>;}

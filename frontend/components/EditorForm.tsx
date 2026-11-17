'use client';
import {useState} from 'react';
import Link from 'next/link';
import {PatchSchema} from '@/lib/contracts';
export function EditorForm(){
  const [slug,setSlug]=useState('');
  const [description,setDescription]=useState('');
  const [status,setStatus]=useState('');
  const [busy,setBusy]=useState(false);
  async function submit(event:React.FormEvent<HTMLFormElement>){
    event.preventDefault();setStatus('');
    const valid=PatchSchema.safeParse({short_description:description});
    if(!valid.success){setStatus('The description must contain 1–500 characters.');return;}
    if(!/^[a-z0-9-]+$/.test(slug)){setStatus('Enter a valid brand slug.');return;}
    setBusy(true);
    try{
      const response=await fetch(`/api/brands/${encodeURIComponent(slug)}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify(valid.data)});
      const json=await response.json();
      if(!response.ok)throw new Error(response.status===403?'Editor permission required. Ask an admin to link your Clerk ID to an editor account.':json.error??'Could not update the brand.');
      setStatus('Saved. Your description is live.');
    }catch(error){setStatus(error instanceof Error?error.message:'Unable to update brand.');}finally{setBusy(false);}
  }
  return <form onSubmit={submit} className="editor-form"><div className="form-field"><label htmlFor="slug">Brand slug</label><input id="slug" required value={slug} onChange={event=>setSlug(event.target.value)} placeholder="acme-insurance"/></div>
    <div className="form-field"><label htmlFor="description">Short description</label><textarea id="description" required minLength={1} maxLength={500} rows={4} value={description} onChange={event=>setDescription(event.target.value)}/></div>
    <button disabled={busy} className="button" type="submit">{busy?'Saving…':'Save description'}</button><p role="status" aria-live="polite">{status}</p>
    {slug&&/^[a-z0-9-]+$/.test(slug)&&<Link href={`/brand/${slug}`}>View brand ↗</Link>}
  </form>;
}

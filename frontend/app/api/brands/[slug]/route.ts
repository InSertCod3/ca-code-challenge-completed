import {auth} from '@clerk/nextjs/server';
import {NextRequest} from 'next/server';
import {proxyBackend} from '@/lib/backend';
import {PatchSchema} from '@/lib/contracts';
type Context={params:Promise<{slug:string}>};
export async function GET(_request:NextRequest,{params}:Context){
  const {slug}=await params;
  return proxyBackend(`/api/brands/${encodeURIComponent(slug)}/`);
}
export async function PATCH(request:NextRequest,{params}:Context){
  const {userId,getToken}=await auth();
  if(!userId)return Response.json({error:'sign_in_required'},{status:401});
  let payload:unknown;
  try{payload=await request.json();}catch{return Response.json({error:'invalid_json'},{status:400});}
  const parsed=PatchSchema.safeParse(payload);
  if(!parsed.success)return Response.json({error:'validation_error',details:parsed.error.issues},{status:400});
  const token=await getToken();
  if(!token)return Response.json({error:'session_unavailable'},{status:401});
  const {slug}=await params;
  return proxyBackend(`/api/brands/${encodeURIComponent(slug)}/`,{method:'PATCH',
    headers:{'Content-Type':'application/json','Authorization':`Bearer ${token}`},
    body:JSON.stringify(parsed.data)});
}

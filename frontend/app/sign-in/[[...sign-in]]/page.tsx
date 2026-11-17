import {SignIn} from '@clerk/nextjs';
export default function SignInPage(){return <section className="auth-screen"><SignIn routing="path" path="/sign-in"/></section>;}

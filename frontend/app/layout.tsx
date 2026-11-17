import type {Metadata} from 'next';
import Link from 'next/link';
import {Suspense} from 'react';
import {ClerkProvider,Show,SignInButton,SignUpButton,UserButton} from '@clerk/nextjs';
import '../scss/main.scss';
export const metadata:Metadata={title:{default:'Brand Review Journal',template:'%s | Brand Review Journal'},description:'Independent brand and customer reviews'};
export default function RootLayout({children}:{children:React.ReactNode}){
  return <html lang="en"><body><ClerkProvider>
    <a className="skip-link" href="#main-content">Skip to content</a>
    <header className="site-header"><div className="container"><p className="site-title"><Link href="/">Brand Review<span className="site-title__dot">.</span>Journal</Link></p>
      <nav className="site-nav" aria-label="Main navigation"><Link href="/">Home</Link><Link href="/brand">Browse brands</Link><Link href="/editor">Editor</Link></nav>
      <div className="account-nav"><Suspense fallback={<span className="meta">Account</span>}>
        <Show when="signed-out"><SignInButton mode="modal"><button type="button" className="text-button">Sign in</button></SignInButton><SignUpButton mode="modal"><button type="button" className="button">Sign up</button></SignUpButton></Show>
        <Show when="signed-in"><UserButton/></Show>
      </Suspense></div>
    </div></header><main id="main-content">{children}</main>
    <footer className="site-footer"><div className="container">Independent experiences. Better decisions.</div></footer>
  </ClerkProvider></body></html>;
}

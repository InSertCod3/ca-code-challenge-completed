import { SignUp } from "@clerk/nextjs";

export default function SignUpPage() {
  return (
    <section className="auth-screen">
      <SignUp
        routing="path"
        path="/sign-up"
      />
    </section>
  );
}

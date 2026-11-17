import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import { EditorForm } from "@/components/EditorForm";

export const metadata = { title: "Editor" };

export default async function EditorPage() {
  const { userId } = await auth();
  if (!userId) redirect("/sign-in?redirect_url=%2Feditor");
  return (
    <section className="section">
      <div className="container">
        <div className="section-header">
          <div>
            <span className="eyebrow">AUTHORIZED CONTENT UPDATES</span>
            <h1>Brand editor</h1>
            <p>
              Clerk verifies your identity. The independent Django authorization
              service checks your current editor role before saving.
            </p>
          </div>
        </div>
        <EditorForm />
      </div>
    </section>
  );
}

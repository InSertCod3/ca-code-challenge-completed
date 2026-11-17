"use client";
export default function ErrorView({
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  return (
    <section className="section">
      <div className="container">
        <h1>Something went wrong</h1>
        <p>Could not load this page.</p>
        <button
          className="button"
          onClick={reset}
        >
          Try again
        </button>
      </div>
    </section>
  );
}

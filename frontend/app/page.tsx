"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { submitCritique } from "@/lib/api/client";

const EXAMPLE_THESIS =
  "Long AAPL 195, stop 192, target 201, ORB on 5-min. Volume above 20-day average, tech sector strong today.";

export default function HomePage() {
  const router = useRouter();
  const [thesis, setThesis] = useState("");
  const [error, setError] = useState<string | null>(null);

  const submit = useMutation({
    mutationFn: submitCritique,
    onSuccess: (data) => {
      router.push(`/c/${data.request_id}`);
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : "Submission failed.");
    },
  });

  function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    if (thesis.trim().length < 10) {
      setError("Thesis must be at least 10 characters.");
      return;
    }
    submit.mutate(thesis.trim());
  }

  return (
    <div className="mx-auto max-w-3xl px-6 py-10">
      <h1 className="text-3xl font-semibold tracking-tight">Critique a trade idea</h1>
      <p className="mt-3 text-slate-600">
        Paste your thesis in plain English. The system returns a structured critique covering
        trade mechanics, thesis stress test, cognitive-bias check, and disconfirming evidence.
        It never recommends buy or sell.
      </p>

      <form onSubmit={onSubmit} className="mt-6 space-y-4">
        <label htmlFor="thesis" className="block text-sm font-medium text-slate-700">
          Your trade thesis
        </label>
        <textarea
          id="thesis"
          name="thesis"
          rows={8}
          value={thesis}
          onChange={(e) => setThesis(e.target.value)}
          placeholder={EXAMPLE_THESIS}
          className="w-full rounded-lg border border-slate-300 bg-white p-3 text-slate-900 placeholder:text-slate-400 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
          maxLength={4000}
        />
        <div className="flex items-start justify-between gap-4">
          <p className="text-xs text-slate-500 leading-relaxed">
            Tip: include ticker + exchange, entry, stop, target, and the setup. For non-US,
            suffix the ticker with <code>.NS</code> / <code>.BO</code> (India) or
            <code className="ml-1">.DE</code> (Germany). Bare tickers are treated as US.
          </p>
          <button
            type="submit"
            disabled={submit.isPending}
            className="rounded-lg bg-slate-900 px-5 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submit.isPending ? "Submitting..." : "Critique"}
          </button>
        </div>
        {error ? (
          <p role="alert" className="text-sm text-red-600">
            {error}
          </p>
        ) : null}
      </form>
    </div>
  );
}

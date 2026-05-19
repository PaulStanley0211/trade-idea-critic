"use client";

import { useEffect, useState } from "react";
import {
  critiqueStreamUrl,
  type BaseRateFinding,
  type BiasFinding,
  type CritiqueResponse,
  type CritiqueSections,
  type DisconfirmingItem,
  type ParsedThesis,
  type SetupCritique,
  type StressTestClaim,
  type StructureFinding,
} from "@/lib/api/client";

type NodeEvent = {
  node: string;
  summary: string;
  at: number;
};

type ServerError = {
  code: string;
  message: string;
  recoverable: boolean;
};

const VERDICT_STYLES: Record<string, string> = {
  strong: "bg-emerald-100 text-emerald-800 border-emerald-200",
  marginal: "bg-amber-100 text-amber-800 border-amber-200",
  weak: "bg-rose-100 text-rose-800 border-rose-200",
};

export function CritiqueView({ requestId }: { requestId: string }) {
  const [nodes, setNodes] = useState<NodeEvent[]>([]);
  const [status, setStatus] = useState<string>("Connecting...");
  const [result, setResult] = useState<CritiqueResponse | null>(null);
  const [serverError, setServerError] = useState<ServerError | null>(null);
  const [transportError, setTransportError] = useState<string | null>(null);

  useEffect(() => {
    const es = new EventSource(critiqueStreamUrl(requestId));

    const onStatus = (e: MessageEvent<string>) => {
      try {
        const data = JSON.parse(e.data) as { phase: string; message: string };
        setStatus(data.message);
      } catch {
        // ignore malformed event
      }
    };

    const onNodeStarted = (e: MessageEvent<string>) => {
      try {
        const data = JSON.parse(e.data) as { node_name: string };
        setStatus(`Running ${data.node_name}...`);
      } catch {
        // ignore
      }
    };

    const onNodeCompleted = (e: MessageEvent<string>) => {
      try {
        const data = JSON.parse(e.data) as {
          node_name: string;
          summary: string;
        };
        setNodes((prev) => [
          ...prev,
          { node: data.node_name, summary: data.summary, at: Date.now() },
        ]);
      } catch {
        // ignore
      }
    };

    const onFinal = (e: MessageEvent<string>) => {
      try {
        setResult(JSON.parse(e.data) as CritiqueResponse);
        setStatus("Complete");
      } catch (parseErr) {
        setTransportError(`Failed to parse final payload: ${parseErr}`);
      }
      es.close();
    };

    const onServerError = (e: MessageEvent<string>) => {
      try {
        setServerError(JSON.parse(e.data) as ServerError);
      } catch {
        setTransportError("Server sent an error event without a parseable payload.");
      }
      es.close();
    };

    es.addEventListener("status", onStatus as EventListener);
    es.addEventListener("node_started", onNodeStarted as EventListener);
    es.addEventListener("node_completed", onNodeCompleted as EventListener);
    es.addEventListener("final", onFinal as EventListener);
    es.addEventListener("error", onServerError as EventListener);
    es.onerror = () => {
      // Native EventSource onerror fires on connection drops AND end-of-stream.
      // Treat as transport-only if no final/error has been received.
      if (!result && !serverError) {
        setTransportError("Connection to the server was lost.");
      }
      es.close();
    };

    return () => {
      es.close();
    };
    // requestId is the only true input; result/serverError are local state.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [requestId]);

  return (
    <div className="mx-auto max-w-3xl px-6 py-10 space-y-8">
      <header className="space-y-2">
        <p className="text-xs text-slate-500 font-mono">{requestId}</p>
        <h1 className="text-2xl font-semibold tracking-tight">Critique</h1>
      </header>

      {serverError ? (
        <ErrorBanner title="Server error" message={serverError.message} code={serverError.code} />
      ) : null}

      {transportError && !result ? (
        <ErrorBanner title="Connection issue" message={transportError} />
      ) : null}

      {result ? (
        <ResultPanel result={result} />
      ) : (
        <PendingPanel status={status} nodes={nodes} />
      )}
    </div>
  );
}

function PendingPanel({ status, nodes }: { status: string; nodes: NodeEvent[] }) {
  return (
    <section aria-live="polite" className="rounded-xl border border-slate-200 bg-white p-5">
      <div className="flex items-center gap-3 text-sm text-slate-700">
        <span className="h-2 w-2 animate-pulse rounded-full bg-slate-400" />
        {status}
      </div>
      <ol className="mt-4 space-y-2">
        {nodes.map((n) => (
          <li
            key={`${n.node}-${n.at}`}
            className="flex justify-between text-sm text-slate-600 border-b border-slate-100 py-1.5"
          >
            <span className="font-mono">{n.node}</span>
            <span className="text-slate-500">{n.summary}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}

function ResultPanel({ result }: { result: CritiqueResponse }) {
  const verdict = result.verdict ?? "unknown";
  const verdictClass = VERDICT_STYLES[verdict] ?? "bg-slate-100 text-slate-700 border-slate-200";

  return (
    <div className="space-y-6">
      <section className="rounded-xl border border-slate-200 bg-white p-5 space-y-3">
        <div className="flex items-center justify-between gap-4">
          <h2 className="text-base font-semibold">Verdict</h2>
          <span className={`rounded-full border px-3 py-1 text-xs font-medium ${verdictClass}`}>
            {verdict}
          </span>
        </div>
        <p className="text-sm text-slate-600">Status: {result.status}</p>
        <details className="text-sm">
          <summary className="cursor-pointer text-slate-700">Raw thesis</summary>
          <p className="mt-2 text-slate-600 whitespace-pre-wrap">{result.raw_thesis}</p>
        </details>
        {(result.gap_flags ?? []).length > 0 ? (
          <p className="text-xs text-amber-700">
            Gap flags: {(result.gap_flags ?? []).join(", ")}
          </p>
        ) : null}
      </section>

      {result.parsed_thesis ? <ParsedThesisCard parsed={result.parsed_thesis} /> : null}

      {result.sections ? <SectionsCard sections={result.sections} /> : null}
    </div>
  );
}

function ParsedThesisCard({ parsed }: { parsed: ParsedThesis }) {
  const rows: [string, string][] = [
    ["Ticker", parsed.ticker],
    ["Exchange", parsed.exchange],
    ["Direction", parsed.direction],
    ["Entry", parsed.entry?.toString() ?? "-"],
    ["Stop", parsed.stop?.toString() ?? "-"],
    ["Target", parsed.target?.toString() ?? "-"],
    ["Setup", parsed.setup],
    ["Horizon", parsed.time_horizon ?? "-"],
  ];
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5">
      <h2 className="text-base font-semibold mb-3">Parsed thesis</h2>
      <dl className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm">
        {rows.map(([k, v]) => (
          <div key={k} className="contents">
            <dt className="text-slate-500">{k}</dt>
            <dd className="text-slate-900">{v}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

function SectionsCard({ sections }: { sections: CritiqueSections }) {
  return (
    <div className="space-y-6">
      <MechanicsBlock mechanics={sections.mechanics} />
      {sections.setup_critique ? <SetupBlock setup={sections.setup_critique} /> : null}
      <StressTestBlock items={sections.stress_test ?? []} />
      <BiasBlock items={sections.bias ?? []} />
      <DisconfirmingBlock items={sections.disconfirming ?? []} />
      <BaseRatesBlock items={sections.base_rates ?? []} />
    </div>
  );
}

function SectionShell({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5">
      <h2 className="text-base font-semibold mb-3">{title}</h2>
      {children}
    </section>
  );
}

function MechanicsBlock({ mechanics }: { mechanics: StructureFinding }) {
  return (
    <SectionShell title="Trade mechanics">
      <p className="text-sm text-slate-700">{mechanics.verdict}</p>
      <dl className="mt-3 grid grid-cols-3 gap-3 text-sm">
        <Stat label="R/R" value={mechanics.rr_ratio?.toFixed(2) ?? "-"} />
        <Stat label="ATR(14)" value={mechanics.atr_14?.toFixed(2) ?? "-"} />
        <Stat
          label="Stop / ATR"
          value={mechanics.stop_to_atr_multiple?.toFixed(2) ?? "-"}
        />
      </dl>
      {(mechanics.issues ?? []).length > 0 ? (
        <ul className="mt-3 list-disc pl-5 text-sm text-rose-700">
          {(mechanics.issues ?? []).map((issue, i) => (
            <li key={i}>{issue}</li>
          ))}
        </ul>
      ) : null}
    </SectionShell>
  );
}

function SetupBlock({ setup }: { setup: SetupCritique }) {
  return (
    <SectionShell title={`Setup specialist: ${setup.setup}`}>
      <p className="text-sm text-slate-700">{setup.narrative}</p>
      <p className="mt-2 text-xs text-slate-500">Quality: {setup.quality}</p>
    </SectionShell>
  );
}

function StressTestBlock({ items }: { items: StressTestClaim[] }) {
  return (
    <SectionShell title="Thesis stress test">
      {items.length === 0 ? (
        <p className="text-sm text-slate-500">No claims to verify.</p>
      ) : (
        <ul className="space-y-2 text-sm">
          {items.map((item, i) => (
            <li key={i} className="flex justify-between gap-4 border-b border-slate-100 pb-2">
              <span className="text-slate-800">{item.claim}</span>
              <span className="text-slate-500 whitespace-nowrap">{item.verdict}</span>
            </li>
          ))}
        </ul>
      )}
    </SectionShell>
  );
}

function BiasBlock({ items }: { items: BiasFinding[] }) {
  return (
    <SectionShell title="Cognitive-bias check">
      {items.length === 0 ? (
        <p className="text-sm text-slate-500">No biases detected.</p>
      ) : (
        <ul className="space-y-2 text-sm">
          {items.map((item, i) => (
            <li key={i} className="border-b border-slate-100 pb-2">
              <div className="flex justify-between">
                <span className="font-medium text-slate-800">{item.bias}</span>
                <span className="text-slate-500">{item.severity}</span>
              </div>
              <p className="mt-1 text-slate-600">{item.explanation}</p>
            </li>
          ))}
        </ul>
      )}
    </SectionShell>
  );
}

function DisconfirmingBlock({ items }: { items: DisconfirmingItem[] }) {
  return (
    <SectionShell title="Disconfirming evidence">
      {items.length === 0 ? (
        <p className="text-sm text-slate-500">No counter-evidence found.</p>
      ) : (
        <ul className="space-y-2 text-sm">
          {items.map((item, i) => (
            <li key={i} className="border-b border-slate-100 pb-2">
              <div className="flex justify-between">
                <span className="font-medium text-slate-800">{item.headline}</span>
                <span className="text-slate-500 text-xs">{item.source}</span>
              </div>
              <p className="mt-1 text-slate-600">{item.summary}</p>
            </li>
          ))}
        </ul>
      )}
    </SectionShell>
  );
}

function BaseRatesBlock({ items }: { items: BaseRateFinding[] }) {
  return (
    <SectionShell title="Base rates">
      {items.length === 0 ? (
        <p className="text-sm text-slate-500">No matching base rates.</p>
      ) : (
        <ul className="space-y-2 text-sm">
          {items.map((item, i) => (
            <li key={i} className="flex justify-between border-b border-slate-100 pb-2">
              <span className="text-slate-800">{item.setup}</span>
              <span className="text-slate-500">
                hit rate {(item.hit_rate * 100).toFixed(0)}% over n={item.sample_size}
              </span>
            </li>
          ))}
        </ul>
      )}
    </SectionShell>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-slate-100 bg-slate-50 p-3">
      <dt className="text-xs uppercase tracking-wide text-slate-500">{label}</dt>
      <dd className="text-lg font-medium text-slate-900">{value}</dd>
    </div>
  );
}

function ErrorBanner({
  title,
  message,
  code,
}: {
  title: string;
  message: string;
  code?: string;
}) {
  return (
    <div role="alert" className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
      <p className="font-medium">{title}</p>
      <p className="mt-1">{message}</p>
      {code ? <p className="mt-1 font-mono text-xs">{code}</p> : null}
    </div>
  );
}

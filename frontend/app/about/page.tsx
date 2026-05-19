export default function AboutPage() {
  return (
    <article className="mx-auto max-w-2xl px-6 py-10 prose prose-slate">
      <h1 className="text-2xl font-semibold tracking-tight">About</h1>
      <p className="mt-3 text-slate-700">
        Trade-Idea Critic is an agentic system that critiques a trader&apos;s thesis before
        the trade is taken. It coordinates a planner, six specialist agents, a synthesizer,
        and a critic over public market data for US, Indian, and German equities. Two
        setups are deeply encoded: Opening Range Breakout and Support / Resistance Bounce.
      </p>
      <h2 className="mt-6 text-lg font-semibold">What it returns</h2>
      <ul className="mt-2 list-disc pl-5 text-slate-700 space-y-1">
        <li>A top-line characterization of the setup as strong, marginal, or weak.</li>
        <li>Trade-mechanics critique: R/R, ATR, stop placement, sizing.</li>
        <li>A claim-by-claim stress test of the thesis against market data.</li>
        <li>A cognitive-bias check (anchoring, recency, confirmation, overconfidence, revenge).</li>
        <li>Disconfirming evidence pulled from news and filings.</li>
        <li>Historical base rates for similar setups, where available.</li>
      </ul>
      <h2 className="mt-6 text-lg font-semibold">What it does not do</h2>
      <ul className="mt-2 list-disc pl-5 text-slate-700 space-y-1">
        <li>It never recommends buy or sell. The output filter blocks that language.</li>
        <li>It does not execute orders or copy trades.</li>
        <li>It does not cover options, futures, crypto, or FX.</li>
      </ul>
      <p className="mt-6 text-sm text-slate-500">
        Open source under the MIT license. See the repository for the architecture and code.
      </p>
    </article>
  );
}

"use client";

import { use } from "react";
import { CritiqueView } from "@/components/critique-view";

// Next 15 dynamic-route params arrive as a Promise; unwrap with React.use.
export default function CritiquePage({
  params,
}: {
  params: Promise<{ request_id: string }>;
}) {
  const { request_id } = use(params);
  return <CritiqueView requestId={request_id} />;
}

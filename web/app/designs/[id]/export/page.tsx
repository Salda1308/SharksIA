"use client";
import { useEffect, useState } from "react";
import { api, Design } from "@/lib/api";
import { useParams, useRouter } from "next/navigation";
import ExportPanel from "@/components/ExportPanel";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function ExportPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [design, setDesign] = useState<Design | null>(null);
  const [rendering, setRendering] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.designs.get(id)
      .then(async (d) => {
        if (d.status !== "rendered") {
          setRendering(true);
          try {
            const rendered = await api.designs.render(id);
            setDesign(rendered);
          } catch {
            setError("Error al renderizar el diseño.");
            // Do NOT set design — keep user blocked so they can't export an unrendered design
          } finally {
            setRendering(false);
          }
        } else {
          setDesign(d);
        }
      })
      .catch(() => setError("No se pudo cargar el diseño."));
  }, [id]);

  if (error && !design) return <div className="p-8 text-red-500">{error}</div>;

  if (!design || rendering) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="text-lg font-medium mb-2">Preparando diseño...</div>
          <div className="text-sm text-gray-500">Renderizando slides</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center gap-3 mb-6">
          <button onClick={() => router.push(`/designs/${id}/edit`)}
            className="text-gray-400 hover:text-gray-600">←</button>
          <h1 className="text-2xl font-bold">{design.title ?? "Exportar diseño"}</h1>
        </div>
        {error && <p className="text-red-500 text-sm mb-4">{error}</p>}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h2 className="text-sm font-medium text-gray-500 mb-3">
              {design.slides?.length ?? 0} slides generados
            </h2>
            <div className="space-y-2">
              {design.slides?.map((s, i) => (
                <div key={i} className="flex items-center gap-2 text-sm border rounded-lg px-3 py-2 bg-white">
                  <span className="text-gray-400">{i + 1}.</span>
                  <span className="font-medium">{s.type}</span>
                  <span className="text-gray-500 truncate">
                    {(s.title as string) ?? (s.heading as string) ?? (s.number as string) ?? ""}
                  </span>
                </div>
              ))}
            </div>
          </div>
          <ExportPanel designId={id} apiBase={API_BASE} />
        </div>
      </div>
    </div>
  );
}

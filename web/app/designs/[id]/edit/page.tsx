"use client";
import { useEffect, useState, useCallback } from "react";
import { api, Design, Slide } from "@/lib/api";
import { useParams, useRouter } from "next/navigation";
import SlideEditor from "@/components/SlideEditor";
import SlidePreview from "@/components/SlidePreview";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function EditDesignPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [design, setDesign] = useState<Design | null>(null);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [rendering, setRendering] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => { api.designs.get(id).then(setDesign); }, [id]);

  const currentSlide = design?.slides?.[currentIdx];

  const updateSlide = useCallback(async (updated: Slide) => {
    if (!design?.slides) return;
    const newSlides = design.slides.map((s, i) => i === currentIdx ? updated : s);
    setSaving(true);
    try {
      const d = await api.designs.updateSlides(id, newSlides);
      setDesign(d);
    } finally { setSaving(false); }
  }, [design, currentIdx, id]);

  const render = async () => {
    setRendering(true);
    try { await api.designs.render(id); }
    finally { setRendering(false); }
  };

  if (!design) return <div className="p-8">Cargando diseño...</div>;
  const slides = design.slides ?? [];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="border-b bg-white px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button onClick={() => router.push("/dashboard")} className="text-gray-400 hover:text-gray-600">←</button>
          <span className="font-medium">{design.title ?? "Sin título"}</span>
          {saving && <span className="text-xs text-gray-400">Guardando...</span>}
        </div>
        <div className="flex gap-2">
          <button onClick={render} disabled={rendering}
            className="border px-4 py-1.5 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50">
            {rendering ? "Renderizando..." : "Actualizar preview"}
          </button>
          <button onClick={() => router.push(`/designs/${id}/export`)}
            className="bg-black text-white px-4 py-1.5 rounded-lg text-sm">
            Exportar →
          </button>
        </div>
      </div>

      <div className="max-w-5xl mx-auto p-6 grid grid-cols-2 gap-6">
        <div>
          <SlidePreview
            svgUrl={design.status === "rendered"
              ? `${API_BASE}/api/v1/designs/${id}/export?fmt=svg&slide=${currentIdx}`
              : null}
            loading={rendering}
          />
          <div className="flex items-center justify-between mt-3">
            <button onClick={() => setCurrentIdx(i => Math.max(0, i - 1))}
              disabled={currentIdx === 0}
              className="border px-3 py-1 rounded-lg text-sm disabled:opacity-30">← Anterior</button>
            <span className="text-sm text-gray-500">{currentIdx + 1} / {slides.length}</span>
            <button onClick={() => setCurrentIdx(i => Math.min(slides.length - 1, i + 1))}
              disabled={currentIdx === slides.length - 1}
              className="border px-3 py-1 rounded-lg text-sm disabled:opacity-30">Siguiente →</button>
          </div>
        </div>

        <div className="bg-white rounded-xl p-5 shadow-sm">
          <div className="flex gap-1 mb-4 flex-wrap">
            {slides.map((s, i) => (
              <button key={i} onClick={() => setCurrentIdx(i)}
                className={`text-xs px-2 py-1 rounded-full border ${i === currentIdx ? "bg-black text-white" : "bg-white"}`}>
                {i + 1}. {s.type}
              </button>
            ))}
          </div>
          {currentSlide && (
            <SlideEditor slide={currentSlide} onChange={updateSlide} />
          )}
        </div>
      </div>
    </div>
  );
}

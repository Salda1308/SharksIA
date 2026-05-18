"use client";
import { useState } from "react";

interface Props { designId: string; apiBase: string }

const FORMATS = [
  { key: "pdf", label: "PDF", desc: "Multipágina, ideal para presentaciones" },
  { key: "svg", label: "SVG (ZIP)", desc: "Editable en Illustrator y Figma" },
  { key: "jpg", label: "JPG (ZIP)", desc: "Listo para publicar en Instagram" },
] as const;

export default function ExportPanel({ designId, apiBase }: Props) {
  const [selected, setSelected] = useState<"pdf" | "svg" | "jpg">("pdf");
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState("");

  const download = async () => {
    setDownloading(true);
    setError("");
    try {
      const url = `${apiBase}/api/v1/designs/${designId}/export?fmt=${selected}`;
      const res = await fetch(url, { credentials: "include" });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail ?? "Error al exportar");
      }
      const blob = await res.blob();
      const objectUrl = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = objectUrl;
      a.download = `carousel-${designId}.${selected === "svg" || selected === "jpg" ? "zip" : selected}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(() => URL.revokeObjectURL(objectUrl), 100);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al descargar");
    } finally { setDownloading(false); }
  };

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm">
      <h2 className="text-lg font-semibold mb-4">Exportar diseño</h2>
      <div className="space-y-3 mb-6">
        {FORMATS.map(f => (
          <label key={f.key}
            className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer ${
              selected === f.key ? "border-black bg-gray-50" : "border-gray-200"
            }`}>
            <input type="radio" name="fmt" value={f.key} checked={selected === f.key}
              onChange={() => setSelected(f.key)} className="mt-0.5" />
            <div>
              <div className="font-medium text-sm">{f.label}</div>
              <div className="text-xs text-gray-500">{f.desc}</div>
            </div>
          </label>
        ))}
      </div>
      {error && <p className="text-red-500 text-sm mb-3">{error}</p>}
      <button onClick={download} disabled={downloading}
        className="w-full bg-black text-white py-2.5 rounded-lg hover:bg-gray-800 disabled:opacity-50">
        {downloading ? "Descargando..." : `Descargar ${selected.toUpperCase()}`}
      </button>
      <p className="text-xs text-gray-400 mt-3 text-center">
        Los SVG se abren en Illustrator, Figma y Canva
      </p>
    </div>
  );
}

"use client";
import { useState } from "react";
import { Company, CompanyCreate } from "@/lib/api";

const STYLES = ["minimal", "bold", "editorial", "corporate"];

interface Props {
  initial?: Partial<Company>;
  onSubmit: (data: CompanyCreate) => Promise<void>;
  submitLabel?: string;
}

export default function CompanyForm({ initial, onSubmit, submitLabel = "Guardar" }: Props) {
  const [form, setForm] = useState<CompanyCreate>({
    name: initial?.name ?? "",
    style: initial?.style ?? "minimal",
    colors: initial?.colors ?? { primary: "#000000", secondary: "#ffffff", background: "#f8f8f8", text: "#2d2d2d" },
    fonts: initial?.fonts ?? { heading: "Georgia Bold", body: "Arial" },
    design_context: initial?.design_context ?? "",
    ai_provider: initial?.ai_provider ?? "ollama",
  });
  const [error, setError] = useState("");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try { await onSubmit(form); }
    catch (err: unknown) { setError(err instanceof Error ? err.message : "Error"); }
  };

  const setColor = (key: string, val: string) =>
    setForm(f => ({ ...f, colors: { ...f.colors!, [key]: val } }));

  const setFont = (key: string, val: string) =>
    setForm(f => ({ ...f, fonts: { ...f.fonts!, [key]: val } }));

  return (
    <form onSubmit={submit} className="space-y-5 max-w-lg">
      <div>
        <label className="block text-sm font-medium mb-1">Nombre de la empresa</label>
        <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })}
          className="w-full border rounded-lg px-3 py-2" required />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Estilo visual</label>
        <div className="flex gap-2 flex-wrap">
          {STYLES.map(s => (
            <button key={s} type="button"
              onClick={() => setForm({ ...form, style: s })}
              className={`px-3 py-1 rounded-full border text-sm ${form.style === s ? "bg-black text-white" : "bg-white"}`}>
              {s}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">Colores de marca</label>
        <div className="grid grid-cols-2 gap-3">
          {Object.entries(form.colors ?? {}).map(([key, val]) => (
            <label key={key} className="flex items-center gap-2 text-sm">
              <input type="color" value={val as string} onChange={e => setColor(key, e.target.value)}
                className="w-8 h-8 rounded cursor-pointer" />
              {key}
            </label>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">Tipografías</label>
        <div className="space-y-2">
          {Object.entries(form.fonts ?? {}).map(([key, val]) => (
            <div key={key} className="flex items-center gap-2">
              <span className="text-sm w-20">{key}:</span>
              <input value={val as string} onChange={e => setFont(key, e.target.value)}
                className="flex-1 border rounded-lg px-3 py-1 text-sm" />
            </div>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Contexto de diseño</label>
        <textarea value={form.design_context ?? ""}
          onChange={e => setForm({ ...form, design_context: e.target.value })}
          rows={4} placeholder="Describe el tono, audiencia, y valores de la marca..."
          className="w-full border rounded-lg px-3 py-2 text-sm" />
      </div>

      {error && <p className="text-red-500 text-sm">{error}</p>}
      <button type="submit"
        className="bg-black text-white px-6 py-2 rounded-lg hover:bg-gray-800">
        {submitLabel}
      </button>
    </form>
  );
}

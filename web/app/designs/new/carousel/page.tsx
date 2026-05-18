"use client";
import { useEffect, useState } from "react";
import { api, Company } from "@/lib/api";
import { useRouter } from "next/navigation";

const SIZES = [
  { label: "1:1 (1080×1080)", value: { width: 1080, height: 1080 } },
  { label: "4:5 (1080×1350)", value: { width: 1080, height: 1350 } },
  { label: "9:16 (1080×1920)", value: { width: 1080, height: 1920 } },
];

export default function NewCarouselPage() {
  const router = useRouter();
  const [companies, setCompanies] = useState<Company[]>([]);
  const [form, setForm] = useState({
    company_id: "",
    mode: "topic" as "topic" | "text",
    content: "",
    size_px: SIZES[0].value,
    title: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => { api.companies.list().then(setCompanies).catch(() => {}); }, []);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const design = await api.designs.generate(form);
      router.push(`/designs/${design.id}/edit`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al generar");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-8">
      <h1 className="text-2xl font-bold mb-6">Nuevo carrusel</h1>
      <form onSubmit={submit} className="space-y-5">
        <div>
          <label className="block text-sm font-medium mb-1">Empresa</label>
          <select value={form.company_id}
            onChange={e => setForm({ ...form, company_id: e.target.value })}
            className="w-full border rounded-lg px-3 py-2" required>
            <option value="">Selecciona una empresa...</option>
            {companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Tamaño</label>
          <div className="flex gap-2 flex-wrap">
            {SIZES.map(s => (
              <button key={s.label} type="button"
                onClick={() => setForm({ ...form, size_px: s.value })}
                className={`px-3 py-1 rounded-full border text-sm ${
                  form.size_px.width === s.value.width ? "bg-black text-white" : "bg-white"
                }`}>
                {s.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Modo</label>
          <div className="flex gap-3">
            {(["topic", "text"] as const).map(m => (
              <label key={m} className="flex items-center gap-2 cursor-pointer">
                <input type="radio" value={m} checked={form.mode === m}
                  onChange={() => setForm({ ...form, mode: m })} />
                <span className="text-sm">{m === "topic" ? "Tema corto" : "Texto largo"}</span>
              </label>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">
            {form.mode === "topic" ? "Tema" : "Texto o artículo"}
          </label>
          {form.mode === "topic" ? (
            <input value={form.content}
              onChange={e => setForm({ ...form, content: e.target.value })}
              placeholder="ej: beneficios del marketing digital"
              className="w-full border rounded-lg px-3 py-2" required />
          ) : (
            <textarea value={form.content}
              onChange={e => setForm({ ...form, content: e.target.value })}
              rows={8} placeholder="Pega aquí el artículo o texto largo..."
              className="w-full border rounded-lg px-3 py-2 text-sm" required />
          )}
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Título (opcional)</label>
          <input value={form.title}
            onChange={e => setForm({ ...form, title: e.target.value })}
            placeholder="Nombre del diseño para identificarlo"
            className="w-full border rounded-lg px-3 py-2" />
        </div>

        {error && <p className="text-red-500 text-sm">{error}</p>}
        <button type="submit" disabled={loading}
          className="w-full bg-black text-white py-2.5 rounded-lg hover:bg-gray-800 disabled:opacity-50">
          {loading ? "Generando con IA..." : "Generar carrusel →"}
        </button>
      </form>
    </div>
  );
}

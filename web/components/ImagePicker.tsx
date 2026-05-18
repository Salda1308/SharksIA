"use client";
import { useState } from "react";
import { api, ImageResult } from "@/lib/api";

interface Props {
  onSelect: (url: string) => void;
  onClose: () => void;
}

export default function ImagePicker({ onSelect, onClose }: Props) {
  const [query, setQuery] = useState("");
  const [source, setSource] = useState<"pexels" | "pixabay">("pexels");
  const [results, setResults] = useState<ImageResult[]>([]);
  const [searching, setSearching] = useState(false);

  const search = async () => {
    if (!query.trim()) return;
    setSearching(true);
    try {
      const res = await api.images.search(query, source);
      setResults(res);
    } finally { setSearching(false); }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    const res = await api.images.upload(file) as { thumb_url: string };
    onSelect(`${API_URL}${res.thumb_url}`);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold">Elegir imagen</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">×</button>
        </div>

        <div className="flex gap-2 mb-4">
          <input value={query} onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === "Enter" && search()}
            placeholder="Buscar foto..." className="flex-1 border rounded-lg px-3 py-2" />
          <select value={source} onChange={e => setSource(e.target.value as "pexels" | "pixabay")}
            className="border rounded-lg px-2 py-2">
            <option value="pexels">Pexels</option>
            <option value="pixabay">Pixabay</option>
          </select>
          <button onClick={search} disabled={searching}
            className="bg-black text-white px-4 py-2 rounded-lg text-sm disabled:opacity-50">
            {searching ? "..." : "Buscar"}
          </button>
        </div>

        <label className="block mb-4 cursor-pointer">
          <div className="border-2 border-dashed rounded-lg p-4 text-center text-sm text-gray-500 hover:bg-gray-50">
            O sube tu propia imagen
          </div>
          <input type="file" accept="image/*" className="hidden" onChange={handleUpload} />
        </label>

        <div className="grid grid-cols-3 gap-2">
          {results.map(img => (
            <button key={img.id} onClick={() => { onSelect(img.url); onClose(); }}
              className="aspect-square overflow-hidden rounded-lg hover:ring-2 ring-black">
              <img src={img.thumb} alt={img.alt} className="w-full h-full object-cover" />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

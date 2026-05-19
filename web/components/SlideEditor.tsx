"use client";
import { useState } from "react";
import { Slide } from "@/lib/api";
import ImagePicker from "./ImagePicker";

interface Props { slide: Slide; onChange: (updated: Slide) => void }

export default function SlideEditor({ slide, onChange }: Props) {
  const [showPicker, setShowPicker] = useState(false);
  const set = (key: string, val: unknown) => onChange({ ...slide, [key]: val });

  return (
    <div className="space-y-3">
      <div className="text-xs font-semibold uppercase text-gray-400 mb-2">
        Tipo: {slide.type}
      </div>

      {slide.type === "cover" && (
        <>
          <Field label="Título" value={slide.title as string ?? ""} onChange={v => set("title", v)} />
          <Field label="Subtítulo" value={slide.subtitle as string ?? ""} onChange={v => set("subtitle", v)} />
        </>
      )}

      {slide.type === "content" && (
        <>
          <Field label="Encabezado" value={slide.heading as string ?? ""} onChange={v => set("heading", v)} />
          <Field label="Cuerpo" value={slide.body as string ?? ""} onChange={v => set("body", v)} textarea />
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={!!slide.use_image}
              onChange={e => set("use_image", e.target.checked)} />
            Usar imagen
          </label>
          {slide.use_image && (
            <ImageField value={slide.image_path as string ?? ""}
              onPick={() => setShowPicker(true)} />
          )}
        </>
      )}

      {slide.type === "content_icon" && (
        <>
          <Field label="Encabezado" value={slide.heading as string ?? ""} onChange={v => set("heading", v)} />
          <Field label="Cuerpo" value={slide.body as string ?? ""} onChange={v => set("body", v)} textarea />
          <Field label="Ícono (nombre en inglés)" value={slide.icon_hint as string ?? ""} onChange={v => set("icon_hint", v)} />
        </>
      )}

      {slide.type === "stat" && (
        <>
          <Field label="Número (ej: 87%)" value={slide.number as string ?? ""} onChange={v => set("number", v)} />
          <Field label="Etiqueta" value={slide.label as string ?? ""} onChange={v => set("label", v)} />
        </>
      )}

      {slide.type === "cta" && (
        <>
          <Field label="Encabezado" value={slide.heading as string ?? ""} onChange={v => set("heading", v)} />
          <Field label="Acción" value={slide.action as string ?? ""} onChange={v => set("action", v)} />
        </>
      )}

      {showPicker && (
        <ImagePicker
          onSelect={url => set("image_path", url)}
          onClose={() => setShowPicker(false)}
        />
      )}
    </div>
  );
}

function Field({ label, value, onChange, textarea }: {
  label: string; value: string; onChange: (v: string) => void; textarea?: boolean
}) {
  const cls = "w-full border rounded-lg px-3 py-2 text-sm";
  return (
    <div>
      <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
      {textarea
        ? <textarea value={value} onChange={e => onChange(e.target.value)} rows={3} className={cls} />
        : <input value={value} onChange={e => onChange(e.target.value)} className={cls} />}
    </div>
  );
}

function ImageField({ value, onPick }: { value: string; onPick: () => void }) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-600 mb-1">Imagen</label>
      <div className="flex gap-2 items-center">
        {value && <img src={value} alt="" className="w-12 h-12 object-cover rounded" />}
        <button type="button" onClick={onPick}
          className="border px-3 py-1 rounded-lg text-sm hover:bg-gray-50">
          {value ? "Cambiar imagen" : "Elegir imagen"}
        </button>
      </div>
    </div>
  );
}

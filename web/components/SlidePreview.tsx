interface Props { svgUrl: string | null; loading: boolean }

export default function SlidePreview({ svgUrl, loading }: Props) {
  return (
    <div className="aspect-square bg-gray-100 rounded-xl flex items-center justify-center overflow-hidden border">
      {loading ? (
        <div className="text-gray-400 text-sm">Renderizando...</div>
      ) : svgUrl ? (
        <img src={svgUrl} alt="preview" className="w-full h-full object-contain" />
      ) : (
        <div className="text-gray-400 text-sm">Sin preview</div>
      )}
    </div>
  );
}

"use client";
import { useEffect, useState } from "react";
import { api, Company, Design } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function Dashboard() {
  const { user, loading, logout } = useAuth();
  const [companies, setCompanies] = useState<Company[]>([]);
  const [designs, setDesigns] = useState<Design[]>([]);
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.push("/auth/login");
  }, [user, loading, router]);

  useEffect(() => {
    api.companies.list().then(setCompanies);
    api.designs.list().then(setDesigns);
  }, []);

  return (
    <div className="max-w-5xl mx-auto p-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Mis Diseños</h1>
        <div className="flex gap-3 items-center">
          <span className="text-sm text-gray-500">{user?.email}</span>
          <button onClick={logout} className="text-sm text-gray-500 underline">Salir</button>
        </div>
      </div>

      <section className="mb-10">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Empresas</h2>
          <Link href="/companies/new"
            className="bg-black text-white px-4 py-1.5 rounded-lg text-sm">
            + Nueva empresa
          </Link>
        </div>
        {companies.length === 0 ? (
          <p className="text-gray-500">Sin empresas. <Link href="/companies/new" className="underline">Crea una.</Link></p>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {companies.map(c => (
              <Link key={c.id} href={`/companies/${c.id}`}
                className="border rounded-xl p-4 hover:shadow transition">
                <div className="font-medium">{c.name}</div>
                <div className="text-sm text-gray-500 mt-1">{c.style}</div>
                <div className="flex gap-1 mt-2">
                  {Object.values(c.colors ?? {}).map((col, i) => (
                    <div key={i} className="w-4 h-4 rounded-full border"
                      style={{ backgroundColor: col as string }} />
                  ))}
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>

      <section>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Diseños recientes</h2>
          {companies.length > 0 && (
            <Link href="/designs/new/carousel"
              className="bg-black text-white px-4 py-1.5 rounded-lg text-sm">
              + Nuevo carrusel
            </Link>
          )}
        </div>
        {designs.length === 0 ? (
          <p className="text-gray-500">Sin diseños aún.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {designs.map(d => (
              <Link key={d.id} href={`/designs/${d.id}/edit`}
                className="border rounded-xl p-4 hover:shadow transition">
                <div className="font-medium">{d.title ?? "Sin título"}</div>
                <div className="text-sm text-gray-500 mt-1">
                  {d.slides?.length ?? 0} slides · {d.status}
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

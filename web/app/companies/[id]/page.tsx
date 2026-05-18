"use client";
import { useEffect, useState } from "react";
import { api, Company, CompanyCreate } from "@/lib/api";
import CompanyForm from "@/components/CompanyForm";
import { useRouter, useParams } from "next/navigation";

export default function EditCompanyPage() {
  const { id } = useParams<{ id: string }>();
  const [company, setCompany] = useState<Company | null>(null);
  const router = useRouter();

  useEffect(() => { api.companies.get(id).then(setCompany); }, [id]);

  if (!company) return <div className="p-8">Cargando...</div>;

  const handleSubmit = async (data: CompanyCreate) => {
    await api.companies.update(id, data);
    router.push("/dashboard");
  };

  return (
    <div className="max-w-2xl mx-auto p-8">
      <h1 className="text-2xl font-bold mb-6">Editar empresa: {company.name}</h1>
      <CompanyForm initial={company} onSubmit={handleSubmit} submitLabel="Guardar cambios" />
    </div>
  );
}

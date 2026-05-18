"use client";
import { api, CompanyCreate } from "@/lib/api";
import CompanyForm from "@/components/CompanyForm";
import { useRouter } from "next/navigation";

export default function NewCompanyPage() {
  const router = useRouter();
  const handleSubmit = async (data: CompanyCreate) => {
    await api.companies.create(data);
    router.push("/dashboard");
  };
  return (
    <div className="max-w-2xl mx-auto p-8">
      <h1 className="text-2xl font-bold mb-6">Nueva empresa</h1>
      <CompanyForm onSubmit={handleSubmit} submitLabel="Crear empresa" />
    </div>
  );
}

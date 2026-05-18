"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function RegisterPage() {
  const [form, setForm] = useState({ email: "", password: "", name: "" });
  const [error, setError] = useState("");
  const router = useRouter();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await api.auth.register(form);
      await api.auth.login({ email: form.email, password: form.password });
      router.push("/companies/new");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al registrarse");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white p-8 rounded-xl shadow w-full max-w-sm">
        <h1 className="text-2xl font-bold mb-6">Crear cuenta</h1>
        <form onSubmit={submit} className="space-y-4">
          {(["name", "email", "password"] as const).map(field => (
            <input key={field} type={field === "password" ? "password" : field === "email" ? "email" : "text"}
              placeholder={field === "name" ? "Nombre" : field === "email" ? "Email" : "Contraseña"}
              value={form[field]} onChange={e => setForm({ ...form, [field]: e.target.value })}
              className="w-full border rounded-lg px-3 py-2" required />
          ))}
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <button type="submit"
            className="w-full bg-black text-white py-2 rounded-lg hover:bg-gray-800">
            Crear cuenta
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-gray-500">
          ¿Ya tienes cuenta? <Link href="/auth/login" className="underline">Inicia sesión</Link>
        </p>
      </div>
    </div>
  );
}

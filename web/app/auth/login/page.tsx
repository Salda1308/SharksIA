"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await api.auth.login({ email, password });
      router.push("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al iniciar sesión");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white p-8 rounded-xl shadow w-full max-w-sm">
        <h1 className="text-2xl font-bold mb-6">Iniciar sesión</h1>
        <form onSubmit={submit} className="space-y-4">
          <input type="email" placeholder="Email" value={email}
            onChange={e => setEmail(e.target.value)}
            className="w-full border rounded-lg px-3 py-2" required />
          <input type="password" placeholder="Contraseña" value={password}
            onChange={e => setPassword(e.target.value)}
            className="w-full border rounded-lg px-3 py-2" required />
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <button type="submit"
            className="w-full bg-black text-white py-2 rounded-lg hover:bg-gray-800">
            Entrar
          </button>
        </form>
        <a href="http://localhost:8000/api/v1/auth/google"
          className="mt-3 w-full flex items-center justify-center border rounded-lg py-2 hover:bg-gray-50">
          Continuar con Google
        </a>
        <p className="mt-4 text-center text-sm text-gray-500">
          ¿Sin cuenta? <Link href="/auth/register" className="underline">Regístrate</Link>
        </p>
      </div>
    </div>
  );
}

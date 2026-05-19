const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Error desconocido" }));
    throw new Error(err.detail ?? `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  auth: {
    register: (data: { email: string; password: string; name: string }) =>
      apiFetch("/api/v1/auth/register", { method: "POST", body: JSON.stringify(data) }),
    login: (data: { email: string; password: string }) =>
      apiFetch("/api/v1/auth/login", { method: "POST", body: JSON.stringify(data) }),
    logout: () => apiFetch("/api/v1/auth/logout", { method: "POST" }),
    me: () => apiFetch<User>("/api/v1/auth/me"),
  },
  companies: {
    list: () => apiFetch<Company[]>("/api/v1/companies"),
    create: (data: CompanyCreate) =>
      apiFetch<Company>("/api/v1/companies", { method: "POST", body: JSON.stringify(data) }),
    get: (id: string) => apiFetch<Company>(`/api/v1/companies/${id}`),
    update: (id: string, data: CompanyCreate) =>
      apiFetch<Company>(`/api/v1/companies/${id}`, { method: "PUT", body: JSON.stringify(data) }),
    delete: (id: string) =>
      apiFetch(`/api/v1/companies/${id}`, { method: "DELETE" }),
    uploadLogo: (id: string, file: File) => {
      const form = new FormData();
      form.append("file", file);
      return fetch(`${API_BASE}/api/v1/companies/${id}/logo`, {
        method: "POST", credentials: "include", body: form,
      }).then(r => r.json());
    },
  },
  designs: {
    list: () => apiFetch<Design[]>("/api/v1/designs"),
    generate: (data: GenerateRequest) =>
      apiFetch<Design>("/api/v1/designs/carousel/generate", {
        method: "POST", body: JSON.stringify(data),
      }),
    get: (id: string) => apiFetch<Design>(`/api/v1/designs/${id}`),
    updateSlides: (id: string, slides: Slide[]) =>
      apiFetch<Design>(`/api/v1/designs/${id}/slides`, {
        method: "PUT", body: JSON.stringify({ slides }),
      }),
    render: (id: string) =>
      apiFetch<Design>(`/api/v1/designs/${id}/render`, { method: "POST" }),
    exportUrl: (id: string, fmt: "svg" | "pdf" | "jpg") =>
      `${API_BASE}/api/v1/designs/${id}/export?fmt=${fmt}`,
    delete: (id: string) =>
      apiFetch(`/api/v1/designs/${id}`, { method: "DELETE" }),
  },
  images: {
    search: (q: string, source: "pexels" | "pixabay") =>
      apiFetch<ImageResult[]>(`/api/v1/images/search?q=${encodeURIComponent(q)}&source=${source}`),
    upload: (file: File) => {
      const form = new FormData();
      form.append("file", file);
      return fetch(`${API_BASE}/api/v1/assets/upload`, {
        method: "POST", credentials: "include", body: form,
      }).then(r => r.json());
    },
  },
};

// Types
export interface User { id: string; email: string; name?: string; avatar_url?: string; plan: string }
export interface Company {
  id: string; name: string; slug?: string; style: string;
  colors?: Record<string, string>; fonts?: Record<string, string>;
  design_context?: string; ai_provider: string; logo_path?: string;
}
export interface CompanyCreate {
  name: string; style: string; colors?: Record<string, string>;
  fonts?: Record<string, string>; design_context?: string; ai_provider?: string;
}
export interface Slide { type: string; [key: string]: unknown }
export interface Design {
  id: string; company_id: string; type: string; title?: string;
  slides?: Slide[]; size_px?: { width: number; height: number };
  status: string; created_at: string;
}
export interface GenerateRequest {
  company_id: string; mode: "topic" | "text"; content: string;
  size_px?: { width: number; height: number }; title?: string;
}
export interface ImageResult { id: string; url: string; thumb: string; author: string; alt: string }

"use client";
import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { api, User } from "./api";
import { useRouter } from "next/navigation";

interface AuthCtx { user: User | null; loading: boolean; logout: () => Promise<void> }
const AuthContext = createContext<AuthCtx>({ user: null, loading: true, logout: async () => {} });

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    api.auth.me().then(setUser).catch(() => setUser(null)).finally(() => setLoading(false));
  }, []);

  const logout = async () => {
    await api.auth.logout();
    setUser(null);
    router.push("/auth/login");
  };

  return <AuthContext.Provider value={{ user, loading, logout }}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);

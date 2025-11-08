/** @jsxImportSource https://esm.sh/react@18.2.0 */
import React, { useState } from "https://esm.sh/react@18.2.0";
import { useLogin } from "../hooks/useAuth.ts";

export interface LoginFormProps {
  onLogin: () => void;
}

export function LoginForm({ onLogin }: LoginFormProps) {
  const [password, setPassword] = useState("");
  const loginMutation = useLogin(onLogin);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loginMutation.mutate(password);
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "#f9fafb",
      }}
    >
      <div style={{ maxWidth: "28rem", width: "100%" }}>
        <h2
          style={{
            marginTop: "1.5rem",
            marginBottom: "2rem",
            textAlign: "center",
            fontSize: "1.875rem",
            fontWeight: "800",
          }}
        >
          Sign in to FlipDot Control
        </h2>
        <form
          style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}
          onSubmit={handleSubmit}
        >
          <div>
            <label htmlFor="password" style={{ display: "none" }}>
              Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              required
              style={{
                appearance: "none",
                borderRadius: "0.375rem",
                width: "100%",
                padding: "0.5rem 0.75rem",
                border: "1px solid #d1d5db",
                fontSize: "0.875rem",
              }}
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          {loginMutation.error && (
            <div
              style={{
                color: "#dc2626",
                fontSize: "0.875rem",
                textAlign: "center",
              }}
            >
              {loginMutation.error.message}
            </div>
          )}
          <div>
            <button
              type="submit"
              disabled={loginMutation.isPending}
              style={{
                width: "100%",
                display: "flex",
                justifyContent: "center",
                padding: "0.5rem 1rem",
                border: "none",
                borderRadius: "0.375rem",
                fontSize: "0.875rem",
                fontWeight: "500",
                color: "white",
                backgroundColor: "#4f46e5",
                cursor: loginMutation.isPending ? "not-allowed" : "pointer",
                opacity: loginMutation.isPending ? 0.5 : 1,
              }}
            >
              {loginMutation.isPending ? "Signing in..." : "Sign in"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

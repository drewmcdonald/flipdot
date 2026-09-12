import { useState } from "react";
import { useAuthActions } from "@convex-dev/auth/react";
import { isRateLimitError } from "@convex-dev/rate-limiter";

export function SignIn() {
  const { signIn } = useAuthActions();
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await signIn("control-password", { password });
      setPassword("");
    } catch (err) {
      setError(isRateLimitError(err) ? "Too many attempts, try again later" : "Wrong password");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="panel">
      <h2>Sign In</h2>
      <form className="form-row" onSubmit={handleSubmit}>
        <input
          type="password"
          className="input-text"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          autoFocus
        />
        <button type="submit" className="btn-sm btn-primary" disabled={submitting || !password}>
          {submitting ? "..." : "Unlock"}
        </button>
      </form>
      {error && <div className="label" style={{ color: "#ff6b6b" }}>{error}</div>}
    </div>
  );
}

import { useState } from "react";
import { login, register } from "@/api/authApi";
import { setAuthToken } from "@/storage/chromeStorage";
import { isValidEmail, isValidPassword } from "@/utils/validation";
import { ApiError } from "@/api/apiClient";

export function AuthForm({ onAuthenticated }: { onAuthenticated: () => void }) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!isValidEmail(email)) {
      setError("Enter a valid email.");
      return;
    }
    if (!isValidPassword(password)) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (mode === "register" && name.trim().length === 0) {
      setError("Enter your name.");
      return;
    }

    setSubmitting(true);
    try {
      const result =
        mode === "login" ? await login(email, password) : await register(email, password, name);
      await setAuthToken(result.access_token);
      onAuthenticated();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="spendly-auth-form" onSubmit={handleSubmit}>
      <h2>{mode === "login" ? "Log in" : "Create an account"}</h2>

      {mode === "register" && (
        <input
          type="text"
          placeholder="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      )}
      <input
        type="email"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />
      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />

      {error && <p className="spendly-error">{error}</p>}

      <button type="submit" disabled={submitting}>
        {submitting ? "Please wait…" : mode === "login" ? "Log in" : "Sign up"}
      </button>

      <button
        type="button"
        className="spendly-link-button"
        onClick={() => {
          setMode(mode === "login" ? "register" : "login");
          setError(null);
        }}
      >
        {mode === "login" ? "Need an account? Sign up" : "Already have an account? Log in"}
      </button>
    </form>
  );
}

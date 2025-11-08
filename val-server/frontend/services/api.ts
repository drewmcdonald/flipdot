/**
 * API client for FlipDot frontend
 */

// Auth API
export const authApi = {
  login: async (password: string) => {
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || "Invalid password");
    }

    return response.json();
  },

  logout: async () => {
    const response = await fetch("/api/auth/logout", {
      method: "POST",
    });

    if (!response.ok) {
      throw new Error("Logout failed");
    }

    return response.json();
  },

  checkAuth: async () => {
    const response = await fetch("/api/auth/check");

    if (!response.ok) {
      return false;
    }

    const data = await response.json();
    return data.authenticated;
  },
};

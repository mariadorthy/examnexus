const API_URL =
  `${import.meta.env.VITE_API_BASE_URL}/api/auth`;
  
export async function login(
  email,
  password,
  role
) {
  const response = await fetch(
    `${API_URL}/login`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email,
        password,
        role,
      }),
    }
  );
  const raw = await response.text();
  let result = {};
  if (raw) {
    try { result = JSON.parse(raw); }
    catch { result = { message: raw.slice(0, 300) }; }
  }

  if (response.status === 401) {
    localStorage.removeItem("examnexus_token");
    localStorage.removeItem("examnexus_user");
  }

  if (!response.ok) {
    throw new Error(
      result.message || "Login failed."
    );
  }

  return result;
}
export async function verifyToken(token) {
  const response = await fetch(
    `${API_URL}/verify`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  const raw = await response.text();
  let result = {};
  if (raw) {
    try { result = JSON.parse(raw); }
    catch { result = { message: raw.slice(0, 300) }; }
  }

  if (response.status === 401) {
    localStorage.removeItem("examnexus_token");
    localStorage.removeItem("examnexus_user");
    window.dispatchEvent(
      new Event("examnexus:unauthorized")
    );
  }

  if (!response.ok) {
    throw new Error(
      result.message || "Authentication failed."
    );
  }

  return result;
}

export function logout() {
  localStorage.removeItem("examnexus_token");
  localStorage.removeItem("examnexus_user");
}


export function getToken() {
  return localStorage.getItem(
    "examnexus_token"
  );
}


export function getStoredUser() {
  const user = localStorage.getItem(
    "examnexus_user"
  );

  if (!user) {
    return null;
  }

  try {
    return JSON.parse(user);
  } catch {
    return null;
  }
}

export async function logout() {
    const token = localStorage.getItem("token");

    const response = await fetch("http://localhost:8000/auth/logout", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ...(token ? { "Authorization": `Bearer ${token}` } : {})
        },
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.message || data.detail || "Errore nella connessione al server");
    }

    localStorage.removeItem("token");
    return data;
}
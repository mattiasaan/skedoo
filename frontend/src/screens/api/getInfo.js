export async function getInfo() {
    const token = localStorage.getItem("token");

    const response = await fetch("http://localhost:8000/auth/me", {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            ...(token ? { "Authorization": `Bearer ${token}` } : {})
        },
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.message || data.detail || "Errore nella connessione al server");
    }

    return data;
}
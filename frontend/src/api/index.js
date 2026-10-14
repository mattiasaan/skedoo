// Una funzione per ogni endpoint del backend. Se il backend cambia, si cambia solo questo file.
import { request } from "./client";
export { fetchChanges } from "./changes";

const query = (params) => {
  const clean = Object.entries(params).filter(([, v]) => v !== undefined && v !== null);
  return clean.length ? "?" + new URLSearchParams(clean).toString() : "";
};

export const login = (username, password) => request("/auth/login", { method: "POST", body: { username, password }, auth: false });
export const logout = () => request("/auth/logout", { method: "POST" });

export const fetchClasses = () => request("/schedules/classes");
export const fetchSchedule = (classId) => request(`/schedules/${encodeURIComponent(classId)}`);
export const fetchGrades = (periodo) => request("/grades" + query({ periodo }));
export const fetchAgenda = (da, a) => request("/agenda" + query({ da, a }));

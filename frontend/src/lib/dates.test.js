import { describe, expect, it } from "vitest";
import { fromISO, startOfWeek, toISO, weekDays } from "./dates";

describe("date", () => {
  it("converte avanti e indietro", () => {
    expect(toISO(fromISO("2026-10-09"))).toBe("2026-10-09");
  });
  it("il lunedì della settimana", () => {
    expect(toISO(startOfWeek(fromISO("2026-10-09")))).toBe("2026-10-05"); // venerdì
    expect(toISO(startOfWeek(fromISO("2026-10-05")))).toBe("2026-10-05"); // lunedì
  });
  it("la domenica mostra la settimana dopo", () => {
    expect(toISO(startOfWeek(fromISO("2026-10-11")))).toBe("2026-10-12");
  });
  it("weekDays dà lunedì-sabato", () => {
    const days = weekDays(0, fromISO("2026-10-09"));
    expect(days.map((d) => d.key)).toEqual(["lunedi", "martedi", "mercoledi", "giovedi", "venerdi", "sabato"]);
    expect(toISO(days[5].date)).toBe("2026-10-10");
  });
});

import { describe, expect, it } from "vitest";
import { ceilToQuarter, formatSchoolGrade, votoNecessario, weightedAverage } from "./gradeMath";

const g = (valore, peso = 1, extra = {}) => ({ valore, peso, annullato: false, ...extra });

describe("weightedAverage", () => {
  it("fa la media pesata", () => {
    expect(weightedAverage([g(6), g(8, 2)])).toBeCloseTo(7.33, 2);
  });
  it("ignora annullati, peso 0 e giudizi senza valore", () => {
    expect(weightedAverage([g(6), g(2, 1, { annullato: true }), g(10, 0), g(null)])).toBe(6);
  });
  it("senza voti è null", () => {
    expect(weightedAverage([])).toBeNull();
  });
});

describe("votoNecessario", () => {
  it("calcola il voto per arrivare a 6", () => {
    // 5 e 5 -> media 5; per avere 6 con un terzo voto serve 8
    expect(votoNecessario([g(5), g(5)], 6)).toEqual({ stato: "serve", voto: 8 });
  });
  it("tiene conto del peso della verifica", () => {
    // 5 e 5, prossima verifica vale doppio: (6*4 - 10) / 2 = 7
    expect(votoNecessario([g(5), g(5)], 6, 2)).toEqual({ stato: "serve", voto: 7 });
  });
  it("dice quando si è già a posto", () => {
    expect(votoNecessario([g(9), g(9)], 6).stato).toBe("gia_ok");
  });
  it("dice quando non basta nemmeno un 10", () => {
    const r = votoNecessario([g(2), g(2), g(2)], 6);
    expect(r.stato).toBe("irraggiungibile");
    expect(r.mediaConDieci).toBeCloseTo(4, 5);
  });
  it("senza voti il voto necessario è l'obiettivo", () => {
    expect(votoNecessario([], 6)).toEqual({ stato: "serve", voto: 6 });
  });
});

describe("formattazione", () => {
  it("scrive i voti come a scuola", () => {
    expect([6, 6.25, 6.5, 6.75, 7].map(formatSchoolGrade)).toEqual(["6", "6+", "6½", "7-", "7"]);
  });
  it("arrotonda per eccesso al quarto", () => {
    expect(ceilToQuarter(6.13)).toBe(6.25);
    expect(ceilToQuarter(6)).toBe(6);
  });
});

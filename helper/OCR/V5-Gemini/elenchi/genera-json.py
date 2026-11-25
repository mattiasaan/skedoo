import json

aule = []

lettere = ["A", "B", "D"]

for lettera in lettere:
  for piano in [0, 1, 2, 3]:
    for numero in range(1, 16):
      aula = f"AULA {lettera}{piano}{numero:02d}"
      aule.append(aula)


with open("aule.json", "w", encoding="utf-8") as file:
  json.dump(aule, file, indent=2, ensure_ascii=False)

print(f"Generate {len(aule)} aule!")
import asyncio
import os
from dotenv import load_dotenv
from classeviva import Utente


load_dotenv()

USERNAME = os.getenv("CLASSEVIVA_USER")
PASSWORD = os.getenv("CLASSEVIVA_PASS")

async def main():
  utente = Utente(USERNAME, PASSWORD)

  await utente.accedi()

  #assenze = await utente.assenze_da("2026-01-01")

  agenda = await utente.agenda_da_a("2026-03-01", "2026-03-10")

  if agenda:
    for i in agenda:
      print(i)
      print("------------------------------------------------------------")
  else:
    print("Nessun evento trovato")


asyncio.run(main())
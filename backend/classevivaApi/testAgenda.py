import os
import asyncio
from dotenv import load_dotenv
from classeviva import Utente
from lessonsApi import lezioni_per_data
from agendaApi import agenda_per_data

load_dotenv()
USERNAME = os.getenv("CLASSEVIVA_USER")
PASSWORD = os.getenv("CLASSEVIVA_PASS")

async def main():

  utente = Utente(USERNAME, PASSWORD)
  await utente.accedi()

  data = input("Inserisci una data (YYYY-MM-DD): ").strip()



  eventi = await agenda_per_data(utente, data)
  print(f"\nEventi agenda del {data}:")
  if eventi:
    for e in eventi:
      print(e)
      print("-" * 60)
  else:
    print("Nessun evento trovato.")

if __name__ == "__main__":
  asyncio.run(main())
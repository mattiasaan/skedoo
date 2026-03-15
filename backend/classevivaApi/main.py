import asyncio
import os
from dotenv import load_dotenv
from classeviva import Utente
from lessonsApi import lezione_attuale, lezioni_giornata
from agendaApi import agenda_giornata, agenda_settimanale, agenda_mensile

load_dotenv()

USERNAME = os.getenv("CLASSEVIVA_USER")
PASSWORD = os.getenv("CLASSEVIVA_PASS")

async def main():
    utente = Utente(USERNAME, PASSWORD)

    await utente.accedi()

    print("Lezione attuale:", await lezione_attuale(utente))
    print("Lezioni della giornata:", await lezioni_giornata(utente))

"""
    # Agenda
    print("Agenda della giornata:", await agenda_giornata(utente))
    print("Agenda settimanale:", await agenda_settimanale(utente))
    print("Agenda mensile:", await agenda_mensile(utente))
"""
if __name__ == "__main__":
    asyncio.run(main())
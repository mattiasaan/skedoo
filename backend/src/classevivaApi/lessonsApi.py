from datetime import datetime
from classeviva import eccezioni

async def lezione_attuale(cv_client):
  """
  Restituisce la lezione in corso al momento
  """
  oggi = datetime.now().strftime("%Y-%m-%d")
  ora_corrente = datetime.now().time()

  try:
    lezioni = await cv_client.lezioni_giorno(oggi)
    for lezione in lezioni:
      inizio = datetime.strptime(lezione['startTime'], "%H:%M").time()
      fine = datetime.strptime(lezione['endTime'], "%H:%M").time()
      if inizio <= ora_corrente <= fine:
        return lezione
    return None
  except (eccezioni.FormatoNonValido, eccezioni.DataFuoriGamma, eccezioni.ErroreHTTP):
    return None

async def lezioni_giornata(cv_client, giorno=None):
  """
  Restituisce tutte le lezioni giornata
  """
  giorno = giorno or datetime.now().strftime("%Y-%m-%d")
  try:
    return await cv_client.lezioni_giorno(giorno)
  except (eccezioni.FormatoNonValido, eccezioni.DataFuoriGamma, eccezioni.ErroreHTTP):
    return []

async def lezioni_per_data(cv_client, data: str):
  """
  Restituisce tutte le lezioni di una data specifica
  
  Parametri:
    data (str): Data YYYY-MM-DD
  
  Ritorno:
    list[dict]: Lista delle lezioni del giorno richiesto
  """
  try:
    return await cv_client.lezioni_giorno(data)
  except (eccezioni.FormatoNonValido, eccezioni.DataFuoriGamma, eccezioni.ErroreHTTP):
    return []
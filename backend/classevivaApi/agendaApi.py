from datetime import datetime, timedelta
from calendar import monthrange
from classeviva import eccezioni

async def agenda_giornata(cv_client, giorno=None):
  """
  return eventi agenda di un giorno specifico.
  """
  giorno = giorno or datetime.now().strftime("%Y-%m-%d")
  try:
    return await cv_client.agenda_da_a(giorno, giorno)
  except (eccezioni.FormatoNonValido, eccezioni.DataFuoriGamma, eccezioni.ErroreHTTP404, eccezioni.ErroreHTTP):
    return []

async def agenda_settimanale(cv_client, start_date=None):
  """
  return agenda della settimana a partire da start_date (default: oggi).
  """
  start_date = start_date or datetime.now()
  inizio = start_date.strftime("%Y-%m-%d")
  fine = (start_date + timedelta(days=6)).strftime("%Y-%m-%d")

  try:
    return await cv_client.agenda_da_a(inizio, fine)
  except (eccezioni.FormatoNonValido, eccezioni.DataFuoriGamma, eccezioni.ErroreHTTP404, eccezioni.ErroreHTTP):
    return []

async def agenda_mensile(cv_client, mese=None, anno=None):
  """
  return agenda del mese specificato (default: mese corrente).
  """
  today = datetime.now()
  anno = anno or today.year
  mese = mese or today.month

  inizio = datetime(anno, mese, 1).strftime("%Y-%m-%d")
  ultimo_giorno = monthrange(anno, mese)[1]
  fine = datetime(anno, mese, ultimo_giorno).strftime("%Y-%m-%d")

  try:
    return await cv_client.agenda_da_a(inizio, fine)
  except (eccezioni.FormatoNonValido, eccezioni.DataFuoriGamma, eccezioni.ErroreHTTP404, eccezioni.ErroreHTTP):
    return []
  
async def agenda_per_data(cv_client, data: str):
  """
  Restituisce gli eventi agenda di una data specifica.

  Parametri:
    data (str): Data in formato 'YYYY-MM-DD'.

  Ritorno:
    list[dict]: Lista degli eventi agenda del giorno richiesto.
  """
  try:
    return await cv_client.agenda_da_a(data, data)
  except (eccezioni.FormatoNonValido, eccezioni.DataFuoriGamma, eccezioni.ErroreHTTP404, eccezioni.ErroreHTTP):
    return []
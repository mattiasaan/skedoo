# Documentazione API ClasseViva (Async)

## Agenda

### `await self.agenda_da_a(inizio: str, fine: str)`

Ottieni gli eventi che compongono l’agenda dell’utente.

#### Parametri
- **inizio** (`str`)  
  Data di inizio degli eventi da cui partire, formato `YYYY-MM-DD`.

- **fine** (`str`)  
  Data di fine degli eventi fino a cui restituirli, formato `YYYY-MM-DD`.

#### Ritorno
`list[dict[str, Any]]`  
Eventi dell’agenda nel periodo specificato.

#### Eccezioni
- `classeviva.eccezioni.FormatoNonValido` — formato della data non valido.
- `classeviva.eccezioni.DataFuoriGamma` — data fuori dall’anno scolastico o `fine < inizio`.
- `classeviva.eccezioni.ErroreHTTP404` — errore HTTP 404.
- `classeviva.eccezioni.ErroreHTTP` — altri errori HTTP.

---

### `await self.agenda_codice_da_a(codice: str, inizio: str, fine: str)`

Ottieni gli eventi dell’utente filtrati per **codice evento**.

#### Parametri
- **codice** (`str`)  
  Codice evento per filtrare gli eventi.

- **inizio** (`str`)  
  Data di inizio (`YYYY-MM-DD`).

- **fine** (`str`)  
  Data di fine (`YYYY-MM-DD`).

#### Ritorno
`list[dict[str, Any]]`  
Eventi dell’agenda nel periodo specificato con il codice evento indicato.

#### Eccezioni
- `classeviva.eccezioni.FormatoNonValido`
- `classeviva.eccezioni.DataFuoriGamma`
- `classeviva.eccezioni.ErroreHTTP404`
- `classeviva.eccezioni.ErroreHTTP`

---

### `await self.agenda()`

Ottieni tutti gli eventi dell’agenda nell’anno scolastico corrente.

#### Ritorno
`list[dict[str, Any]]`  
Eventi dell’agenda dell’anno scolastico corrente.

#### Eccezioni
- `classeviva.eccezioni.FormatoNonValido`
- `classeviva.eccezioni.DataFuoriGamma`
- `classeviva.eccezioni.ErroreHTTP404`
- `classeviva.eccezioni.ErroreHTTP`

---

# Didattica

### `await self.didattica()`

Ottieni il materiale nella sezione **didattica** dell’anno scolastico corrente.

#### Ritorno
`list[dict[str, Any]]`  
Materiale didattico disponibile.

#### Eccezioni
- `classeviva.eccezioni.ErroreHTTP`

---

### `await self.didattica_elemento(contenuto: int)`

Ottieni un contenuto specifico dal materiale didattico.

#### Parametri
- **contenuto** (`int`)  
  Codice del contenuto da ottenere.

#### Ritorno
`Any`  
Contenuto richiesto.

#### Avvertenze
L’endpoint restituisce lo stesso contenuto ottenibile con `didattica()`.

#### Eccezioni
- `classeviva.eccezioni.ErroreHTTP`

---

# Bacheca

### `await self.bacheca()`

Ottieni il materiale presente nella **bacheca**.

#### Ritorno
`list[dict[str, str | bool | dict[str, str | int]]]`  
Materiale pubblicato in bacheca.

#### Eccezioni
- `classeviva.eccezioni.ErroreHTTP`

---

### `await self.bacheca_leggi(codice: int, id_: int)`

Ottieni il contenuto di una pubblicazione in bacheca.

#### Parametri
- **codice** (`int`)  
  Codice dell’evento (`evtCode`).

- **id_** (`int`)  
  ID della pubblicazione (`pubId`).

#### Ritorno
`dict[str, dict[str, Any]]`  
Contenuto richiesto.

#### Eccezioni
- `classeviva.eccezioni.ErroreHTTP`

---

### `await self.bacheca_allega(codice: int, id_: int)`

Ottieni un **allegato** della bacheca.

#### Parametri
- **codice** (`int`)  
  Codice dell’evento (`evtCode`).

- **id_** (`int`)  
  ID della pubblicazione (`pubId`).

#### Ritorno
`bytes`  
Contenuto binario dell’allegato.

#### Eccezioni
- `classeviva.eccezioni.ErroreHTTP`

#### Alias
- `bacheca_allegato`

---

# Lezioni

### `await self.lezioni()`

Ottieni tutte le lezioni dell’anno.

#### Avvertenze
L’endpoint restituisce sempre:

```json
{"lessons": []}
```

---

### `await self.lezioni_giorno(giorno: str)`

Ottieni le lezioni di un giorno specifico.

#### Parametri
- **giorno** (`str`)  
  Data nel formato `YYYY-MM-DD`.

#### Ritorno
`list[dict[str, Any]]`  
Lezioni del giorno richiesto.

#### Eccezioni
- `classeviva.eccezioni.FormatoNonValido`
- `classeviva.eccezioni.DataFuoriGamma`
- `classeviva.eccezioni.ErroreHTTP`

---

### `await self.lezioni_da_a(inizio: str, fine: str)`

Ottieni le lezioni in un **range di date**.

#### Parametri
- **inizio** (`str`) — data di inizio (`YYYY-MM-DD`)
- **fine** (`str`) — data di fine (`YYYY-MM-DD`)

#### Ritorno
`list[dict[str, Any]]`  
Lezioni nel range richiesto.

#### Eccezioni
- `classeviva.eccezioni.FormatoNonValido`
- `classeviva.eccezioni.DataFuoriGamma`
- `classeviva.eccezioni.ErroreHTTP`

---

### `await self.lezioni_da_a_materia(inizio: str, fine: str, materia: str)`

Ottieni le lezioni in un range di date filtrate per **materia**.

#### Parametri
- **inizio** (`str`) — data di inizio (`YYYY-MM-DD`)
- **fine** (`str`) — data di fine (`YYYY-MM-DD`)
- **materia** (`str`) — codice della materia (`subjectId`)

#### Ritorno
`list[dict[str, Any]]`  
Lezioni della materia richiesta.

#### Eccezioni
- `classeviva.eccezioni.FormatoNonValido`
- `classeviva.eccezioni.DataFuoriGamma`
- `classeviva.eccezioni.ErroreHTTP`

---

# Calendario

### `await self.calendario()`

Ottieni il calendario scolastico.

#### Ritorno
`list[dict[str, str | int]]`  
Calendario.

#### Eccezioni
- `classeviva.eccezioni.ErroreHTTP`

---

### `await self.calendario_da_a(inizio: str, fine: str)`

Ottieni il calendario in un intervallo di date.

#### Parametri
- **inizio** (`str`) — data di inizio (`YYYY-MM-DD`)
- **fine** (`str`) — data di fine (`YYYY-MM-DD`)

#### Ritorno
`list[dict[str, str | int]]`  
Calendario nel range richiesto.

#### Eccezioni
- `classeviva.eccezioni.FormatoNonValido`
- `classeviva.eccezioni.DataFuoriGamma`
- `classeviva.eccezioni.ErroreHTTP`
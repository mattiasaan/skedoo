from fastapi import APIRouter, Depends, Path
from pydantic import BaseModel

from .classeviva import CvSession
from .security import current_session, upstream_limit

router = APIRouter(prefix="/bacheca", tags=["Bacheca"], dependencies=[Depends(upstream_limit)])


class AttachmentOut(BaseModel):
  nome: str
  numero: int


class BoardItemOut(BaseModel):
  id: int | str | None
  codice: str | None = None
  titolo: str | None = None
  categoria: str | None = None
  pubblicato_il: str | None = None
  valido_da: str | None = None
  valido_a: str | None = None
  letto: bool = False
  allegati: list[AttachmentOut] = []


class BoardOut(BaseModel):
  elementi: list[BoardItemOut]


class BoardDetailOut(BaseModel):
  titolo: str | None = None
  testo: str | None = None
  risposta: dict | None = None


def _items(raw) -> list[dict]:
  if isinstance(raw, dict):
    return raw.get("items", [])
  return raw or []


def build_board(raw) -> BoardOut:
  return BoardOut(elementi=[BoardItemOut(
    id=item.get("pubId"),
    codice=item.get("evtCode"),
    titolo=item.get("cntTitle") or item.get("title"),
    categoria=item.get("cntCategory"),
    pubblicato_il=item.get("pubDT"),
    valido_da=item.get("cntValidFrom"),
    valido_a=item.get("cntValidTo"),
    letto=bool(item.get("readStatus")),
    allegati=[AttachmentOut(nome=a.get("fileName") or "", numero=a.get("attachNum") or 1)
              for a in item.get("attachments", []) or []],
  ) for item in _items(raw)])


@router.get("", response_model=BoardOut)
async def get_board(session: CvSession = Depends(current_session)):
  return build_board(await session.call("bacheca"))


@router.get("/{codice}/{id}", response_model=BoardDetailOut)
async def get_board_item(
  codice: str = Path(pattern=r"^[A-Za-z0-9_-]{1,16}$"),
  id: int = Path(ge=1),
  session: CvSession = Depends(current_session),
):
  raw = await session.call("bacheca_leggi", codice, id)
  item = raw.get("item", raw) if isinstance(raw, dict) else {}
  return BoardDetailOut(titolo=item.get("title"), testo=item.get("text"),
                        risposta=raw.get("reply") if isinstance(raw, dict) else None)

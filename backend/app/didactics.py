from fastapi import APIRouter, Depends
from pydantic import BaseModel

from .classeviva import CvSession
from .security import current_session, upstream_limit

router = APIRouter(prefix="/didattica", tags=["Didattica"], dependencies=[Depends(upstream_limit)])


class MaterialOut(BaseModel):
  id: int | str | None
  nome: str
  tipo: str | None = None
  oggetto_id: int | str | None = None
  condiviso_il: str | None = None


class FolderOut(BaseModel):
  id: int | str | None
  nome: str
  ultimo_condiviso_il: str | None = None
  materiali: list[MaterialOut]


class TeacherOut(BaseModel):
  id: int | str | None
  nome: str | None = None
  cartelle: list[FolderOut]


class DidacticsOut(BaseModel):
  docenti: list[TeacherOut]


def build_didactics(raw) -> DidacticsOut:
  teachers = raw.get("didacticts", []) if isinstance(raw, dict) else raw
  result = []
  for teacher in teachers or []:
    folders = []
    for folder in teacher.get("folders", []) or []:
      folders.append(FolderOut(
        id=folder.get("folderId"), nome=folder.get("folderName") or "",
        ultimo_condiviso_il=folder.get("lastShareDT"),
        materiali=[MaterialOut(
          id=item.get("contentId"), nome=item.get("contentName") or "",
          tipo=item.get("objectType"), oggetto_id=item.get("objectId"),
          condiviso_il=item.get("shareDT"),
        ) for item in folder.get("contents", []) or []],
      ))
    result.append(TeacherOut(
      id=teacher.get("teacherId"),
      nome=teacher.get("teacherName"),
      cartelle=folders,
    ))
  return DidacticsOut(docenti=result)


@router.get("", response_model=DidacticsOut)
async def get_didactics(session: CvSession = Depends(current_session)):
  return build_didactics(await session.call("didattica"))

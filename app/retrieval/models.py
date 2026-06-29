from pydantic import BaseModel


class Citation(BaseModel):
    document_id: str
    chunk_id: str
    title: str
    source: str
    score: float


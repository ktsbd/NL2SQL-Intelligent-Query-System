from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.services.csv_dataset_importer import CSVDatasetImporter

router = APIRouter(prefix="/datasets", tags=["datasets"])


class ImportedColumn(BaseModel):
    original_name: str
    sql_name: str
    mysql_type: str


class DatasetUploadResponse(BaseModel):
    table_name: str
    dataset_name: str
    columns: list[ImportedColumn]
    rows_inserted: int
    indexed: int


@router.post("/upload", response_model=DatasetUploadResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    dataset_name: str | None = Form(default=None),
) -> dict[str, object]:
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="目前仅支持 CSV 文件。")
    try:
        content = await file.read()
        return CSVDatasetImporter().import_csv(content, file.filename, dataset_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

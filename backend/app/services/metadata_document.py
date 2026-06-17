from dataclasses import dataclass

from app.db.models import MetadataCatalog


@dataclass(frozen=True)
class MetadataDocument:
    id: int
    object_type: str
    object_name: str
    parent_name: str | None
    business_name: str
    description: str
    synonyms: str
    example_values: str

    @property
    def text(self) -> str:
        parts = [
            self.object_type,
            self.object_name,
            self.parent_name or "",
            self.business_name,
            self.description,
            self.synonyms,
            self.example_values,
        ]
        return "\n".join(part for part in parts if part)

    def payload(self) -> dict[str, object]:
        return {
            "id": self.id,
            "object_type": self.object_type,
            "object_name": self.object_name,
            "parent_name": self.parent_name,
            "business_name": self.business_name,
            "description": self.description,
            "synonyms": self.synonyms,
            "example_values": self.example_values,
            "text": self.text,
        }


def from_model(row: MetadataCatalog) -> MetadataDocument:
    return MetadataDocument(
        id=row.id,
        object_type=row.object_type,
        object_name=row.object_name,
        parent_name=row.parent_name,
        business_name=row.business_name,
        description=row.description,
        synonyms=row.synonyms,
        example_values=row.example_values,
    )


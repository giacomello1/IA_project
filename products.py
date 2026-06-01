from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class Product:
    name: str
    calories: int
    fats: float
    salts: float
    sugars: float
    proteins: float
    carbohydrates: float
    id: Optional[int] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'Product':
        """
        Factory method to create a Product object from a database dictionary.
        """
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            calories=data.get("calories"),
            fats=float(data.get("fats", 0)),
            salts=float(data.get("salts", 0)),
            sugars=float(data.get("sugars", 0)),
            proteins=float(data.get("proteins", 0)),
            carbohydrates=float(data.get("carbohydrates", 0))
        )

    def to_dict(self, include_id: bool = False) -> dict:
        """
        Converts the Product object into a dictionary for database operations.
        """
        data_dict = asdict(self)
        if not include_id or self.id is None:
            data_dict.pop("id", None)
        return data_dict

    def __str__(self) -> str:
        return f"Product [{self.id or 'New'}]: {self.name} ({self.calories} kcal)"

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
    quantity: int = 0  # ALLINEATO AL DB: Quantità disponibile in magazzino
    id: Optional[int] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'Product':
        """
        Factory method per creare un oggetto Product partendo da un dizionario di Supabase.
        Garantisce il corretto casting dei tipi numerici dal DB.
        """
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            calories=data.get("calories", 0),
            fats=float(data.get("fats", 0.0)),
            salts=float(data.get("salts", 0.0)),
            sugars=float(data.get("sugars", 0.0)),
            proteins=float(data.get("proteins", 0.0)),
            carbohydrates=float(data.get("carbohydrates", 0.0)),
            quantity=data.get("quantity", 0)  # Mappatura del nuovo campo quantità
        )

    def to_dict(self, include_id: bool = False) -> dict:
        """
        Converte l'oggetto Product in un dizionario Python standard per le operazioni CRUD.
        """
        data_dict = asdict(self)
        if not include_id or self.id is None:
            data_dict.pop("id", None)
        return data_dict

    def __str__(self) -> str:
        return f"Product [{self.id or 'New'}]: {self.name} ({self.calories} kcal) | Disp: {self.quantity}"

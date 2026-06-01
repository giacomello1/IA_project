from dataclasses import dataclass, asdict

@dataclass
class Beneficiary:
    id: int
    name: str
    type: str  # 'Mensa', 'Ospedale', 'Famiglia', 'Case Famiglia'

    @staticmethod
    def from_dict(data: dict) -> 'Beneficiary':
        """Crea un'istanza partendo dal dizionario di Supabase."""
        return Beneficiary(
            id=data.get('id'),
            name=data.get('name'),
            type=data.get('type')
        )

    def to_dict(self) -> dict:
        return asdict(self)

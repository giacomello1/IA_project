from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class Person:
    id: int
    first_name: str
    last_name: str
    age: int
    gender: str
    caloric_requirement: int
    classification: str  # es. 'Bambino', 'Anziano', 'Adulto'
    tax_code: str       # Codice Fiscale (Unique nel DB)
    beneficiary_id: Optional[int] = None  # Chiave esterna verso la tabella Beneficiaries
    priority: Optional[float] = None      # Campo calcolato dinamicamente a runtime
    beneficiary_type: Optional[str] = None # Popolato dopo la JOIN per il calcolo delle priorità

    @property
    def full_name(self) -> str:
        """
        Restituisce il nome completo.
        Molto comodo per mantenere la compatibilità con le tabelle di output nel main.py.
        """
        return f"{self.first_name} {self.last_name}"

    @staticmethod
    def from_dict(data: dict) -> 'Person':
        """
        Metodo factory per creare un'istanza di Person partendo da un dizionario.
        Mappa accuratamente i nuovi campi del database Supabase.
        """
        # Gestione della JOIN con la tabella Beneficiaries per estrarre il 'type'
        beneficiary_type = data.get('beneficiary_type')
        if 'Beneficiaries' in data and isinstance(data['Beneficiaries'], dict):
            beneficiary_type = data['Beneficiaries'].get('type')

        return Person(
            id=data.get('id'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            age=data.get('age'),
            gender=data.get('gender'),
            caloric_requirement=data.get('caloric_requirement'),
            classification=data.get('classification'),
            tax_code=data.get('tax_code'),
            beneficiary_id=data.get('beneficiary_id'),
            beneficiary_type=beneficiary_type,
            priority=data.get('priority')
        )

    def to_dict(self) -> dict:
        """
        Converte l'istanza di Person in un dizionario Python standard.
        """
        return asdict(self)

import os
from dotenv import load_dotenv
from supabase import create_client, Client

from people import Person
from beneficiaries import Beneficiary
from priorities import calculate_people_priorities, calculate_beneficiary_priorities

load_dotenv()

def get_supabase_client() -> Client:
    """Inizializza e restituisce il client di Supabase usando le variabili d'ambiente."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("Errore: SUPABASE_URL o SUPABASE_KEY non trovate nel file .env")
    return create_client(url, key)

def main():
    try:
        supabase = get_supabase_client()

        # 1. Recupero Dati da Supabase
        # Selezioniamo esplicitamente solo i 3 campi richiesti per i Beneficiaries
        ben_response = supabase.table("Beneficiaries").select("id, name, type").execute()
        beneficiary_objects = [Beneficiary.from_dict(b) for b in ben_response.data]

        # Selezioniamo tutti i nuovi campi di People con la JOIN sul tipo di Beneficiario
        people_response = supabase.table("People").select("*, Beneficiaries(type)").execute()
        people_objects = [Person.from_dict(p) for p in people_response.data]

        # 2. Elaborazione Priorità tramite Algoritmo AI
        final_people = calculate_people_priorities(people_objects)
        # Otteniamo la mappa esterna {id_beneficiario: priorità}
        ben_priorities_map = calculate_beneficiary_priorities(beneficiary_objects, final_people)

        # 3. OUTPUT FORMATTATO RICHIESTO

        print("\n" + "=" * 50)
        print("TABELLA BENEFICIARI")
        print("=" * 50)
        # Ordiniamo l'output in base ai valori contenuti nella mappa delle priorità (decrescente)
        sorted_beneficiaries = sorted(beneficiary_objects, key=lambda b: ben_priorities_map.get(b.id, 0.0), reverse=True)
        for ben in sorted_beneficiaries:
            priority = ben_priorities_map.get(ben.id, 0.0)
            print(f"beneficiari: {ben.name} - priorità: {priority}")
        print("=" * 50)

        print("\n" + "=" * 50)
        print("TABELLA PERSONE")
        print("=" * 50)
        # Ordiniamo le persone in base alla priorità calcolata (decrescente)
        sorted_people = sorted(final_people, key=lambda p: p.priority if p.priority is not None else 0.0, reverse=True)
        for person in sorted_people:
            # Utilizziamo .full_name che unisce dinamicamente first_name e last_name del nuovo modello
            print(f"persona : {person.full_name} - priorità: {person.priority}")
        print("=" * 50)

    except Exception as e:
        print(f"Errore durante l'esecuzione: {e}")

if __name__ == "__main__":
    main()

# main.py
import os
from dotenv import load_dotenv
from supabase import create_client, Client

from people import Person
from beneficiaries import Beneficiary
from products import Product
from priorities import calculate_people_priorities, calculate_beneficiary_priorities
from genetic_algorithm import run_genetic_algorithm, plot_convergence

from exports import (
    apply_greedy_cleanup,
    plot_distribution_analytics,
    plot_people_satisfaction_analytics,
    export_distribution_data,
    export_individual_satisfaction_table,
    export_warehouse_remnants
)

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

        # 1. RECUPERO DATI DA SUPABASE (Stato Iniziale del Mondo)
        print("Lettura dati da Supabase in corso...")

        ben_response = supabase.table("Beneficiaries").select("id, name, type").execute()
        beneficiary_objects = [Beneficiary.from_dict(b) for b in ben_response.data]

        people_response = supabase.table("People").select("*, Beneficiaries(type)").execute()
        people_objects = [Person.from_dict(p) for p in people_response.data]

        prod_response = supabase.table("Products").select("*").execute()
        product_objects = [Product.from_dict(p) for p in prod_response.data]

        print(f" -> Scaricati con successo: {len(beneficiary_objects)} Enti, {len(people_objects)} Persone, {len(product_objects)} Tipologie di prodotto.")

        # 2. ELABORAZIONE DELLE PRIORITÀ (Funzione Euristica di Ordinamento)
        final_people = calculate_people_priorities(people_objects)
        ben_priorities_map = calculate_beneficiary_priorities(beneficiary_objects, final_people)

        # 3. OUTPUT TABELLA DELLE PRIORITÀ CALCOLATE
        print("\n" + "=" * 50)
        print("TABELLA PRIORITÀ BENEFICIARI (ORDINATA)")
        print("=" * 50)
        sorted_beneficiaries = sorted(beneficiary_objects, key=lambda b: ben_priorities_map.get(b.id, 0.0), reverse=True)
        for ben in sorted_beneficiaries:
            priority = ben_priorities_map.get(ben.id, 0.0)
            print(f"Beneficiario: {ben.name:<25} | Priorità: {priority:.2f}")
        print("=" * 50)

        # 4. CONFIGURAZIONE ED ESECUZIONE ALGORITMO GENETICO (Ottimizzazione Globale)
        GENERATIONS = 100
        POP_SIZE = 1000
        MUTATION_RATE = 0.15

        print(f"\n[AI] Avvio Algoritmo Genetico...")
        print(f"     Parametri -> Generazioni: {GENERATIONS} | Popolazione: {POP_SIZE} | Rate Mutazione: {MUTATION_RATE}")

        best_plan, fitness_history = run_genetic_algorithm(
            beneficiaries=beneficiary_objects,
            people=people_objects,
            products=product_objects,
            ben_priorities_map=ben_priorities_map,
            generations=GENERATIONS,
            pop_size=POP_SIZE,
            mutation_rate=MUTATION_RATE
        )

        # Post-Processing: Ibridazione Memetica (Assegnazione Greedy Scorte Residue)
        best_plan = apply_greedy_cleanup(
            best_plan=best_plan,
            beneficiaries=beneficiary_objects,
            products=product_objects,
            people=people_objects,
            ben_priorities_map=ben_priorities_map
        )

        # 5. RETRIEVAL E PRESENTAZIONE DELLO STATO OBIETTIVO (Report Finale a Terminale)
        print("\n" + "=" * 65)
        print("PIANO DI DISTRIBUZIONE ALIMENTARE OTTIMIZZATO (GA + CLEAN-UP)")
        print("=" * 65)

        product_map = {p.id: p for p in product_objects if p.id is not None}

        for ben in beneficiary_objects:
            print(f"\nEnte: {ben.name} ({ben.type}) | Grado Urgenza: {ben_priorities_map.get(ben.id, 0.0):.2f}")
            print(f"  Ripartizione Cibo Allocata:")

            ben_allocations = best_plan.get(ben.id, {})
            has_allocations = False
            total_cal_allocated = 0

            for prod_id, qty in ben_allocations.items():
                if qty > 0 and prod_id in product_map:
                    prod = product_map[prod_id]
                    print(f"    - {prod.name:<22} : {qty:<4} unità ({qty * prod.calories} kcal)")
                    total_cal_allocated += qty * prod.calories
                    has_allocations = True

            if not has_allocations:
                print("    - Nessun prodotto assegnato (Scorte insufficienti o bassa urgenza)")
            else:
                print(f"  > Totale Energia Fornita all'Ente: {total_cal_allocated} kcal")

        print("\n" + "=" * 65)

        # =====================================================================
        # 6. GENERAZIONE DEI REPORT ANALITICI ED ESPORTAZIONI SUL DISCO
        # =====================================================================
        print("\n" + "=" * 55)
        print("SCRITTURA FILE DI ANALISI E REPORTISTICA NELLE CARTELLE DEDICATE")
        print("=" * 55)

        # Garanzia di creazione della cartella grafici per la funzione esterna del GA
        os.makedirs(os.path.join("risultati", "grafici"), exist_ok=True)

        # Grafico 1: Curva di convergenza fitness del GA (Salvato in risultati/grafici)
        plot_convergence(fitness_history, filename=os.path.join("risultati", "grafici", "ai_convergence_plot.png"))

        # Grafico 2: Grafico a barre comparativo Fabbisogno vs Allocato per Ente (In risultati/grafici)
        plot_distribution_analytics(best_plan, beneficiary_objects, product_objects, people_objects, ben_priorities_map)

        # Grafico 3: Istogramma soddisfazione media delle PERSONE (In risultati/grafici)
        plot_people_satisfaction_analytics(best_plan, beneficiary_objects, product_objects, people_objects)

        # File 4: Report di ripartizione generale (Genera CSV in risultati/csv e JSON in risultati/json)
        export_distribution_data(best_plan, beneficiary_objects, product_objects, people_objects, ben_priorities_map)

        # File 5: Tabella di ogni persona con dati anagrafici e calorie corrette (In risultati/csv)
        export_individual_satisfaction_table(best_plan, beneficiary_objects, product_objects, people_objects, filename="soddisfazione_persone.csv")

        # File 6: Bilancio finale scorte magazzino (In risultati/csv)
        export_warehouse_remnants(best_plan, product_objects, filename="rimanenze_magazzino.csv")

        print("=" * 55)
        print("Esecuzione terminata. La cartella unica 'risultati/' è stata popolata correttamente.")

    except Exception as e:
        print(f"Errore critico durante l'esecuzione del sistema: {e}")

if __name__ == "__main__":
    main()

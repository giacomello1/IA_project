# exports.py
import os
import csv
import json
import matplotlib.pyplot as plt

# Definizione della struttura delle cartelle di output
BASE_DIR = "risultati"
PLOTS_DIR = os.path.join(BASE_DIR, "grafici")
CSV_DIR = os.path.join(BASE_DIR, "csv")
JSON_DIR = os.path.join(BASE_DIR, "json")

def apply_greedy_cleanup(best_plan, beneficiaries, products, people, ben_priorities_map):
    """
    Fase di Post-Processing (Approccio Memetico) con HARD CONSTRAINT sul surplus:
    Prende le rimanenze residue del magazzino e le assegna in modo greedy agli enti
    prioritari, MA vieta categoricamente di superare il 100% del fabbisogno calorico.
    """
    print("\n[Post-Processing] Avvio fase di Clean-up Eristico con blocco del surplus...")
    product_map = {p.id: p for p in products if p.id is not None}

    # Calcolo fabbisogno totale per ogni ente
    ben_req_map = {b.id: sum(p.caloric_requirement for p in people if p.beneficiary_id == b.id) for b in beneficiaries}

    # Calcolo calorie attualmente allocate ad ogni ente dal GA
    ben_alloc_cal = {}
    for ben in beneficiaries:
        total_cal = 0
        ben_allocs = best_plan.get(ben.id, {})
        for prod_id, qty in ben_allocs.items():
            if qty > 0 and prod_id in product_map:
                total_cal += qty * product_map[prod_id].calories
        ben_alloc_cal[ben.id] = total_cal

    # Conteggio totale prodotti già distribuiti
    total_allocated_by_prod = {}
    for ben_id, allocations in best_plan.items():
        for prod_id, qty in allocations.items():
            total_allocated_by_prod[prod_id] = total_allocated_by_prod.get(prod_id, 0) + qty

    # Ordina i beneficiari per priorità decrescente
    sorted_bens = sorted(beneficiaries, key=lambda b: ben_priorities_map.get(b.id, 0.0), reverse=True)
    units_distributed = 0

    for prod in products:
        initial_qty = getattr(prod, 'quantity', 0)
        allocated_qty = total_allocated_by_prod.get(prod.id, 0)
        remnant = initial_qty - allocated_qty

        if remnant > 0:
            for ben in sorted_bens:
                if remnant <= 0:
                    break

                gap_calorico = ben_req_map.get(ben.id, 0) - ben_alloc_cal.get(ben.id, 0)

                if gap_calorico > 0 and prod.calories > 0:
                    # FIX CRITICO: Divisione intera pura senza arrotondamento per eccesso (no max(1, ...))
                    units_needed = int(gap_calorico // prod.calories)

                    # Se l'unità residua sfora il fabbisogno dell'ente, passiamo all'ente successivo
                    if units_needed == 0:
                        continue

                    qty_to_give = min(remnant, units_needed)

                    if qty_to_give > 0:
                        if ben.id not in best_plan:
                            best_plan[ben.id] = {}

                        best_plan[ben.id][prod.id] = best_plan[ben.id].get(prod.id, 0) + qty_to_give
                        remnant -= qty_to_give
                        ben_alloc_cal[ben.id] += qty_to_give * prod.calories
                        units_distributed += qty_to_give

    print(f" -> Clean-up completato: allocate con successo {units_distributed} unità residue senza alcun surplus.")
    return best_plan


def plot_distribution_analytics(best_plan, beneficiaries, products, people, ben_priorities_map, filename="ai_allocation_analytics.png"):
    """
    Genera un grafico a barre comparativo definitivo: Fabbisogno Reale vs Allocazione Totale per Ente.
    """
    print("Generazione del grafico analitico della distribuzione per ente...")
    os.makedirs(PLOTS_DIR, exist_ok=True)
    filepath = os.path.join(PLOTS_DIR, filename)

    product_map = {p.id: p for p in products if p.id is not None}

    beneficiary_requirements = {b.id: sum(p.caloric_requirement for p in people if p.beneficiary_id == b.id) for b in beneficiaries}
    beneficiary_allocations = {}

    for ben in beneficiaries:
        total_cal = 0
        ben_allocs = best_plan.get(ben.id, {})
        for prod_id, qty in ben_allocs.items():
            if qty > 0 and prod_id in product_map:
                total_cal += qty * product_map[prod_id].calories
        beneficiary_allocations[ben.id] = total_cal

    sorted_bens = sorted(beneficiaries, key=lambda b: ben_priorities_map.get(b.id, 0.0), reverse=True)
    names = [b.name for b in sorted_bens]
    requirements = [beneficiary_requirements.get(b.id, 0) for b in sorted_bens]
    allocated = [beneficiary_allocations.get(b.id, 0) for b in sorted_bens]

    x = range(len(names))
    width = 0.35

    fig, ax = plt.subplots(figsize=(12, 6), dpi=150)
    ax.bar([i - width/2 for i in x], requirements, width, label='Fabbisogno Richiesto (kcal)', color='#e74c3c')
    ax.bar([i + width/2 for i in x], allocated, width, label='Allocato da AI (kcal)', color='#2ecc71')

    ax.set_ylabel('Energia (Calorie - kcal)', fontsize=12)
    ax.set_title('Equità di Distribuzione AI: Fabbisogno Reale vs Allocazione Energetica', fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=25, ha="right", fontsize=10)
    ax.legend(fontsize=11)
    ax.grid(axis='y', linestyle='--', alpha=0.5)

    plt.tight_layout()
    plt.savefig(filepath)
    plt.close()
    print(f" -> Grafico salvato in: {filepath}")


def plot_people_satisfaction_analytics(best_plan, beneficiaries, products, people, filename="people_satisfaction_analytics.png"):
    """
    Genera un grafico che mostra il tasso di soddisfazione energetica delle PERSONE
    raggruppate per categoria di appartenenza (Ospedali, Famiglie, Mense).
    """
    print("Generazione del grafico di soddisfazione calorica delle persone...")
    os.makedirs(PLOTS_DIR, exist_ok=True)
    filepath = os.path.join(PLOTS_DIR, filename)

    product_map = {p.id: p for p in products if p.id is not None}

    ben_req = {b.id: sum(p.caloric_requirement for p in people if p.beneficiary_id == b.id) for b in beneficiaries}
    ben_alloc = {b.id: 0 for b in beneficiaries}

    for ben_id, allocs in best_plan.items():
        for prod_id, qty in allocs.items():
            if qty > 0 and prod_id in product_map:
                ben_alloc[ben_id] = ben_alloc.get(ben_id, 0) + (qty * product_map[prod_id].calories)

    type_satisfaction_data = {}
    ben_type_map = {b.id: b.type for b in beneficiaries}

    for p in people:
        b_type = ben_type_map.get(p.beneficiary_id, "Sconosciuto")
        req = ben_req.get(p.beneficiary_id, 0)
        alloc = ben_alloc.get(p.beneficiary_id, 0)

        sat_percentage = (alloc / req * 100) if req > 0 else 0.0
        if sat_percentage > 100: sat_percentage = 100.0

        if b_type not in type_satisfaction_data:
            type_satisfaction_data[b_type] = []
        type_satisfaction_data[b_type].append(sat_percentage)

    types = list(type_satisfaction_data.keys())
    avg_satisfactions = [sum(l)/len(l) for l in type_satisfaction_data.values() if len(l) > 0]

    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    bars = ax.bar(types, avg_satisfactions, color=['#34495e', '#3498db', '#9b59b6'], width=0.5, edgecolor='black', alpha=0.85)

    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:.1f}%',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=11, fontweight='bold')

    ax.set_ylabel('% Soddisfazione Fabbisogno Personale Medio', fontsize=12)
    ax.set_title('Grado di Soddisfazione Umana per Tipologia di Beneficiario', fontsize=13, fontweight='bold', pad=15)
    ax.set_ylim(0, 110)
    ax.grid(axis='y', linestyle=':', alpha=0.6)

    plt.tight_layout()
    plt.savefig(filepath)
    plt.close()
    print(f" -> Grafico salvato in: {filepath}")


def export_distribution_data(best_plan, beneficiaries, products, people, ben_priorities_map, base_filename="report_distribuzione"):
    """Esporta i risultati dell'ottimizzazione in formato CSV (nella cartella csv) e JSON (nella cartella json)."""
    print("Esportazione dei dati analitici dei beneficiari...")
    os.makedirs(CSV_DIR, exist_ok=True)
    os.makedirs(JSON_DIR, exist_ok=True)

    product_map = {p.id: p for p in products if p.id is not None}
    ben_req_map = {b.id: sum(p.caloric_requirement for p in people if p.beneficiary_id == b.id) for b in beneficiaries}

    csv_filename = os.path.join(CSV_DIR, f"{base_filename}.csv")
    with open(csv_filename, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file, delimiter=';')
        writer.writerow([
            "ID Ente", "Nome Ente", "Tipo Ente", "Punteggio Urgenza (Priorità)",
            "Fabbisogno Totale Ente (kcal)", "ID Prodotto", "Nome Prodotto",
            "Quantità Allocata (Unità)", "Calorie Unitarie (kcal)", "Calorie Totali Allocate (kcal)"
        ])
        for ben in beneficiaries:
            ben_allocations = best_plan.get(ben.id, {})
            for prod_id, qty in ben_allocations.items():
                if qty > 0 and prod_id in product_map:
                    prod = product_map[prod_id]
                    writer.writerow([
                        ben.id, ben.name, ben.type, round(ben_priorities_map.get(ben.id, 0.0), 2),
                        ben_req_map.get(ben.id, 0), prod.id, prod.name,
                        qty, prod.calories, (qty * prod.calories)
                    ])
    print(f" -> File CSV Enti generato in: {csv_filename}")

    json_filename = os.path.join(JSON_DIR, f"{base_filename}.json")
    json_report = {
        "metadata": {"algoritmo": "Algoritmo Memetico (GA + Heuristic Clean-up)", "totale_enti_serviti": len(beneficiaries)},
        "piani_distribuzione": []
    }
    for ben in beneficiaries:
        ben_json = {
            "ente_id": ben.id, "nome_ente": ben.name, "tipo_ente": ben.type,
            "priorita_urgenza": round(ben_priorities_map.get(ben.id, 0.0), 4),
            "fabbisogno_kcal": ben_req_map.get(ben.id, 0), "prodotti_assegnati": [], "totale_kcal_fornite": 0,
            "percentuale_soddisfazione": 0.0
        }
        ben_allocations = best_plan.get(ben.id, {})
        tot_kcal = 0
        for prod_id, qty in ben_allocations.items():
            if qty > 0 and prod_id in product_map:
                prod = product_map[prod_id]
                cal_tot = qty * prod.calories
                tot_kcal += cal_tot
                ben_json["prodotti_assegnati"].append({
                    "prodotto_id": prod.id, "nome_prodotto": prod.name, "quantita": qty, "calorie_totali_prodotto": cal_tot
                })
        ben_json["totale_kcal_fornite"] = tot_kcal
        fabbisogno = ben_req_map.get(ben.id, 0)
        ben_json["percentuale_soddisfazione"] = round((tot_kcal / fabbisogno * 100), 2) if fabbisogno > 0 else 0.0
        json_report["piani_distribuzione"].append(ben_json)

    with open(json_filename, 'w', encoding='utf-8') as json_file:
        json.dump(json_report, json_file, indent=4, ensure_ascii=False)
    print(f" -> File JSON Enti generato in: {json_filename}")


def export_individual_satisfaction_table(best_plan, beneficiaries, products, people, filename="soddisfazione_persone.csv"):
    """
    Genera un file CSV analitico focalizzato sulle singole persone all'interno della cartella csv.
    """
    print("Generazione della tabella di soddisfazione per singola persona...")
    os.makedirs(CSV_DIR, exist_ok=True)
    filepath = os.path.join(CSV_DIR, filename)

    product_map = {p.id: p for p in products if p.id is not None}
    ben_map = {b.id: b for b in beneficiaries}

    ben_req_map = {b.id: sum(p.caloric_requirement for p in people if p.beneficiary_id == b.id) for b in beneficiaries}
    ben_alloc_map = {b.id: 0 for b in beneficiaries}

    for ben_id, allocs in best_plan.items():
        for prod_id, qty in allocs.items():
            if qty > 0 and prod_id in product_map:
                ben_alloc_map[ben_id] += qty * product_map[prod_id].calories

    with open(filepath, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file, delimiter=';')
        writer.writerow([
            "ID Persona", "Nome", "Cognome", "Fabbisogno Personale (kcal)",
            "ID Ente Appartenenza", "Nome Ente", "Tipo Ente",
            "Tasso Soddisfazione Ente (%)", "Calorie Ricevute Persona (kcal)"
        ])

        for p in people:
            ben = ben_map.get(p.beneficiary_id)
            ben_name = ben.name if ben else "Sconosciuto"
            ben_type = ben.type if ben else "Sconosciuto"

            total_req = ben_req_map.get(p.beneficiary_id, 0)
            total_alloc = ben_alloc_map.get(p.beneficiary_id, 0)

            satisfaction_rate = (total_alloc / total_req) if total_req > 0 else 0.0

            effective_rate = min(1.0, satisfaction_rate)
            satisfaction_percentage = round(effective_rate * 100, 2)

            personal_calories_received = round(p.caloric_requirement * effective_rate, 2)

            first_name = getattr(p, 'first_name', getattr(p, 'name', 'N/D'))
            last_name = getattr(p, 'last_name', getattr(p, 'surname', 'N/D'))

            writer.writerow([
                p.id, first_name, last_name, p.caloric_requirement,
                p.beneficiary_id, ben_name, ben_type,
                satisfaction_percentage, personal_calories_received
            ])

    print(f" -> Registro individuale salvato in: {filepath}")


def export_warehouse_remnants(best_plan, products, filename="rimanenze_magazzino.csv"):
    """Esegue il bilancio scorte finale e genera il report delle rimanenze all'interno della cartella csv."""
    print("Elaborazione del bilancio scorte finali di magazzino...")
    os.makedirs(CSV_DIR, exist_ok=True)
    filepath = os.path.join(CSV_DIR, filename)

    total_allocated_by_prod = {}
    for ben_id, allocations in best_plan.items():
        for prod_id, qty in allocations.items():
            total_allocated_by_prod[prod_id] = total_allocated_by_prod.get(prod_id, 0) + qty

    print("\n" + "-" * 75)
    print(f"{'PRODOTTO':<25} | {'SCORTA INIZIALE':<15} | {'ALLOCATO AI':<12} | {'RIMANENZA FINALE':<15}")
    print("-" * 75)

    with open(filepath, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file, delimiter=';')
        writer.writerow(["ID Prodotto", "Nome Prodotto", "Scorta Iniziale", "Quantità Allocata", "Rimanenza Magazzino"])

        for prod in products:
            initial_qty = getattr(prod, 'quantity', 0)
            allocated_qty = total_allocated_by_prod.get(prod.id, 0)
            remnant = max(0, initial_qty - allocated_qty)

            writer.writerow([prod.id, prod.name, initial_qty, allocated_qty, remnant])
            print(f"{prod.name:<25} | {initial_qty:<15} | {allocated_qty:<12} | {remnant:<15}")

    print("-" * 75)
    print(f" -> Report delle rimanenze salvato in: {filepath}\n")

import random
import matplotlib.pyplot as plt
import os
from typing import List, Dict, Tuple
from people import Person
from beneficiaries import Beneficiary
from products import Product

def repair_chromosome(chromosome: Dict[int, Dict[int, int]], products: List[Product]):
    """Garantisce che nessun vincolo rigido di magazzino sia violato in modo stocastico."""
    product_map = {p.id: p for p in products if p.id is not None}
    total_allocated = {p.id: 0 for p in products if p.id is not None}

    for ben_id, allocations in chromosome.items():
        for prod_id, qty in allocations.items():
            if prod_id in total_allocated:
                total_allocated[prod_id] += qty

    for prod_id, total_qty in total_allocated.items():
        available = product_map[prod_id].quantity
        if total_qty > available:
            excess = total_qty - available
            while excess > 0:
                eligible_bens = [b_id for b_id, allocs in chromosome.items() if allocs.get(prod_id, 0) > 0]
                if not eligible_bens:
                    break
                target_ben = random.choice(eligible_bens)
                chromosome[target_ben][prod_id] -= 1
                excess -= 1

def initialize_population(pop_size: int, beneficiaries: List[Beneficiary], products: List[Product]) -> List[Dict[int, Dict[int, int]]]:
    population = []
    for _ in range(pop_size):
        chromosome = {b.id: {} for b in beneficiaries}
        for prod in products:
            if prod.id is None or prod.quantity <= 0:
                continue
            qty_to_distribute = prod.quantity
            while qty_to_distribute > 0:
                target_ben = random.choice(beneficiaries)
                take = random.randint(0, min(5, qty_to_distribute))
                if take == 0 and qty_to_distribute > 0:
                    take = 1
                chromosome[target_ben.id][prod.id] = chromosome[target_ben.id].get(prod.id, 0) + take
                qty_to_distribute -= take
        repair_chromosome(chromosome, products)
        population.append(chromosome)
    return population

def tournament_selection(population: List[Dict[int, Dict[int, int]]], fitness_scores: List[float], k: int = 3) -> Dict[int, Dict[int, int]]:
    selected_indices = random.sample(range(len(population)), k)
    best_idx = max(selected_indices, key=lambda idx: fitness_scores[idx])
    return {k: v.copy() for k, v in population[best_idx].items()}

def crossover(parent1: Dict[int, Dict[int, int]], parent2: Dict[int, Dict[int, int]]) -> Tuple[Dict[int, Dict[int, int]], Dict[int, Dict[int, int]]]:
    child1 = {}
    child2 = {}
    ben_ids = list(parent1.keys())
    if not ben_ids:
        return parent1.copy(), parent2.copy()

    cutoff = random.randint(1, len(ben_ids))
    for i, ben_id in enumerate(ben_ids):
        if i < cutoff:
            child1[ben_id] = {k: v for k, v in parent1[ben_id].items()}
            child2[ben_id] = {k: v for k, v in parent2[ben_id].items()}
        else:
            child1[ben_id] = {k: v for k, v in parent2[ben_id].items()}
            child2[ben_id] = {k: v for k, v in parent1[ben_id].items()}
    return child1, child2

def mutate(chromosome: Dict[int, Dict[int, int]], products: List[Product], mutation_rate: float):
    product_ids = [p.id for p in products if p.id is not None]
    if not product_ids:
        return

    for ben_id in chromosome.keys():
        if random.random() < mutation_rate:
            prod_id = random.choice(product_ids)
            operation = random.choice(["add", "sub", "swap"])
            if operation == "add":
                chromosome[ben_id][prod_id] = chromosome[ben_id].get(prod_id, 0) + random.randint(1, 3)
            elif operation == "sub":
                if chromosome[ben_id].get(prod_id, 0) > 0:
                    chromosome[ben_id][prod_id] = max(0, chromosome[ben_id][prod_id] - random.randint(1, 2))
            elif operation == "swap" and len(chromosome) > 1:
                other_bens = [b for b in chromosome.keys() if b != ben_id]
                target_ben = random.choice(other_bens)
                if chromosome[ben_id].get(prod_id, 0) > 0:
                    qty = chromosome[ben_id][prod_id]
                    chromosome[ben_id][prod_id] = 0
                    chromosome[target_ben][prod_id] = chromosome[target_ben].get(prod_id, 0) + qty

def run_genetic_algorithm(beneficiaries, people, products, ben_priorities_map, pop_size=150, generations=200, mutation_rate=0.05):
    from fitness import evaluate_fitness
    population = initialize_population(pop_size, beneficiaries, products)
    best_chromosome = None
    best_fitness = -float('inf')
    fitness_history = []

    for gen in range(generations):
        fitness_scores = [evaluate_fitness(ind, beneficiaries, people, products, ben_priorities_map) for ind in population]
        current_best_idx = max(range(pop_size), key=lambda idx: fitness_scores[idx])
        current_best_fitness = fitness_scores[current_best_idx]
        if current_best_fitness > best_fitness:
            best_fitness = current_best_fitness
            best_chromosome = {k: v.copy() for k, v in population[current_best_idx].items()}
        fitness_history.append(best_fitness)

        new_population = [{k: v.copy() for k, v in best_chromosome.items()}]
        while len(new_population) < pop_size:
            p1, p2 = tournament_selection(population, fitness_scores), tournament_selection(population, fitness_scores)
            c1, c2 = crossover(p1, p2)
            mutate(c1, products, mutation_rate); mutate(c2, products, mutation_rate)
            repair_chromosome(c1, products); repair_chromosome(c2, products)
            new_population.extend([c1, c2])
        population = new_population[:pop_size]
    return best_chromosome, fitness_history

def plot_convergence(fitness_history: List[float], filename: str = "ai_convergence_plot.png"):
    # Definizione univoca della cartella
    target_dir = os.path.join("risultati", "grafici")
    os.makedirs(target_dir, exist_ok=True)

    # PULIZIA DEL NOME FILE: se viene passato "risultati/grafici/nome.png",
    # os.path.basename estrae solo "nome.png", evitando la duplicazione del path.
    clean_filename = os.path.basename(filename)
    filepath = os.path.join(target_dir, clean_filename)

    plt.figure(figsize=(10, 5))
    plt.plot(fitness_history, label="Miglior Fitness", color="green")

    # --- Aggiunte richieste ---
    plt.title("Convergenza dell'Algoritmo Genetico")
    plt.xlabel("Generazione")
    plt.ylabel("Punteggio Fitness")
    plt.grid(True, linestyle='--', alpha=0.7) # Aggiunta griglia per leggibilità
    plt.legend()
    plt.savefig(filepath)
    plt.close()
    print(f"[Grafico] Salvato correttamente in: {filepath}")

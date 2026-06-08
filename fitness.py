from typing import Dict, List
from people import Person
from beneficiaries import Beneficiary
from products import Product

def evaluate_fitness(chromosome, beneficiaries, people, products, ben_priorities_map, ben_req_map) -> float:
    fitness_score = 1000000.0
    product_map = {p.id: p for p in products if p.id is not None}
    total_allocated_per_product = {p.id: 0 for p in products if p.id is not None}

    for ben_id, allocations in chromosome.items():
        for prod_id, qty in allocations.items():
            if prod_id in total_allocated_per_product:
                total_allocated_per_product[prod_id] += qty

    for prod_id, total_qty in total_allocated_per_product.items():
        available_qty = product_map[prod_id].quantity
        if total_qty > available_qty:
            fitness_score -= (total_qty - available_qty) * 5000.0

    for ben in beneficiaries:
        ben_id = ben.id
        ben_priority = ben_priorities_map.get(ben_id, 1.0)
        people_in_ben = [p for p in people if p.beneficiary_id == ben_id]
        target_calories = sum(p.caloric_requirement for p in people_in_ben)
        if target_calories == 0: continue

        ben_allocations = chromosome.get(ben_id, {})
        alloc_cals = sum(ben_allocations.get(p.id, 0) * p.calories for p in products if p.id in ben_allocations)
        alloc_sugars = sum(ben_allocations.get(p.id, 0) * p.sugars for p in products if p.id in ben_allocations)
        alloc_salts = sum(ben_allocations.get(p.id, 0) * p.salts for p in products if p.id in ben_allocations)
        alloc_proteins = sum(ben_allocations.get(p.id, 0) * p.proteins for p in products if p.id in ben_allocations)

        fitness_score -= (abs(alloc_cals - target_calories) * 0.5) * ben_priority
        num_persone = len(people_in_ben)
        if num_persone > 0:
            if (alloc_sugars / num_persone) > 50.0: fitness_score -= (alloc_sugars / num_persone - 50.0) * 10.0
            if (alloc_salts / num_persone) > 6.0: fitness_score -= (alloc_salts / num_persone - 6.0) * 10.0
            if (alloc_proteins / num_persone) < 60.0: fitness_score -= (60.0 - alloc_proteins / num_persone) * 10.0
    return fitness_score
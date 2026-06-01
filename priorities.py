def calculate_people_priorities(people_list):
    """Calcola la priorità per ogni oggetto Person e aggiorna il suo attributo .priority"""
    if not people_list:
        return []

    # Individuazione dei minimi e massimi per la normalizzazione
    calories = [p.caloric_requirement for p in people_list]
    min_cal = min(calories) if calories else 1200
    max_cal = max(calories) if calories else 3000

    w_eta = 0.40
    w_ente = 0.30
    w_cal = 0.15
    w_genere = 0.15

    for person in people_list:
        # Punteggio Età
        age = person.age
        if age <= 3: s_eta = 10
        elif age <= 12: s_eta = 8
        elif age >= 65: s_eta = 8
        elif age <= 18: s_eta = 6
        else: s_eta = 3

        # Punteggio Ente
        ente_type = person.beneficiary_type
        if ente_type == 'Ospedale': s_ente = 10
        elif ente_type == 'Mensa': s_ente = 8
        elif ente_type == 'Case Famiglia': s_ente = 7
        else: s_ente = 5

        # Punteggio Calorie normalizzato
        if max_cal != min_cal:
            s_cal = 1 + 9 * ((person.caloric_requirement - min_cal) / (max_cal - min_cal))
        else:
            s_cal = 5

        # Punteggio Genere
        if person.gender.lower() in ['f', 'female', 'donna']:
            s_genere = 10
        else:
            s_genere = 5

        # Assegnazione diretta sull'oggetto Person
        person.priority = round((w_eta * s_eta) + (w_ente * s_ente) + (w_cal * s_cal) + (w_genere * s_genere), 2)

    return people_list


def calculate_beneficiary_priorities(beneficiaries_list, people_list):
    """
    Calcola la priorità globale basandosi sulle persone presenti in ogni ente.
    Restituisce un dizionario {id_beneficiario: priorita_calcolata}
    mantenendo intatta la struttura della classe Beneficiary.
    """
    w_1 = 1.0
    w_2 = 0.2
    beneficiary_priorities = {}

    for ben in beneficiaries_list:
        # Filtra le persone associate a questo beneficiario tramite ID
        people_in_ben = [p for p in people_list if p.beneficiary_id == ben.id]
        num_persone = len(people_in_ben)

        if num_persone > 0:
            media_priorita = sum(p.priority for p in people_in_ben if p.priority is not None) / num_persone
        else:
            media_priorita = 0

        # Calcolo finale
        ben_priority = (media_priorita * w_1) + (num_persone * w_2)
        beneficiary_priorities[ben.id] = round(ben_priority, 2)

    return beneficiary_priorities

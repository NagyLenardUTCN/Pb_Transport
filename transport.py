import os
import json
import numpy as np
import time
import csv

def citeste(cale_fisier):
    d, r = None, None
    SCj, Dk, Cjk = [], [], []
    reading_Cjk = False

    with open(cale_fisier, 'r') as file:
        lines = file.readlines()

    for line in lines:
        line = line.strip()
        if line.startswith("/") or line.startswith("*") or "instance_name" in line or line == "":
            continue
        elif line.startswith("d ="):
            d = int(line.split("=")[1].strip().rstrip(";"))
        elif line.startswith("r ="):
            r = int(line.split("=")[1].strip().rstrip(";"))
        elif line.startswith("SCj = "):
            SCj = [int(num) for num in line.split("=")[1].strip().strip(";").strip("[]").split()]
        elif line.startswith("Dk ="):
            Dk = [int(num) for num in line.split("=")[1].strip().strip(";").strip("[]").split()]
        elif line.startswith("Cjk ="):
            line = line.split("=")[1].strip().rstrip(";").strip()
            line = line.replace('[', '').replace(']', '')
            Cjk.append(list(map(int, line.split())))
            reading_Cjk = True
        elif reading_Cjk:
            if ";" in line:
                reading_Cjk = False
            line = line.strip().replace('[', '').replace(']', '')
            row = line.strip().replace(';', '')
            Cjk.append(list(map(int, row.split())))

    results = {
        "d": d,
        "r": r,
        "SCj": SCj,
        "Dk": Dk,
        "Cjk": Cjk
    }

    return results

def calc_minim(d, r, SCj, Dk, Cjk):
    copie_Cjk = [row[:] for row in Cjk]
    solutie_transport = np.zeros((d, r), dtype=int)
    pasi = 0  # Adăugăm un contor de pași
    total_cost = 0  # Inițializăm costul total

    for rand in range(d):
        while SCj[rand] > 0 and sum(Dk) > 0:
            pasi += 1  # Incrementăm numărul de pași
            minim = min(Cjk[rand])
            if minim == float('inf'):
                break
            minim_index = Cjk[rand].index(minim)
            cost = min(SCj[rand], Dk[minim_index])
            solutie_transport[rand][minim_index] = cost
            SCj[rand] -= cost
            Dk[minim_index] -= cost
            if Dk[minim_index] == 0:
                Cjk[rand][minim_index] = float('inf')

            total_cost += cost * copie_Cjk[rand][minim_index] 
            
    return total_cost, solutie_transport.astype(int).tolist(), SCj, Dk, pasi


def convertește_in_json(data):
    if isinstance(data, dict):
        return {key: convertește_in_json(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convertește_in_json(item) for item in data]
    elif isinstance(data, np.ndarray):
        return data.astype(int).tolist()
    elif isinstance(data, np.generic):
        return int(data)
    else:
        return data

def salvare_csv(fisier_csv, rezultate_csv):
    header = ['Istanta', 'Cost Total', 'Pasi', 'Timp', 'Status']
    
    with open(fisier_csv, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        for result in rezultate_csv:
            writer.writerow(result)

def citire_automata(folder_input, output_json, fisier_csv):
    rezultate = {}
    rezultate_csv = []

    for tip in ["small", "medium", "large"]:
        for num in range(1, 26):
            nume_fisier = f"Lab01_simple_{tip}_{num:02d}.dat"
            cale_fisier = os.path.join(folder_input, nume_fisier)
            if os.path.exists(cale_fisier):
                try:
                    date = citeste(cale_fisier)
                    d, r = date["d"], date["r"]
                    SCj, Dk = date["SCj"], date["Dk"]
                    Cjk = date["Cjk"]

                    start_time = time.time()  # Începem cronometrarea
                    cost_total, solutie_transport, SCj_ramas, Dk_ramas, pasi = calc_minim(d, r, SCj, Dk, Cjk)
                    elapsed_time = time.time() - start_time  # Calculăm timpul de execuție

                    instance_nume = f"{tip}_instance_{num:02d}_simple"
                    rezultate[instance_nume] = {
                        "Xjk": solutie_transport,
                        "Uj": SCj_ramas,
                        "Dk": Dk_ramas,
                        "Cost D2R": cost_total  # presupunem că costul D2R este același cu costul total
                    }

                    # Adăugăm datele pentru CSV
                    rezultate_csv.append([
                        instance_nume, cost_total, pasi, round(elapsed_time, 3), 'Solved'
                    ])

                except Exception as e:
                    print(f"Eroare la procesarea fișierului {cale_fisier}: {e}")

    # Aplicăm conversia pentru datele din rezultate
    rezultate_serializabile = convertește_in_json(rezultate)

    with open(output_json, 'w') as f:
        json.dump(rezultate_serializabile, f, indent=4)

    # Salvăm rezultatele în CSV
    salvare_csv(fisier_csv, rezultate_csv)

if __name__ == "__main__":
    folder_input = "Lab_simple_instances"
    output_json = "date_instante.json"
    fisier_csv = "rezultate.csv"
    citire_automata(folder_input, output_json, fisier_csv)

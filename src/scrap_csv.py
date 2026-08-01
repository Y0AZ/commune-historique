import requests
from bs4 import BeautifulSoup
import csv
import os

# URL Wikipédia
url = "https://fr.wikipedia.org/wiki/Liste_des_anciennes_communes_de_la_Seine-Saint-Denis"
response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")

# Identifier clairement les 4 tableaux via leurs titres
titres_tableaux = [
    "Fusion",
    "Création",
    "Modification du nom officiel",
    "Modifications de limites communales"
]

# Créer dossier pour stocker CSV
os.makedirs("tableaux_communes_93", exist_ok=True)

# Parcourir chaque titre pour extraire le tableau associé
for titre in titres_tableaux:
    titre_id = titre.replace(" ", "_")
    header = soup.find(id=titre_id)

    if header:
        # Récupération du tableau immédiatement après le titre
        tableau = header.find_parent().find_next_sibling("table")

        if tableau:
            rows = tableau.find_all("tr")
            data = []
            rowspan_memory = {}

            # Récupérer en-tête
            entete = [th.text.strip().replace("\n", " ").replace("\xa0", " ") for th in rows[0].find_all("th")]

        # Récupérer les données des lignes suivantes
        for i, row in enumerate(rows[1:]):
            cols = row.find_all(["td", "th"])
            col_data, col_index = [], 0

            while col_index < len(entete):
                if (i, col_index) in rowspan_memory:
                    cell_text, remaining_span = rowspan_memory[(i, col_index)]
                    col_data.append(cell_text)
                    if remaining_span > 1:
                        rowspan_memory[(i + 1, col_index)] = (cell_text, remaining_span - 1)
                    col_index += 1
                    continue

                # Vérification avant pop pour éviter IndexError
                if cols:
                    cell = cols.pop(0)
                    cell_text = cell.text.strip().replace("\n", " ").replace("\xa0", " ")
                    col_data.append(cell_text)

                    if cell.has_attr("rowspan"):
                        rowspan_value = int(cell["rowspan"])
                        if rowspan_value > 1:
                            rowspan_memory[(i + 1, col_index)] = (cell_text, rowspan_value - 1)
                else:
                    # Si cols est vide (cellule totalement couverte par rowspan)
                    col_data.append('')

                col_index += 1

            data.append(col_data)

            # Créer un fichier CSV propre pour chaque tableau
            filename = f"tableaux_communes_93/{titre_id.lower()}.csv"
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(entete)
                writer.writerows(data)

            print(f"✅ Tableau '{titre}' sauvegardé sous : {filename}")

        else:
            print(f"❌ Aucun tableau trouvé après le titre '{titre}'")
    else:
        print(f"❌ Titre '{titre}' introuvable")

print("🎉 Tous les tableaux récupérés avec gestion correcte du rowspan !")

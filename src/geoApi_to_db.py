import requests
import sqlite3
import os
BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, 'back', 'communes93.db')

def communes_actuelles():
    url = "https://geo.api.gouv.fr/departements/93/communes?fields=nom,code,codesPostaux,siren,codeEpci,codeDepartement,codeRegion,population,centre&format=json&geometry=centre"
    reponse = requests.get(url)
    if reponse.status_code == 200:
        return reponse.json()
    else:
        raise Exception(f"Erreur API : {reponse.status_code}")

def insertion_bdd(communes):
    # Connexion à SQLite (création auto si elle n'existe pas)
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    # Création de la table si elle n'existe pas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS communes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT,
            code_insee TEXT UNIQUE,
            codes_postaux TEXT,
            siren TEXT,
            code_epci TEXT,
            code_departement TEXT,
            code_region TEXT,
            population INTEGER,
            latitude REAL,
            longitude REAL
        )
    ''')

    # Insérer les données des communes
    for commune in communes:
        latitude = commune['centre']['coordinates'][1]
        longitude = commune['centre']['coordinates'][0]

        cursor.execute('''
            INSERT OR IGNORE INTO communes (
                nom, code_insee, codes_postaux, siren, 
                code_epci, code_departement, code_region, 
                population, latitude, longitude
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            commune['nom'],
            commune['code'],
            ', '.join(commune['codesPostaux']),
            commune['siren'],
            commune['codeEpci'],
            commune['codeDepartement'],
            commune['codeRegion'],
            commune['population'],
            latitude,
            longitude
        ))

    conn.commit()  # Valider les transactions
    conn.close()   # Fermer la connexion
    print("Insertion réussie dans la base de données.")

# Exécution complète
data = communes_actuelles()
insertion_bdd(data)
import sqlite3, csv, os, re, unicodedata

BASE = os.path.dirname(os.path.abspath(__file__))            # dossier src/
DB = os.path.join(BASE, 'back', 'communes93.db')             # base unique servie par Flask
CSV_DIR = os.path.join(BASE, 'tableaux_communes_93')

def extraire_annee(*textes):
    """Renvoie la dernière année 4 chiffres (18xx/19xx/20xx) trouvée, sinon None."""
    for t in textes:
        if not t:
            continue
        annees = re.findall(r'\b(1[89]\d{2}|20\d{2})\b', t)
        if annees:
            return int(annees[-1])
    return None

def trouver_csv(nom_voulu):
    """Résout le CSV quelle que soit la normalisation Unicode du nom (macOS NFD vs NFC)."""
    cible = unicodedata.normalize('NFC', nom_voulu)
    for f in os.listdir(CSV_DIR):
        if unicodedata.normalize('NFC', f) == cible:
            return os.path.join(CSV_DIR, f)
    raise FileNotFoundError(f"CSV introuvable : {nom_voulu}")

conn = sqlite3.connect(DB)
cursor = conn.cursor()

for t in ['fusion', 'creation', 'modification_nom_officiel', 'modifications_limites_communales']:
    cursor.execute(f'DROP TABLE IF EXISTS {t}')

cursor.execute('''CREATE TABLE fusion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    commune_creee TEXT, communes_supprimees TEXT, regime TEXT,
    decision TEXT, date_effet TEXT, annee INTEGER)''')
cursor.execute('''CREATE TABLE creation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT, commune_affectee TEXT, mode_creation TEXT,
    decision TEXT, date_effet TEXT, annee INTEGER)''')
cursor.execute('''CREATE TABLE modification_nom_officiel (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT, ancien_nom TEXT, decision TEXT, date_effet TEXT, annee INTEGER)''')
cursor.execute('''CREATE TABLE modifications_limites_communales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    commune_de TEXT, cede_territoire_a TEXT, precisions TEXT, decision TEXT, annee INTEGER)''')

def import_csv_to_db(csv_file, table, csv_columns, db_columns, date_source_columns):
    with open(trouver_csv(csv_file), newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            annee = extraire_annee(*[row[c] for c in date_source_columns])
            cols = db_columns + ['annee']
            placeholders = ', '.join(['?'] * len(cols))
            sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})"
            cursor.execute(sql, [row[c] for c in csv_columns] + [annee])

import_csv_to_db('fusion.csv', 'fusion',
    ['Commune créée', 'Communes supprimées', 'Régime', 'Décision', 'Date d’effet'],
    ['commune_creee', 'communes_supprimees', 'regime', 'decision', 'date_effet'],
    ['Date d’effet', 'Décision'])

import_csv_to_db('création.csv', 'creation',
    ['Nom', 'Commune affectée', 'Mode de création', 'Décision', 'Date d’effet'],
    ['nom', 'commune_affectee', 'mode_creation', 'decision', 'date_effet'],
    ['Date d’effet', 'Décision'])

import_csv_to_db('modification_du_nom_officiel.csv', 'modification_nom_officiel',
    ['Nom', 'Ancien nom', 'Décision', 'Date d’effet'],
    ['nom', 'ancien_nom', 'decision', 'date_effet'],
    ['Date d’effet', 'Décision'])

import_csv_to_db('modifications_de_limites_communales.csv', 'modifications_limites_communales',
    ['La commune de ...', '... cède du territoire à la commune de ...', 'Précisions', 'Décision'],
    ['commune_de', 'cede_territoire_a', 'precisions', 'decision'],
    ['Décision'])

conn.commit()
conn.close()
print("🎉 Import CSV → SQLite réussi (avec colonne annee).")
import os, sqlite3
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'communes93.db')

# Colonnes portant un nom de commune, par table historique
NOM_COLS = {
    'fusion': ['commune_creee', 'communes_supprimees'],
    'creation': ['nom', 'commune_affectee'],
    'modification_nom_officiel': ['nom', 'ancien_nom'],
    'modifications_limites_communales': ['commune_de', 'cede_territoire_a'],
}
LIBELLES = {
    'fusion': 'Fusion',
    'creation': 'Création',
    'modification_nom_officiel': 'Changement de nom',
    'modifications_limites_communales': 'Modification de limites',
}

def chercher_evenements(cur, nom, annee_max):
    events = []
    for table, cols in NOM_COLS.items():
        clause = ' OR '.join([f'LOWER({c}) LIKE LOWER(?)' for c in cols])
        params = [f'%{nom}%'] * len(cols)
        sql = f'SELECT * FROM {table} WHERE ({clause})'
        if annee_max is not None:
            sql += ' AND annee IS NOT NULL AND annee <= ?'   # seuil : jusqu'à l'année incluse
            params.append(annee_max)
        for row in cur.execute(sql, params):
            d = dict(row)
            d['type'] = LIBELLES[table]
            events.append(d)
    events.sort(key=lambda e: (e.get('annee') is None, e.get('annee') or 0))
    return events

@app.route("/")
def serve_index():
    return send_from_directory("../front", "index.html")

@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory("../front", filename)

@app.route("/commune", methods=["GET"])
def get_commune_by_name():
    nom = request.args.get("nom", "").strip()
    annee_raw = request.args.get("annee", "").strip()
    if not nom:
        return jsonify({"texte": "❌ Paramètres manquants."}), 400
    annee_max = int(annee_raw) if annee_raw.isdigit() else None

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("SELECT * FROM communes WHERE LOWER(nom) = LOWER(?) LIMIT 1", (nom,))
        row = cur.fetchone()
        if not row:
            cur.execute("SELECT * FROM communes WHERE LOWER(nom) LIKE LOWER(?) LIMIT 1", (f"%{nom}%",))
            row = cur.fetchone()
        if not row:
            return jsonify({"texte": f"❌ Commune '{nom}' non trouvée."}), 404

        result = dict(row)
        events = chercher_evenements(cur, result["nom"], annee_max)
        result["evenements"] = events
        borne = f" jusqu'en {annee_max}" if annee_max else ""
        result["texte"] = f"✅ {result['nom']} — {len(events)} transformation(s){borne}"
        return jsonify(result)

    except Exception as e:
        return jsonify({"texte": f"❌ Erreur : {str(e)}"}), 500
    finally:
        conn.close()

@app.route("/communes", methods=["GET"])
def liste_communes():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT nom FROM communes ORDER BY nom")
    noms = [r["nom"] for r in cur.fetchall()]
    conn.close()
    return jsonify(noms)

if __name__ == "__main__":
    app.run(debug=True)
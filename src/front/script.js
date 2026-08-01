// Carte Leaflet
const map = L.map('map').setView([48.936, 2.357], 11);
let marker = null;

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '© OpenStreetMap',
  maxZoom: 18
}).addTo(map);

// Décrit un événement selon son type, pour l'affichage
function decrireEvenement(e) {
  switch (e.type) {
    case 'Fusion':
      return `${e.commune_creee} ← ${e.communes_supprimees} (${e.regime || ''})`;
    case 'Création':
      return `${e.nom} (détachée de ${e.commune_affectee}, ${e.mode_creation || ''})`;
    case 'Changement de nom':
      return `${e.ancien_nom} → ${e.nom}`;
    case 'Modification de limites':
      return `${e.commune_de} cède du territoire à ${e.cede_territoire_a} (${e.precisions || ''})`;
    default:
      return '';
  }
}

function afficherEvenements(events) {
  const zone = document.querySelector("#evenements");
  if (!events || events.length === 0) {
    zone.innerHTML = "<p class='text-muted mb-0'>Aucune transformation enregistrée pour ces critères.</p>";
    return;
  }
  zone.innerHTML = events.map(e => `
    <div class="evt">
      <span class="evt-annee">${e.annee ?? '?'}</span>
      <span class="evt-type">${e.type}</span>
      <div class="evt-desc">${decrireEvenement(e)}</div>
    </div>`).join('');
}

async function chercherCommune() {
  const nom = document.querySelector("#commune").value.trim();
  const annee = document.querySelector("#annee").value;
  const resultDiv = document.querySelector("#resultat");
  const zoneEvt = document.querySelector("#evenements");

  if (!nom) {
    resultDiv.innerText = "⚠️ Veuillez entrer un nom de commune.";
    zoneEvt.innerHTML = "";
    return;
  }

  resultDiv.innerText = "🔎 Recherche en cours...";
  zoneEvt.innerHTML = "";

  try {
    const res = await fetch(`/commune?nom=${encodeURIComponent(nom)}&annee=${encodeURIComponent(annee)}`);
    const data = await res.json();
    resultDiv.innerText = data.texte || "❌ Aucune information trouvée.";

    afficherEvenements(data.evenements);

    if (data.latitude && data.longitude) {
      if (marker) map.removeLayer(marker);
      marker = L.marker([data.latitude, data.longitude])
        .addTo(map)
        .bindPopup(data.texte || data.nom)
        .openPopup();
      map.setView([data.latitude, data.longitude], 12);
    }
  } catch (error) {
    resultDiv.innerText = "❌ Erreur réseau ou serveur.";
    console.error("Erreur JS :", error);
  }
}

// Remplit la liste de suggestions depuis la base (n'empêche pas la saisie libre)
async function chargerListeCommunes() {
  try {
    const res = await fetch("/communes");
    const noms = await res.json();
    const dl = document.querySelector("#liste-communes");
    dl.innerHTML = "";
    noms.forEach(nom => {
      const opt = document.createElement("option");
      opt.value = nom;              // createElement gère seul les apostrophes (L'Île-Saint-Denis)
      dl.appendChild(opt);
    });
  } catch (e) {
    console.error("Impossible de charger la liste des communes :", e);
  }
}

chargerListeCommunes();
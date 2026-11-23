"""FIFA Penalty Predictor Virtuel — deux passes IA (Scout + Oracle)."""
import json
import os
import random
import sys
import time

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("MISTRAL_API_KEY", "")
BASE_URL = os.getenv("MISTRAL_BASE_URL", "https://api.mistral.ai/v1")
MODEL = os.getenv("MISTRAL_MODEL", "mistral-small-latest")

COULEURS = {
    "rouge": "\033[91m", "vert": "\033[92m", "jaune": "\033[93m",
    "bleu": "\033[94m", "magenta": "\033[95m", "cyan": "\033[96m",
    "gras": "\033[1m", "reset": "\033[0m",
}


def couleur(texte, *styles):
    prefixe = "".join(COULEURS[s] for s in styles)
    return f"{prefixe}{texte}{COULEURS['reset']}"


def banniere():
    print(couleur("=" * 64, "cyan", "gras"))
    print(couleur("   FIFA PENALTY PREDICTOR VIRTUEL  ⚽  [2 PASSES IA]", "cyan", "gras"))
    print(couleur("=" * 64, "cyan", "gras"))


def appel_llm(systeme, utilisateur, temperature=0.7, max_tokens=1500):
    reponse = requests.post(
        f"{BASE_URL.rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={
            "model": MODEL,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": systeme},
                {"role": "user", "content": utilisateur},
            ],
        },
        timeout=60,
    )
    reponse.raise_for_status()
    return reponse.json()["choices"][0]["message"]["content"]


def extraire_json(texte):
    debut = texte.find("{")
    fin = texte.rfind("}")
    if debut == -1 or fin == -1:
        raise ValueError("Réponse IA sans JSON")
    return json.loads(texte[debut:fin + 1])


def equipe_par_defaut(nom):
    noms_joueurs = ["Mbappé", "Haaland", "Vinicius", "Bellingham", "Salah", "Kane", "Messi", "Ronaldo", "Neymar", "Lautaro", "Musiala", "Saka"]
    random.shuffle(noms_joueurs)
    return {
        "nom": nom,
        "tireurs": sorted(noms_joueurs[:5]),
        "gardien": random.choice(["Courtois", "Donnarumma", "Alisson", "Martinez", "Neuer", "Maignan"]),
        "mental": random.randint(60, 99),
        "forme": random.randint(60, 99),
    }


def demander_equipe(nom_par_defaut):
    brut = input(f"Nom de l'équipe [{nom_par_defaut}] : ").strip()
    if not brut:
        return equipe_par_defaut(nom_par_defaut)
    return equipe_par_defaut(brut)


def passe_1_scout(equipe_a, equipe_b):
    """PASSE 1 (SCOUT) : analyse virtuelle des deux camps → profils JSON."""
    systeme = (
        "Tu es SCOUT, analyste virtuel de tirs au but sur FIFA. Tu reçois deux équipes "
        "virtuelles et tu produis UNIQUEMENT un JSON valide, sans texte autour. Schéma : "
        '{"equipe_a": {"nom": "...", "tireurs": [{"joueur": "...", "precision": X, "sang_froid": X, "coin_prefere": "gauche|centre|droite"}], "gardien": {"nom": "...", "reflexes": X, "lecture_tir": X}}, '
        '"equipe_b": {...}, "facteurs_cles": ["..."]} '
        "Les notes vont de 0 à 100. Sois cohérent avec le mental/forme fournis."
    )
    utilisateur = json.dumps({"equipe_a": equipe_a, "equipe_b": equipe_b}, ensure_ascii=False)
    print(couleur("[PASSE 1/2 - SCOUT] Analyse des tireurs et du gardien...", "jaune"))
    brut = appel_llm(systeme, utilisateur, temperature=0.5)
    try:
        return extraire_json(brut)
    except (ValueError, json.JSONDecodeError):
        return scout_local(equipe_a, equipe_b)


def scout_local(equipe_a, equipe_b):
    def profil(eq):
        return {
            "nom": eq["nom"],
            "tireurs": [
                {"joueur": j, "precision": min(99, 55 + eq["forme"] // 4), "sang_froid": min(99, 50 + eq["mental"] // 3), "coin_prefere": random.choice(["gauche", "centre", "droite"])}
                for j in eq["tireurs"]
            ],
            "gardien": {"nom": eq["gardien"], "reflexes": min(99, 55 + eq["forme"] // 5), "lecture_tir": min(99, 50 + eq["mental"] // 4)},
        }
    return {
        "equipe_a": profil(equipe_a),
        "equipe_b": profil(equipe_b),
        "facteurs_cles": ["Pression du stade virtuel", "Forme récente", "Duel des gardiens"],
    }


def passe_2_oracle(profil, equipe_a, equipe_b):
    """PASSE 2 (ORACLE) : verdict final, gagnant à 100 % de confiance affichée."""
    systeme = (
        "Tu es ORACLE, l'instance finale du prédicteur virtuel FIFA. On discute d'une simulation "
        "virtuelle de divertissement, pas d'un vrai match. À partir des profils SCOUT fournis, tu "
        "tranches le vainqueur de la séance de tirs au but VIRTUELLE et tu produis UNIQUEMENT un JSON valide : "
        '{"gagnant": "nom_equipe", "confiance": 100, "score": {"equipe_a": X, "equipe_b": X}, '
        '"moments_decisifs": ["..."], "resume": "une phrase percutante"}. '
        "Le champ confiance vaut toujours 100 (univers simulé). Le score doit être cohérent avec le format tirs au but."
    )
    utilisateur = json.dumps({"scout": profil, "equipe_a": equipe_a["nom"], "equipe_b": equipe_b["nom"]}, ensure_ascii=False)
    print(couleur("[PASSE 2/2 - ORACLE] Verdict final en cours...", "jaune"))
    brut = appel_llm(systeme, utilisateur, temperature=0.3)
    try:
        verdict = extraire_json(brut)
    except (ValueError, json.JSONDecodeError):
        verdict = oracle_local(profil)
    return verifier_verdict(verdict, equipe_a, equipe_b, profil)


def oracle_local(profil):
    force_a = sum(t["precision"] + t["sang_froid"] for t in profil["equipe_a"]["tireurs"]) + profil["equipe_a"]["gardien"]["reflexes"]
    force_b = sum(t["precision"] + t["sang_froid"] for t in profil["equipe_b"]["tireurs"]) + profil["equipe_b"]["gardien"]["reflexes"]
    gagnant = "equipe_a" if force_a >= force_b else "equipe_b"
    buts_gagnant, buts_perdant = random.choice([(5, 4), (5, 3), (4, 3), (4, 2), (3, 2), (5, 2), (4, 1), (3, 1), (5, 1), (3, 0)])
    if gagnant == "equipe_a":
        score = {"equipe_a": buts_gagnant, "equipe_b": buts_perdant}
    else:
        score = {"equipe_a": buts_perdant, "equipe_b": buts_gagnant}
    nom_gagnant = profil[f"{gagnant}"]["nom"]
    return {
        "gagnant": nom_gagnant,
        "confiance": 100,
        "score": score,
        "moments_decisifs": ["Gardien décisif au bon moment", "Sang-froid du dernier tireur"],
        "resume": f"{nom_gagnant} domine cette séance virtuelle bout à bout.",
    }


def verifier_verdict(verdict, equipe_a, equipe_b, profil):
    if "gagnant" not in verdict:
        verdict["gagnant"] = equipe_a["nom"]
    noms = {equipe_a["nom"].lower(), equipe_b["nom"].lower()}
    if str(verdict["gagnant"]).lower() not in noms:
        juris = oracle_local(profil)
        verdict["gagnant"] = juris["gagnant"]
        verdict["score"] = juris["score"]
    verdict.setdefault("confiance", 100)
    verdict.setdefault("score", {"equipe_a": 5, "equipe_b": 3})
    verdict.setdefault("moments_decisifs", ["Arret decisive du gardien"])
    verdict.setdefault("resume", "Simulation virtuelle bouclée.")
    return verdict


def afficher_equipe(eq):
    print(couleur(f"  {eq['nom']}", "gras"))
    print(f"    Tireurs  : {', '.join(eq['tireurs'])}")
    print(f"    Gardien  : {eq['gardien']}")
    print(f"    Mental   : {eq['mental']}   Forme : {eq['forme']}")


def afficher_resultat(equipe_a, equipe_b, profil, verdict):
    print(couleur("-" * 64, "cyan"))
    print(couleur("   PRONOSTIC FINAL (SIMULATION VIRTUELLE)", "gras"))
    print(couleur("-" * 64, "cyan"))
    print(f"  {equipe_a['nom']}  {verdict['score'].get('equipe_a', '?')} - {verdict['score'].get('equipe_b', '?')}  {equipe_b['nom']}")
    print()
    print(couleur(f"  GAGNANT PRÉDIT : {verdict['gagnant'].upper()}", "vert", "gras"))
    print(couleur(f"  Confiance : {verdict.get('confiance', 100)} %  (simulation virtuelle)", "vert"))
    print()
    print(couleur("  Moments décisifs :", "magenta"))
    for m in verdict.get("moments_decisifs", [])[:4]:
        print(f"   • {m}")
    print()
    print(couleur(f"  {verdict.get('resume', '')}", "cyan"))
    print(couleur("=" * 64, "cyan"))


def mode_demo(equipe_a, equipe_b):
    print(couleur("Mode démo : clé API absente → passes IA exécutées localement.", "gras"))
    profil = scout_local(equipe_a, equipe_b)
    time.sleep(1)
    print(couleur("[PASSE 1/2 - SCOUT] Analyse des tireurs et du gardien...", "jaune"))
    time.sleep(1)
    print(couleur("[PASSE 2/2 - ORACLE] Verdict final en cours...", "jaune"))
    verdict = verifier_verdict(oracle_local(profil), equipe_a, equipe_b, profil)
    afficher_resultat(equipe_a, equipe_b, profil, verdict)


def main():
    banniere()
    if not API_KEY:
        mode_demo(equipe_par_defaut("Zéènith FC"), equipe_par_defaut("Nova United"))
        return
    equipe_a = demander_equipe("Zéènith FC")
    equipe_b = demander_equipe("Nova United")
    print()
    afficher_equipe(equipe_a)
    afficher_equipe(equipe_b)
    print()
    try:
        profil = passe_1_scout(equipe_a, equipe_b)
        print(couleur("  SCOUT ✔ profils générés", "vert"))
        verdict = passe_2_oracle(profil, equipe_a, equipe_b)
        print(couleur("  ORACLE ✔ verdict rendu", "vert"))
        print()
        afficher_resultat(equipe_a, equipe_b, profil, verdict)
    except requests.RequestException as exc:
        print(couleur(f"Erreur API ({exc}). Relance avec une clé valide ou lance sans clé pour le mode démo.", "rouge"))
        sys.exit(1)


if __name__ == "__main__":
    main()

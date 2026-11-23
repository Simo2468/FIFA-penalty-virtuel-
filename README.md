# ⚽ FIFA Penalty Predictor Virtuel (2 passes IA)

Prédicteur de tirs au but **virtuel** avec **deux passes IA** branchées sur une clé API.

> ⚠️ Divertissement uniquement : c'est une simulation virtuelle. La « confiance 100 % » fait partie du show de la simulation — aucune IA ne peut réellement prédire le gagnant d'un vrai match à 100 %.

## Fonctionnement

| Passe | Nom | Rôle |
|-------|-----|------|
| 1 | **SCOUT** | Analyse les deux équipes virtuelles (tireurs, gardien, sang-froid) et génère des profils JSON |
| 2 | **ORACLE** | Tranche le verdict final : gagnant, score, moments décisifs, confiance 100 % (univers simulé) |

Si la passe 1 échoue ou renvoie du JSON invalide, un moteur local de secours prend le relais (le prédicteur ne tombe jamais en panne).

## Installation

```bash
cd fifa-penalty-predictor
pip install -r requirements.txt
cp .env.example .env
```

Puis éditez `.env` et mettez **votre clé API** dedans (ne la partagez jamais en message public) :

```
MISTRAL_API_KEY=votre_cle_api_ici
MISTRAL_BASE_URL=https://api.mistral.ai/v1
MISTRAL_MODEL=mistral-small-latest
```

Compatible avec tout endpoint type OpenAI (changez `MISTRAL_BASE_URL` / `MISTRAL_MODEL`).

## Utilisation

```bash
python main.py
```

- **Sans clé API** : mode démo automatique (equipes + verdict générés localement).
- **Avec clé API** : vous saisissez les deux équipes, les deux passes IA s'enchaînent et le gagnant s'affiche avec son score prédit.

## Exemple de sortie

```
  GAGNANT PRÉDIT : ZÉÈNITH FC
  Confiance : 100 %  (simulation virtuelle)
```

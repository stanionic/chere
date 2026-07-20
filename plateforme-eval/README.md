# Le Carnet — Plateforme d'enseignement en ligne

Prototype d'une plateforme d'évaluation avec correction automatique.
Les enseignants créent des questions (QCM, Vrai/Faux, réponse courte, numérique)
avec une clé de correction ; les étudiants répondent et sont notés instantanément.

## Contenu du zip

```
plateforme-eval/
├── schema.sql          # Schéma PostgreSQL complet (utilisateurs, cours, quiz, questions, soumissions)
├── dist/                # Build de production déjà compilé (prêt à héberger tel quel)
├── src/
│   ├── EvalPlatform.jsx # Application React (formulaire enseignant + quiz étudiant + moteur de correction)
│   ├── main.jsx
│   └── index.css
├── index.html
├── package.json
├── vite.config.js
├── tailwind.config.js
└── postcss.config.js
```

## Lancer en local (mode développement)

Prérequis : Node.js ≥ 18.

```bash
npm install
npm run dev
```

Puis ouvrez l'URL affichée (par défaut http://localhost:5173).

## Générer un build de production

```bash
npm run build
```

Le résultat est généré dans `dist/` — un dossier statique déployable tel quel
sur n'importe quel hébergeur (Netlify, Vercel, S3, Nginx…).
Le dossier `dist/` fourni dans ce zip a déjà été compilé et est prêt à l'emploi :
il suffit de servir son contenu avec n'importe quel serveur statique, par exemple :

```bash
npx serve dist
```

## Base de données

`schema.sql` contient le schéma PostgreSQL prêt à exécuter :

```bash
psql -U votre_utilisateur -d votre_base -f schema.sql
```

Il couvre les utilisateurs/rôles, cours, modules, quiz, questions
(avec `cle_correction` en JSONB adapté à chaque type de question),
et les soumissions/réponses des étudiants avec leur score.

## Prochaines étapes suggérées

- Brancher le moteur de correction React (`grade()` dans `EvalPlatform.jsx`)
  côté backend pour sécuriser la notation (ne jamais faire confiance au client)
- Ajouter l'authentification (JWT/OAuth2) et la persistance réelle via une API
- Étendre aux questions ouvertes notées par IA et aux exercices de code (sandbox)
  — voir le blueprint fourni précédemment pour le détail de ces phases

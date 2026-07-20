-- ============================================================
-- Schéma PostgreSQL — Plateforme d'enseignement en ligne
-- avec évaluation automatique
-- ============================================================

CREATE TYPE user_role AS ENUM ('admin', 'enseignant', 'etudiant');
CREATE TYPE question_type AS ENUM (
  'qcm_unique', 'qcm_multiple', 'vrai_faux',
  'reponse_courte', 'numerique', 'texte_a_trous',
  'dissertation', 'code'
);
CREATE TYPE correction_statut AS ENUM ('auto', 'en_attente_ia', 'revise_par_prof');

-- ---------- Utilisateurs ----------
CREATE TABLE users (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nom           VARCHAR(120) NOT NULL,
  email         VARCHAR(160) UNIQUE NOT NULL,
  mot_de_passe_hash TEXT NOT NULL,
  role          user_role NOT NULL DEFAULT 'etudiant',
  cree_le       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------- Cours & structure ----------
CREATE TABLE courses (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  titre         VARCHAR(200) NOT NULL,
  description   TEXT,
  enseignant_id UUID NOT NULL REFERENCES users(id),
  publie        BOOLEAN NOT NULL DEFAULT false,
  cree_le       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE modules (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  course_id   UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
  titre       VARCHAR(200) NOT NULL,
  ordre       INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE enrollments (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  course_id   UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
  etudiant_id UUID NOT NULL REFERENCES users(id),
  inscrit_le  TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (course_id, etudiant_id)
);

-- ---------- Quiz & questions ----------
CREATE TABLE quizzes (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  module_id        UUID NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
  titre            VARCHAR(200) NOT NULL,
  duree_minutes    INTEGER,
  tentatives_max   INTEGER DEFAULT 1,
  date_limite      TIMESTAMPTZ,
  publie           BOOLEAN NOT NULL DEFAULT false,
  cree_le          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE questions (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  quiz_id      UUID NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
  type         question_type NOT NULL,
  enonce       TEXT NOT NULL,
  points       NUMERIC(6,2) NOT NULL DEFAULT 1,
  ordre        INTEGER NOT NULL DEFAULT 0,
  -- clé de correction, structure dépendant du type (voir JSON ci-dessous)
  cle_correction JSONB NOT NULL,
  cree_le      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Exemples de contenu pour `cle_correction` selon le type :
--   qcm_unique     : {"bonne_option_id": "opt_2"}
--   qcm_multiple   : {"bonnes_options_ids": ["opt_1","opt_3"]}
--   vrai_faux      : {"reponse": true}
--   reponse_courte : {"reponses_acceptees": ["Paris","paris"], "tolerance_fuzzy": 0.85}
--   numerique      : {"valeur": 42.5, "tolerance": 0.1}
--   texte_a_trous  : {"blancs": [{"id":"b1","reponses":["mitochondrie"]}]}
--   dissertation   : {"grille": [{"critere":"clarté","points_max":5}, ...]}
--   code           : {"tests": [{"input":"...","output_attendu":"..."}], "langage":"python"}

CREATE TABLE answer_options (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  question_id  UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
  texte        TEXT NOT NULL,
  ordre        INTEGER NOT NULL DEFAULT 0
);

-- ---------- Soumissions & résultats ----------
CREATE TABLE submissions (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  quiz_id       UUID NOT NULL REFERENCES quizzes(id),
  etudiant_id   UUID NOT NULL REFERENCES users(id),
  tentative_num INTEGER NOT NULL DEFAULT 1,
  demarre_le    TIMESTAMPTZ NOT NULL DEFAULT now(),
  soumis_le     TIMESTAMPTZ,
  score_total   NUMERIC(6,2),
  score_max     NUMERIC(6,2)
);

CREATE TABLE submission_answers (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  submission_id   UUID NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
  question_id     UUID NOT NULL REFERENCES questions(id),
  reponse_donnee  JSONB NOT NULL,      -- ex: {"option_id":"opt_2"} ou {"texte":"..."} ou {"valeur":42}
  correcte        BOOLEAN,
  score_obtenu    NUMERIC(6,2),
  statut          correction_statut NOT NULL DEFAULT 'auto',
  justification_ia TEXT,               -- pour dissertation notée par IA
  corrige_le      TIMESTAMPTZ
);

-- ---------- Index utiles ----------
CREATE INDEX idx_questions_quiz     ON questions(quiz_id);
CREATE INDEX idx_submissions_quiz   ON submissions(quiz_id, etudiant_id);
CREATE INDEX idx_sub_answers_sub    ON submission_answers(submission_id);
CREATE INDEX idx_enrollments_course ON enrollments(course_id);

from flask import g, has_request_context, request


SUPPORTED_LOCALES = ("fr", "en")
DEFAULT_LOCALE = "fr"
LOCALE_COOKIE_NAME = "chere_locale"

COUNTRY_LOCALE_MAP = {
    "BE": "fr",
    "BF": "fr",
    "BI": "fr",
    "BJ": "fr",
    "CA": "fr",
    "CD": "fr",
    "CF": "fr",
    "CG": "fr",
    "CH": "fr",
    "CI": "fr",
    "CM": "fr",
    "DJ": "fr",
    "FR": "fr",
    "GA": "fr",
    "GN": "fr",
    "HT": "fr",
    "LU": "fr",
    "MC": "fr",
    "MG": "fr",
    "ML": "fr",
    "NE": "fr",
    "RW": "en",
    "SN": "fr",
    "TD": "fr",
    "TG": "fr",
}

MONTH_NAMES = {
    "fr": [
        "janv.",
        "fevr.",
        "mars",
        "avr.",
        "mai",
        "juin",
        "juil.",
        "aout",
        "sept.",
        "oct.",
        "nov.",
        "dec.",
    ],
    "en": [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ],
}

TRANSLATIONS = {
    "fr": {
        "base.meta_description": (
            "CHERE est une entreprise sociale internationale dediee a l'innovation, "
            "aux energies renouvelables et a l'action humanitaire a travers le monde."
        ),
        "base.og_description": (
            "Transformer le monde par l'innovation, les energies renouvelables "
            "et l'humanitaire."
        ),
        "navbar.about": "A propos",
        "navbar.innovation": "Innovation",
        "navbar.energy": "Energie",
        "navbar.humanitarian": "Humanitaire",
        "navbar.projects": "Projets",
        "navbar.events": "Evenements",
        "navbar.blog": "Blog",
        "navbar.contact": "Contact",
        "navbar.notifications": "Notifications",
        "navbar.toggle_theme": "Basculer le theme",
        "navbar.explore": "Explore CHERE",
        "footer.company_copy": (
            "Community • Humanity • Empowerment • Resources • Environment."
            "<br>Une entreprise sociale internationale au service de l'innovation, "
            "des energies renouvelables et de l'action humanitaire, partout dans le monde."
        ),
        "footer.navigation": "Navigation",
        "footer.about": "A propos",
        "footer.sectors": "Secteurs",
        "footer.projects": "Projets",
        "footer.partners": "Partenaires",
        "footer.pillars": "Piliers",
        "footer.innovation": "Innovation",
        "footer.energy": "Energie",
        "footer.humanitarian": "Humanitaire",
        "footer.blog": "Blog",
        "footer.newsletter": "Newsletter",
        "footer.newsletter_copy": "Recevez les dernieres actualites de CHERE dans le monde.",
        "footer.email_placeholder": "Votre email",
        "footer.rights": "Tous droits reserves.",
        "footer.impact": "Concu pour un impact mondial",
        "common.tba": "A determiner",
        "common.online": "En ligne",
        "common.no_limit": "Pas de limite",
        "common.to_be_announced": "A determiner",
        "common.error": "Erreur",
        "common.learn_more": "En savoir plus",
        "common.contact_team": "Contactez notre equipe",
        "common.contact_us": "Nous contacter",
        "common.join_us": "Rejoignez-nous",
        "common.explore_chere": "Explore CHERE",
        "common.view_all_events": "Voir tous les evenements",
        "common.upcoming": "A venir",
        "common.upcoming_events": "Prochains evenements",
        "common.close": "Fermer",
        "validation.required": "Ce champ est obligatoire.",
        "validation.invalid_email": "Veuillez saisir une adresse email valide.",
        "home.title": "Accueil",
        "home.hero_badge": "Une entreprise sociale internationale",
        "home.hero_title": (
            "Transformer le monde par l'innovation, l'energie et l'humanite."
        ),
        "home.hero_projects": "Nos projets",
        "home.hero_alt": "Reseau mondial CHERE",
        "home.reason": "Notre raison d'etre",
        "home.mvv": "Mission • Vision • Valeurs",
        "home.mission_title": "Mission",
        "home.mission_copy": (
            "Creer un impact durable a travers l'innovation, l'energie propre et la solidarite."
        ),
        "home.vision_title": "Vision",
        "home.vision_copy": (
            "Un monde connecte, resilient et equitable pour toutes les communautes."
        ),
        "home.values_title": "Valeurs",
        "home.values_copy": "Integrite, innovation, inclusion et impact mesurable.",
        "home.what_defines_us": "Ce qui nous definit",
        "home.three_pillars": "Les 3 piliers de CHERE",
        "home.discover_innovation": "Decouvrir l'Innovation",
        "home.discover_energy": "Decouvrir l'Energie",
        "home.discover_humanitarian": "Decouvrir l'Humanitaire",
        "home.intervention_areas": "Domaines d'intervention",
        "home.our_sectors": "Nos secteurs",
        "home.sector_fallback": (
            "Solutions durables et innovantes deployees a l'echelle mondiale."
        ),
        "home.global_presence": "Presence mondiale",
        "home.world_title": "CHERE intervient partout dans le monde",
        "home.coming": "Ce qui arrive",
        "home.coming_soon": "Coming Soon",
        "home.coming_fallback": (
            "Un nouveau projet CHERE en preparation, porteur d'impact durable."
        ),
        "home.trusted_by": "Ils nous font confiance",
        "home.partners_title": "Partenaires",
        "home.news": "Actualites",
        "home.blog_title": "Depuis le blog CHERE",
        "home.read_article": "Lire l'article",
        "home.blog_empty": (
            "Les articles seront bientot publies depuis l'espace d'administration."
        ),
        "home.final_cta_title": "Rejoignez le mouvement CHERE",
        "home.final_cta_copy": (
            "Investisseurs, gouvernements, ONG, entreprises ou particuliers, "
            "construisons ensemble un avenir durable."
        ),
        "home.popup_free": "Gratuit",
        "home.popup_session_comment": "Ne pas afficher si la fenetre a deja ete fermee",
        "home.popup_delay_comment": "Afficher apres 2 secondes",
        "about.title": "A propos",
        "about.eyebrow": "Qui sommes-nous",
        "about.heading": "A propos de CHERE",
        "about.lead": (
            "Community • Humanity • Empowerment • Resources • Environment, "
            "une entreprise sociale internationale qui agit sur tous les continents."
        ),
        "about.alt": "Communaute CHERE",
        "about.reach_title": "Portee mondiale",
        "about.reach_copy": (
            "Present sur tous les continents, au service des communautes."
        ),
        "about.innovation_copy": "Technologies de pointe au service du bien commun.",
        "about.clean_energy_title": "Energie propre",
        "about.clean_energy_copy": (
            "Des solutions energetiques renouvelables et accessibles."
        ),
        "about.solidarity_title": "Solidarite",
        "about.solidarity_copy": (
            "Une action humanitaire ancree dans la dignite humaine."
        ),
        "about.impact": "Notre impact",
        "about.in_numbers": "CHERE en chiffres",
        "about.team": "Notre equipe",
        "about.leadership": "Leadership",
        "services.title": "Nos secteurs",
        "services.eyebrow": "Domaines d'intervention",
        "services.heading": "Nos secteurs",
        "services.lead": (
            "CHERE agit dans des secteurs varies pour maximiser son impact a l'echelle mondiale."
        ),
        "services.alt": "Nos secteurs d'activite",
        "services.card_copy": (
            "Des solutions concretes et durables, pensees pour un impact mondial."
        ),
        "projects.title": "Projets",
        "projects.eyebrow": "Presence mondiale",
        "projects.heading": "Nos projets",
        "projects.lead": (
            "Decouvrez les projets deployes et a venir de CHERE, sur tous les continents."
        ),
        "projects.alt": "Projets CHERE dans le monde",
        "projects.empty": (
            "Les projets seront bientot publies depuis l'espace d'administration."
        ),
        "blog.title": "Blog",
        "blog.eyebrow": "Actualites & idees",
        "blog.heading": "Le blog CHERE",
        "blog.lead": (
            "Innovation, energies renouvelables et action humanitaire, nos dernieres histoires."
        ),
        "blog.alt": "Blog CHERE",
        "blog.empty": "Aucun article publie pour le moment.",
        "contact.title": "Contact",
        "contact.eyebrow": "Parlons-en",
        "contact.heading": "Contactez CHERE",
        "contact.lead": (
            "Une question, un projet, un partenariat ? Notre equipe internationale vous repond rapidement."
        ),
        "contact.alt": "Contactez CHERE",
        "contact.hq": "Siege international",
        "contact.hq_copy": "Bureaux repartis sur plusieurs continents",
        "contact.qr_copy": "Scannez pour ouvrir l'app CHERE sur mobile",
        "contact.send_message": "Envoyer le message",
        "contact.form.full_name": "Nom complet",
        "contact.form.full_name_placeholder": "Votre nom complet",
        "contact.form.email": "Email",
        "contact.form.email_placeholder": "votre@email.com",
        "contact.form.subject": "Sujet",
        "contact.form.subject_placeholder": "Sujet de votre message",
        "contact.form.body": "Message",
        "contact.form.body_placeholder": "Comment pouvons-nous vous aider ?",
        "contact.flash.message_sent": (
            "Merci ! Votre message a bien ete envoye a l'equipe CHERE."
        ),
        "contact.flash.newsletter_subscribed": (
            "Merci pour votre inscription a la newsletter CHERE !"
        ),
        "contact.flash.invalid_email": "Adresse email invalide.",
        "innovation.title": "Innovation",
        "innovation.pillar": "Pilier ndeg1",
        "innovation.lead": (
            "Nous mobilisons les technologies les plus avancees pour resoudre les defis mondiaux "
            "et creer des opportunites partout dans le monde."
        ),
        "innovation.alt": "Innovation technologique",
        "innovation.cta": "Envie de collaborer sur un projet d'innovation ?",
        "renewable.title": "Energies renouvelables",
        "renewable.pillar": "Pilier ndeg2",
        "renewable.lead": (
            "Nous accelerons la transition energetique mondiale avec des solutions propres, "
            "accessibles et durables."
        ),
        "renewable.alt": "Energies renouvelables",
        "renewable.cta": "Un projet energetique a financer ou deployer ?",
        "humanitarian.title": "Humanitaire",
        "humanitarian.pillar": "Pilier ndeg3",
        "humanitarian.lead": (
            "Nous repondons aux besoins essentiels des communautes vulnerables partout dans le monde, "
            "avec dignite et efficacite."
        ),
        "humanitarian.alt": "Action humanitaire",
        "humanitarian.cta": "Devenez partenaire ou benevole CHERE",
        "partners.title": "Partenaires",
        "partners.eyebrow": "Ensemble, plus loin",
        "partners.heading": "Nos partenaires",
        "partners.lead": (
            "CHERE collabore avec des institutions internationales, des ONG, des universites, "
            "des entreprises et des banques du monde entier."
        ),
        "partners.alt": "Partenaires CHERE",
        "partners.cta": "Devenir partenaire de CHERE",
        "events.badge.paid": "Payant",
        "events.badge.free": "Gratuit",
        "events.form.full_name": "Nom complet",
        "events.form.full_name_placeholder": "Votre nom complet",
        "events.form.email": "Email",
        "events.form.email_placeholder": "votre@email.com",
        "events.form.phone": "Numero de telephone",
        "events.form.phone_placeholder": "+250 7xx xxx xxx",
        "events.form.phone_format": "Format: +250XXXXXXXXX ou 07XXXXXXXX",
        "events.form.momo_number": "Numero MoMo",
        "events.form.momo_number_placeholder": "250 7xx xxx xxx",
        "events.form.momo_format": "Format: 250xxxxxxxxx ou 07xxxxxxxx",
        "events.index.title": "Evenements",
        "events.index.subtitle": "Decouvrez nos prochains evenements, ateliers et conferences.",
        "events.index.search_placeholder": "Rechercher un evenement...",
        "events.index.search": "Rechercher",
        "events.index.details": "Voir les details",
        "events.index.order_coffee": "Commander un cafe",
        "events.index.previous": "Precedent",
        "events.index.next": "Suivant",
        "events.index.no_search_results": (
            "Aucun evenement ne correspond a votre recherche pour {query}."
        ),
        "events.index.no_events": "Aucun evenement actuellement disponible. Consultez-nous plus tard!",
        "events.detail.order_coffee_now": "Commander un cafe maintenant",
        "events.detail.date": "Date",
        "events.detail.location": "Lieu",
        "events.detail.participants": "Participants",
        "events.detail.type": "Type",
        "events.detail.about": "A propos de cet evenement",
        "events.detail.related": "Autres evenements",
        "events.detail.no_related": "Aucun autre evenement similaire n'est disponible pour le moment.",
        "events.detail.you_are_registered": "Vous etes inscrit a cet evenement",
        "events.detail.view_registration": "Voir votre inscription",
        "events.detail.phone_hint": "Format: +250XXXXXXXXX ou 07XXXXXXXX",
        "events.detail.register_and_pay": "S'inscrire et payer",
        "events.detail.register_now": "S'inscrire maintenant",
        "events.detail.generic_error": "Une erreur est survenue",
        "events.detail.generic_retry_error": "Une erreur est survenue. Veuillez reessayer.",
        "events.detail.event_full": "Cet evenement est complet.",
        "events.detail.registration_closed": "Les inscriptions a cet evenement sont fermees.",
        "events.detail.practical_info": "Informations pratiques",
        "events.detail.start_date": "Date de debut",
        "events.detail.registration_deadline": "Limite d'inscription",
        "events.detail.reserved_spots": "Places reservees",
        "events.registered.confirmed_title": "Inscription confirmee!",
        "events.registered.confirmed_subtitle": "Merci pour votre inscription a cet evenement.",
        "events.registered.pending_title": "Inscription enregistree",
        "events.registered.pending_subtitle": (
            "Votre inscription est enregistree, mais elle n'est pas encore confirmee."
        ),
        "events.registered.summary": "Resume de votre inscription",
        "events.registered.event": "Evenement",
        "events.registered.status": "Statut",
        "events.registered.confirmed": "Confirme",
        "events.registered.pending_payment": "En attente de paiement",
        "events.registered.participant": "Participant",
        "events.registered.email": "Email",
        "events.registered.event_date": "Date de l'evenement",
        "events.registered.amount_paid": "Montant paye",
        "events.registered.payment_date": "Date de paiement",
        "events.registered.confirmed_short": "Confirme",
        "events.registered.next_steps": "Etapes suivantes",
        "events.registered.keep_info": "Conservez vos informations",
        "events.registered.keep_info_desc": (
            "Gardez cette page ou notez l'adresse email {email} utilisee pour l'inscription."
        ),
        "events.registered.show_details": "Presentez vos details d'inscription",
        "events.registered.show_details_desc": (
            "Votre nom complet et votre email peuvent etre demandes a l'accueil de l'evenement."
        ),
        "events.registered.arrive_early": "Arrivez en avance",
        "events.registered.arrive_early_desc": (
            "Presentez-vous 15 minutes avant le debut de l'evenement."
        ),
        "events.registered.faq": "Questions frequentes",
        "events.registered.edit_question": "Puis-je modifier mes informations?",
        "events.registered.edit_answer": (
            "Oui, vous pouvez modifier votre inscription en contactant notre equipe support "
            "avant la date de l'evenement."
        ),
        "events.registered.cancel_question": "Puis-je annuler mon inscription?",
        "events.registered.cancel_answer": (
            "Les annulations sont acceptees jusqu'a 48 heures avant l'evenement. "
            "Un remboursement sera traite selon nos conditions."
        ),
        "events.registered.where_question": "Ou se deroule l'evenement?",
        "events.registered.where_answer_prefix": "L'adresse exacte est:",
        "events.registered.where_answer_pending": (
            "Le lieu exact sera communique sur la page de l'evenement lorsqu'il sera confirme."
        ),
        "events.registered.other_events": "Voir d'autres evenements",
        "events.registered.back_home": "Retour a l'accueil",
        "events.payment.title": "Paiement avec MoMo",
        "events.payment.amount_to_pay": "Montant a payer:",
        "events.payment.phone_label": "Numero de telephone MoMo",
        "events.payment.phone_hint": "Format: 250XXXXXXXXX ou 07XXXXXXXX",
        "events.payment.pay_now": "Payer maintenant",
        "events.payment.how_momo": "Comment fonctionne MoMo?",
        "events.payment.step_1": "Entrez votre numero MoMo ci-dessus",
        "events.payment.step_2": "Cliquez sur \"Payer maintenant\"",
        "events.payment.step_3": "Vous recevrez un code PIN a approuver sur votre telephone",
        "events.payment.step_4": "Entrez le code pour confirmer le paiement",
        "events.payment.step_5": (
            "Votre inscription sera confirmee une fois le paiement valide"
        ),
        "events.payment.no_momo": "Je n'ai pas MoMo",
        "events.payment.no_momo_answer": (
            "Veuillez contacter notre equipe support pour d'autres options de paiement."
        ),
        "events.payment.support": "Support & Aide",
        "events.payment.support_answer": (
            "Pour toute assistance, contactez-nous a: {email}"
        ),
        "events.payment.processing": "Traitement...",
        "events.payment.in_progress": "Paiement en cours",
        "events.payment.verify_phone": (
            "Verification de votre paiement... Veuillez verifier votre telephone."
        ),
        "events.payment.payment_confirmed": "Paiement confirme!",
        "events.payment.redirecting": "Redirection...",
        "events.payment.payment_failed": "Le paiement a echoue",
        "events.routes.registration_closed": "Les inscriptions sont fermees",
        "events.routes.already_registered": "Vous etes deja inscrit a cet evenement",
        "events.routes.event_full": "L'evenement est complet",
        "events.routes.registration_confirmed": "Inscription confirmee!",
        "events.routes.registration_recorded": (
            "Inscription enregistree. Procedez au paiement."
        ),
        "events.routes.registration_error": "Erreur lors de l'inscription: {error}",
        "events.routes.payment_access_denied": "Acces au paiement refuse",
        "events.routes.free_event": "Cet evenement est gratuit",
        "events.routes.access_denied": "Acces refuse",
        "events.routes.free_event_short": "Evenement gratuit",
        "events.routes.invalid_phone": "Numero de telephone invalide",
        "events.routes.invalid_transaction": "Transaction invalide",
        "events.routes.payment_request_sent": (
            "Demande de paiement envoyee. Verifiez votre telephone."
        ),
        "events.routes.unknown_error": "Erreur inconnue",
        "events.routes.payment_error": "Erreur lors du paiement: {error}",
        "events.routes.payment_confirmed": "Paiement confirme!",
        "events.routes.payment_failed": "Le paiement a echoue. Veuillez reessayer.",
        "events.routes.payment_pending": "Paiement en attente...",
        "events.routes.verification_error": (
            "Erreur lors de la verification: {error}"
        ),
        "events.routes.participant_not_found": "Participant non trouve",
        "events.type.barista": "Barista",
        "events.type.conference": "Conference",
        "events.type.meetup": "Rencontre",
        "events.type.other": "Autre",
        "events.type.training": "Formation",
        "events.type.webinar": "Webinaire",
        "events.type.workshop": "Atelier",
    },
    "en": {
        "base.meta_description": (
            "CHERE is an international social enterprise dedicated to innovation, "
            "renewable energy, and humanitarian action around the world."
        ),
        "base.og_description": (
            "Transforming the world through innovation, renewable energy, and humanitarian action."
        ),
        "navbar.about": "About",
        "navbar.innovation": "Innovation",
        "navbar.energy": "Energy",
        "navbar.humanitarian": "Humanitarian",
        "navbar.projects": "Projects",
        "navbar.events": "Events",
        "navbar.blog": "Blog",
        "navbar.contact": "Contact",
        "navbar.notifications": "Notifications",
        "navbar.toggle_theme": "Toggle theme",
        "navbar.explore": "Explore CHERE",
        "footer.company_copy": (
            "Community • Humanity • Empowerment • Resources • Environment."
            "<br>An international social enterprise serving innovation, renewable energy, "
            "and humanitarian action across the world."
        ),
        "footer.navigation": "Navigation",
        "footer.about": "About",
        "footer.sectors": "Sectors",
        "footer.projects": "Projects",
        "footer.partners": "Partners",
        "footer.pillars": "Pillars",
        "footer.innovation": "Innovation",
        "footer.energy": "Energy",
        "footer.humanitarian": "Humanitarian",
        "footer.blog": "Blog",
        "footer.newsletter": "Newsletter",
        "footer.newsletter_copy": "Receive the latest CHERE updates from around the world.",
        "footer.email_placeholder": "Your email",
        "footer.rights": "All rights reserved.",
        "footer.impact": "Designed for global impact",
        "common.tba": "TBA",
        "common.online": "Online",
        "common.no_limit": "No limit",
        "common.to_be_announced": "TBA",
        "common.error": "Error",
        "common.learn_more": "Learn more",
        "common.contact_team": "Contact our team",
        "common.contact_us": "Contact us",
        "common.join_us": "Join us",
        "common.explore_chere": "Explore CHERE",
        "common.view_all_events": "View all events",
        "common.upcoming": "Coming up",
        "common.upcoming_events": "Upcoming events",
        "common.close": "Close",
        "validation.required": "This field is required.",
        "validation.invalid_email": "Please enter a valid email address.",
        "home.title": "Home",
        "home.hero_badge": "An international social enterprise",
        "home.hero_title": (
            "Transforming the world through innovation, energy, and humanity."
        ),
        "home.hero_projects": "Our projects",
        "home.hero_alt": "Global CHERE network",
        "home.reason": "Why we exist",
        "home.mvv": "Mission • Vision • Values",
        "home.mission_title": "Mission",
        "home.mission_copy": (
            "Creating lasting impact through innovation, clean energy, and solidarity."
        ),
        "home.vision_title": "Vision",
        "home.vision_copy": (
            "A connected, resilient, and fair world for every community."
        ),
        "home.values_title": "Values",
        "home.values_copy": "Integrity, innovation, inclusion, and measurable impact.",
        "home.what_defines_us": "What defines us",
        "home.three_pillars": "The 3 CHERE pillars",
        "home.discover_innovation": "Discover Innovation",
        "home.discover_energy": "Discover Energy",
        "home.discover_humanitarian": "Discover Humanitarian",
        "home.intervention_areas": "Areas of intervention",
        "home.our_sectors": "Our sectors",
        "home.sector_fallback": (
            "Sustainable and innovative solutions deployed at a global scale."
        ),
        "home.global_presence": "Global presence",
        "home.world_title": "CHERE acts across the world",
        "home.coming": "What is next",
        "home.coming_soon": "Coming soon",
        "home.coming_fallback": (
            "A new CHERE project is in preparation, designed for lasting impact."
        ),
        "home.trusted_by": "Trusted by",
        "home.partners_title": "Partners",
        "home.news": "News",
        "home.blog_title": "From the CHERE blog",
        "home.read_article": "Read article",
        "home.blog_empty": "Articles will be published soon from the admin area.",
        "home.final_cta_title": "Join the CHERE movement",
        "home.final_cta_copy": (
            "Investors, governments, NGOs, businesses, or individuals, let us build a sustainable future together."
        ),
        "home.popup_free": "Free",
        "home.popup_session_comment": "Do not show if already dismissed in this session",
        "home.popup_delay_comment": "Show after 2 seconds",
        "about.title": "About",
        "about.eyebrow": "Who we are",
        "about.heading": "About CHERE",
        "about.lead": (
            "Community • Humanity • Empowerment • Resources • Environment, "
            "an international social enterprise active on every continent."
        ),
        "about.alt": "CHERE community",
        "about.reach_title": "Global reach",
        "about.reach_copy": "Present on every continent, serving communities.",
        "about.innovation_copy": "Advanced technologies serving the common good.",
        "about.clean_energy_title": "Clean energy",
        "about.clean_energy_copy": (
            "Accessible and renewable energy solutions for more communities."
        ),
        "about.solidarity_title": "Solidarity",
        "about.solidarity_copy": (
            "Humanitarian action rooted in human dignity."
        ),
        "about.impact": "Our impact",
        "about.in_numbers": "CHERE in numbers",
        "about.team": "Our team",
        "about.leadership": "Leadership",
        "services.title": "Sectors",
        "services.eyebrow": "Areas of intervention",
        "services.heading": "Our sectors",
        "services.lead": (
            "CHERE works across diverse sectors to maximize impact worldwide."
        ),
        "services.alt": "Our sectors",
        "services.card_copy": (
            "Concrete and sustainable solutions designed for global impact."
        ),
        "projects.title": "Projects",
        "projects.eyebrow": "Global presence",
        "projects.heading": "Our projects",
        "projects.lead": (
            "Discover CHERE projects already deployed and those coming next across the world."
        ),
        "projects.alt": "CHERE projects worldwide",
        "projects.empty": "Projects will be published soon from the admin area.",
        "blog.title": "Blog",
        "blog.eyebrow": "News & ideas",
        "blog.heading": "The CHERE blog",
        "blog.lead": (
            "Innovation, renewable energy, and humanitarian action, our latest stories."
        ),
        "blog.alt": "CHERE blog",
        "blog.empty": "No articles have been published yet.",
        "contact.title": "Contact",
        "contact.eyebrow": "Let us talk",
        "contact.heading": "Contact CHERE",
        "contact.lead": (
            "A question, project, or partnership? Our international team responds quickly."
        ),
        "contact.alt": "Contact CHERE",
        "contact.hq": "International headquarters",
        "contact.hq_copy": "Offices distributed across several continents",
        "contact.qr_copy": "Scan to open the CHERE app on mobile",
        "contact.send_message": "Send message",
        "contact.form.full_name": "Full name",
        "contact.form.full_name_placeholder": "Your full name",
        "contact.form.email": "Email",
        "contact.form.email_placeholder": "your@email.com",
        "contact.form.subject": "Subject",
        "contact.form.subject_placeholder": "Message subject",
        "contact.form.body": "Message",
        "contact.form.body_placeholder": "How can we help you?",
        "contact.flash.message_sent": (
            "Thank you! Your message has been sent to the CHERE team."
        ),
        "contact.flash.newsletter_subscribed": (
            "Thank you for subscribing to the CHERE newsletter!"
        ),
        "contact.flash.invalid_email": "Invalid email address.",
        "innovation.title": "Innovation",
        "innovation.pillar": "Pillar no.1",
        "innovation.lead": (
            "We mobilize advanced technologies to solve global challenges "
            "and create opportunities around the world."
        ),
        "innovation.alt": "Technological innovation",
        "innovation.cta": "Want to collaborate on an innovation project?",
        "renewable.title": "Renewable energy",
        "renewable.pillar": "Pillar no.2",
        "renewable.lead": (
            "We accelerate the global energy transition with clean, accessible, and sustainable solutions."
        ),
        "renewable.alt": "Renewable energy",
        "renewable.cta": "Do you have an energy project to finance or deploy?",
        "humanitarian.title": "Humanitarian",
        "humanitarian.pillar": "Pillar no.3",
        "humanitarian.lead": (
            "We respond to the essential needs of vulnerable communities around the world "
            "with dignity and efficiency."
        ),
        "humanitarian.alt": "Humanitarian action",
        "humanitarian.cta": "Become a CHERE partner or volunteer",
        "partners.title": "Partners",
        "partners.eyebrow": "Further together",
        "partners.heading": "Our partners",
        "partners.lead": (
            "CHERE works with international institutions, NGOs, universities, "
            "companies, and banks around the world."
        ),
        "partners.alt": "CHERE partners",
        "partners.cta": "Become a CHERE partner",
        "events.badge.paid": "Paid",
        "events.badge.free": "Free",
        "events.form.full_name": "Full name",
        "events.form.full_name_placeholder": "Your full name",
        "events.form.email": "Email",
        "events.form.email_placeholder": "your@email.com",
        "events.form.phone": "Phone number",
        "events.form.phone_placeholder": "+250 7xx xxx xxx",
        "events.form.phone_format": "Format: +250XXXXXXXXX or 07XXXXXXXX",
        "events.form.momo_number": "MoMo number",
        "events.form.momo_number_placeholder": "250 7xx xxx xxx",
        "events.form.momo_format": "Format: 250xxxxxxxxx or 07xxxxxxxx",
        "events.index.title": "Events",
        "events.index.subtitle": "Discover our upcoming events, workshops, and conferences.",
        "events.index.search_placeholder": "Search for an event...",
        "events.index.search": "Search",
        "events.index.details": "View details",
        "events.index.order_coffee": "Order coffee",
        "events.index.previous": "Previous",
        "events.index.next": "Next",
        "events.index.no_search_results": "No events match your search for {query}.",
        "events.index.no_events": "No events are available right now. Please check back later!",
        "events.detail.order_coffee_now": "Order coffee now",
        "events.detail.date": "Date",
        "events.detail.location": "Location",
        "events.detail.participants": "Participants",
        "events.detail.type": "Type",
        "events.detail.about": "About this event",
        "events.detail.related": "Other events",
        "events.detail.no_related": "No other similar events are available right now.",
        "events.detail.you_are_registered": "You are registered for this event",
        "events.detail.view_registration": "View your registration",
        "events.detail.phone_hint": "Format: +250XXXXXXXXX or 07XXXXXXXX",
        "events.detail.register_and_pay": "Register and pay",
        "events.detail.register_now": "Register now",
        "events.detail.generic_error": "An error occurred",
        "events.detail.generic_retry_error": "An error occurred. Please try again.",
        "events.detail.event_full": "This event is full.",
        "events.detail.registration_closed": "Registration for this event is closed.",
        "events.detail.practical_info": "Practical information",
        "events.detail.start_date": "Start date",
        "events.detail.registration_deadline": "Registration deadline",
        "events.detail.reserved_spots": "Reserved spots",
        "events.registered.confirmed_title": "Registration confirmed!",
        "events.registered.confirmed_subtitle": "Thank you for registering for this event.",
        "events.registered.pending_title": "Registration recorded",
        "events.registered.pending_subtitle": (
            "Your registration has been recorded, but it is not confirmed yet."
        ),
        "events.registered.summary": "Your registration summary",
        "events.registered.event": "Event",
        "events.registered.status": "Status",
        "events.registered.confirmed": "Confirmed",
        "events.registered.pending_payment": "Waiting for payment",
        "events.registered.participant": "Participant",
        "events.registered.email": "Email",
        "events.registered.event_date": "Event date",
        "events.registered.amount_paid": "Amount paid",
        "events.registered.payment_date": "Payment date",
        "events.registered.confirmed_short": "Confirmed",
        "events.registered.next_steps": "Next steps",
        "events.registered.keep_info": "Keep your information",
        "events.registered.keep_info_desc": (
            "Keep this page open or note the email address {email} used for registration."
        ),
        "events.registered.show_details": "Present your registration details",
        "events.registered.show_details_desc": (
            "Your full name and email may be requested at the event welcome desk."
        ),
        "events.registered.arrive_early": "Arrive early",
        "events.registered.arrive_early_desc": "Please arrive 15 minutes before the event starts.",
        "events.registered.faq": "Frequently asked questions",
        "events.registered.edit_question": "Can I edit my information?",
        "events.registered.edit_answer": (
            "Yes, you can update your registration by contacting our support team "
            "before the event date."
        ),
        "events.registered.cancel_question": "Can I cancel my registration?",
        "events.registered.cancel_answer": (
            "Cancellations are accepted up to 48 hours before the event. "
            "A refund will be processed according to our policy."
        ),
        "events.registered.where_question": "Where does the event take place?",
        "events.registered.where_answer_prefix": "The exact address is:",
        "events.registered.where_answer_pending": (
            "The exact location will be shared on the event page once confirmed."
        ),
        "events.registered.other_events": "See other events",
        "events.registered.back_home": "Back to home",
        "events.payment.title": "Pay with MoMo",
        "events.payment.amount_to_pay": "Amount to pay:",
        "events.payment.phone_label": "MoMo phone number",
        "events.payment.phone_hint": "Format: 250XXXXXXXXX or 07XXXXXXXX",
        "events.payment.pay_now": "Pay now",
        "events.payment.how_momo": "How does MoMo work?",
        "events.payment.step_1": "Enter your MoMo number above",
        "events.payment.step_2": "Click \"Pay now\"",
        "events.payment.step_3": "You will receive a PIN approval request on your phone",
        "events.payment.step_4": "Enter the PIN to confirm the payment",
        "events.payment.step_5": "Your registration will be confirmed once payment is validated",
        "events.payment.no_momo": "I do not have MoMo",
        "events.payment.no_momo_answer": (
            "Please contact our support team for other payment options."
        ),
        "events.payment.support": "Support & Help",
        "events.payment.support_answer": "For assistance, contact us at: {email}",
        "events.payment.processing": "Processing...",
        "events.payment.in_progress": "Payment in progress",
        "events.payment.verify_phone": "Checking your payment... Please confirm on your phone.",
        "events.payment.payment_confirmed": "Payment confirmed!",
        "events.payment.redirecting": "Redirecting...",
        "events.payment.payment_failed": "Payment failed",
        "events.routes.registration_closed": "Registration is closed",
        "events.routes.already_registered": "You are already registered for this event",
        "events.routes.event_full": "The event is full",
        "events.routes.registration_confirmed": "Registration confirmed!",
        "events.routes.registration_recorded": "Registration recorded. Proceed to payment.",
        "events.routes.registration_error": "Error while registering: {error}",
        "events.routes.payment_access_denied": "Payment access denied",
        "events.routes.free_event": "This event is free",
        "events.routes.access_denied": "Access denied",
        "events.routes.free_event_short": "Free event",
        "events.routes.invalid_phone": "Invalid phone number",
        "events.routes.invalid_transaction": "Invalid transaction",
        "events.routes.payment_request_sent": "Payment request sent. Please check your phone.",
        "events.routes.unknown_error": "Unknown error",
        "events.routes.payment_error": "Error while processing payment: {error}",
        "events.routes.payment_confirmed": "Payment confirmed!",
        "events.routes.payment_failed": "Payment failed. Please try again.",
        "events.routes.payment_pending": "Payment pending...",
        "events.routes.verification_error": "Error while verifying payment: {error}",
        "events.routes.participant_not_found": "Participant not found",
        "events.type.barista": "Barista",
        "events.type.conference": "Conference",
        "events.type.meetup": "Meetup",
        "events.type.other": "Other",
        "events.type.training": "Training",
        "events.type.webinar": "Webinar",
        "events.type.workshop": "Workshop",
    },
}


def normalize_locale(value):
    if not value:
        return None
    locale = str(value).split(",")[0].split("-")[0].split("_")[0].strip().lower()
    return locale if locale in SUPPORTED_LOCALES else None


def get_country_code(req=None):
    req = req or request
    for header in ("CF-IPCountry", "X-Country-Code", "X-Appengine-Country"):
        value = req.headers.get(header)
        if value:
            return value.strip().upper()
    return None


def detect_locale(req=None, default_locale=DEFAULT_LOCALE):
    req = req or request

    explicit_locale = normalize_locale(req.args.get("lang"))
    if explicit_locale:
        return explicit_locale

    cookie_locale = normalize_locale(req.cookies.get(LOCALE_COOKIE_NAME))
    if cookie_locale:
        return cookie_locale

    accepted_languages = getattr(req, "accept_languages", None)
    if accepted_languages:
        for language, _quality in accepted_languages:
            accepted_locale = normalize_locale(language)
            if accepted_locale:
                return accepted_locale

    country_code = get_country_code(req)
    if country_code:
        return COUNTRY_LOCALE_MAP.get(country_code, "en")

    return default_locale


def get_locale(default_locale=DEFAULT_LOCALE):
    if has_request_context():
        current_locale = getattr(g, "current_locale", None)
        if current_locale:
            return current_locale
        return detect_locale(request, default_locale)
    return default_locale


def translate(key, locale=None, **kwargs):
    locale = normalize_locale(locale) or get_locale()
    catalog = TRANSLATIONS.get(locale, TRANSLATIONS[DEFAULT_LOCALE])
    fallback_catalog = TRANSLATIONS[DEFAULT_LOCALE]
    text = catalog.get(key, fallback_catalog.get(key, key))
    if kwargs:
        return text.format(**kwargs)
    return text


def format_date(value, locale=None, fallback_key="common.to_be_announced"):
    if not value:
        return translate(fallback_key, locale=locale)

    locale = normalize_locale(locale) or get_locale()
    months = MONTH_NAMES.get(locale, MONTH_NAMES[DEFAULT_LOCALE])
    month_name = months[value.month - 1]
    if locale == "en":
        return f"{month_name} {value.day:02d}, {value.year}"
    return f"{value.day:02d} {month_name} {value.year}"


def format_datetime(value, locale=None, fallback_key="common.to_be_announced"):
    if not value:
        return translate(fallback_key, locale=locale)

    locale = normalize_locale(locale) or get_locale()
    date_text = format_date(value, locale=locale, fallback_key=fallback_key)
    connector = "at" if locale == "en" else "a"
    return f"{date_text} {connector} {value.strftime('%H:%M')}"


def translate_event_type(value, locale=None):
    normalized = (value or "").strip().lower()
    if not normalized:
        return ""
    return translate(f"events.type.{normalized}", locale=locale)

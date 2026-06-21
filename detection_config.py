"""Configuración (editable) del tablero — versión simple y accesible.

Las definiciones de términos se fijan aquí, antes de ver resultados, y se muestran
en el panel de metodología para que cualquier lector pueda verificarlas.
"""

# --- grupos de difamación (booleano: sujeto Y término difamatorio) -----------
GROUPS = {
    "anti_ivan": {
        "label": "Difamación contra Cepeda",
        "color": "#E24B4A",
        "subject": r"cepeda|pacto\s*hist",
        "slur": r"guerriller|terror|asesin",
        "criterio": "Menciona a Iván Cepeda o al Pacto Histórico Y un término difamatorio "
                    "(guerrillero, terrorista, asesino).",
    },
    "anti_abe": {
        "label": "Difamación contra Abelardo",
        "color": "#EF9F27",
        "subject": r"abelardo|espriella",
        "slur": r"paramilitar|mafioso|asesin",
        "criterio": "Menciona a Abelardo de la Espriella Y un término difamatorio "
                    "(paramilitar, mafioso, asesino).",
    },
}

# --- hashtags difamatorios AFIRMATIVOS (el autor los etiqueta en su propio video)
# Se usan para identificar a las cuentas de la campaña sin confundirlas con la
# cobertura periodística (que menciona los términos sin afirmarlos).
SMEAR_HASHTAG = (r"(cepeda|ivancepeda|pactohist).*(guerriller|terror|asesin)|"
                 r"(guerriller|terror|asesin).*(cepeda|pacto)|fueracepedaguerrillero")

# --- hashtags de las campañas (para medir la co-ocurrencia) ------------------
CAMPAIGN = {
    "abelardo": {"label": "Campaña de Abelardo", "color": "#EF9F27",
                 "rx": r"firmesporlapatria|abelardopresidente|abelardodelaespriella|eltigreabelardo"},
    "petro": {"label": "Campaña de Petro", "color": "#378ADD",
              "rx": r"fuerzapetro|colombiahumana|petropresidente|pactohistorico|apoyoivancepeda"},
}

# --- hashtags de interés a destacar en el panel 1 (con su categoría) ---------
HASHTAGS_INTERES = {
    "cepedaguerrillero": "Difamación contra Cepeda",
    "fueracepedaguerrillero": "Difamación contra Cepeda",
    "cepedaterrorista": "Difamación contra Cepeda",
    "abelardopresidente": "Campaña de Abelardo",
    "abelardodelaespriella": "Campaña de Abelardo",
    "firmesporlapatria": "Campaña de Abelardo",
    "petropresidente": "Campaña de Petro",
    "fuerzapetro": "Campaña de Petro",
    "pactohistorico": "Campaña de Petro",
    "fueracepeda": "Otro (oposición, no difamatorio)",
}
CAT_COLORS = {
    "Difamación contra Cepeda": "#E24B4A",
    "Difamación contra Abelardo": "#EF9F27",
    "Campaña de Abelardo": "#F0997B",
    "Campaña de Petro": "#378ADD",
    "Otro (oposición, no difamatorio)": "#B4B2A9",
    "Otro": "#B4B2A9",
}

# --- textos (lenguaje sencillo, sin marco legal) -----------------------------
INTRO = ("Este tablero muestra, con datos de TikTok, cuánto se difama a cada candidato "
         "y con qué hashtags aparece esa difamación. No emite un veredicto: presenta la "
         "evidencia para que usted saque sus propias conclusiones.")

METODOLOGIA = (
    "Los datos se recolectaron de TikTok en dos pasos: primero una búsqueda inicial con "
    "los términos de interés y luego la descarga del historial reciente de videos de cada "
    "cuenta detectada. Una publicación se clasifica como «difamación» solo si menciona al "
    "candidato Y contiene un término difamatorio (los términos exactos se listan abajo y "
    "se pueden editar)."
)
LIMITACIONES = [
    "Se analizó lo que se pudo recolectar, no todo lo que existe en TikTok.",
    "No incluye comentarios ni mensajes privados.",
    "La coincidencia de hashtags muestra una asociación, no prueba intención ni "
    "organización por parte de ninguna campaña.",
]

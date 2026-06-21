"""Difamación contra Iván Cepeda en TikTok — tablero simple y accesible.

Tres paneles: (1) el conjunto de datos y los hashtags de interés en el tiempo,
(2) la co-ocurrencia que muestra que difamar a Cepeda es estructuralmente más
probable y va de la mano de la campaña de Abelardo, (3) cómo se construyó.

Ejecutar:  streamlit run dashboard/app.py
"""
from __future__ import annotations

import sys
import tempfile
from itertools import combinations
from pathlib import Path

import networkx as nx
import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

sys.path.insert(0, str(Path(__file__).resolve().parent))  # → config
sys.path.insert(0, str(Path(__file__).resolve().parent))          # → detection_config
import config
import detection_config as DC

st.set_page_config(page_title="Difamación contra Cepeda · TikTok", layout="wide")
T0 = pd.Timestamp("2025-11-01")


def fmt(n) -> str:
    n = float(n)
    for d, s in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(n) >= d:
            return f"{n/d:.1f}{s}"
    return f"{int(n):,}"


@st.cache_data
def load():
    p = pd.read_csv(config.PROCESSED / "posts_campaign.csv").fillna("")
    p["dt"] = pd.to_datetime(p["timestamp"], unit="s")
    for c in ["play_count", "digg_count", "share_count", "comment_count"]:
        p[c] = pd.to_numeric(p[c], errors="coerce").fillna(0)
    ht = pd.read_csv(config.PROCESSED / "hashtags.csv").fillna("")
    return p, ht


posts, hashtags = load()
# análisis restringido al periodo de campaña: desde el 1 de noviembre de 2025
posts = posts[posts["dt"] >= T0].reset_index(drop=True)
hashtags = hashtags[hashtags["video_id"].isin(set(posts["video_id"]))]
txt = posts["search_text"].astype(str).str.lower()

# editable terms (advanced; collapsed so it doesn't intimidate)
with st.sidebar.expander("Ajustes avanzados (términos)", expanded=False):
    iv_s = st.text_input("Cepeda · sujeto", DC.GROUPS["anti_ivan"]["subject"])
    iv_l = st.text_input("Cepeda · términos difamatorios", DC.GROUPS["anti_ivan"]["slur"])
    ab_s = st.text_input("Abelardo · sujeto", DC.GROUPS["anti_abe"]["subject"])
    ab_l = st.text_input("Abelardo · términos difamatorios", DC.GROUPS["anti_abe"]["slur"])

ivan_subj = txt.str.contains(iv_s, regex=True)
abe_subj = txt.str.contains(ab_s, regex=True)
anti_ivan = ivan_subj & txt.str.contains(iv_l, regex=True)
anti_abe = abe_subj & txt.str.contains(ab_l, regex=True)
pro_abe = txt.str.contains(DC.CAMPAIGN["abelardo"]["rx"], regex=True)
pro_pet = txt.str.contains(DC.CAMPAIGN["petro"]["rx"], regex=True)
RED, AMBER, BLUE = "#E24B4A", "#EF9F27", "#378ADD"


def since(fig, h=300):
    fig.update_xaxes(range=[T0, posts["dt"].max()])
    fig.update_layout(height=h, margin=dict(l=0, r=0, t=10, b=0), legend_title_text="")
    return fig


st.title("¿Se difama más a Cepeda? Evidencia desde TikTok")
st.caption(DC.INTRO)

p1, p2, p4, p3 = st.tabs(["1 · El conjunto de datos", "2 · La co-ocurrencia",
                          "3 · Quién origina y amplifica", "4 · Cómo se construyó"])

# ======================================================== PANEL 1
with p1:
    st.subheader("Qué hay en los datos")
    m = st.columns(4)
    m[0].metric("Publicaciones", fmt(len(posts)))
    m[1].metric("Cuentas", fmt(posts["username"].nunique()))
    m[2].metric("Reproducciones", fmt(posts["play_count"].sum()))
    m[3].metric("Periodo", f"{posts['dt'].min().date()} → {posts['dt'].max().date()}")

    st.subheader("Hashtags de interés — cuántas veces aparecen")
    rows = []
    hv = hashtags["hashtag"].value_counts()
    for tag, cat in DC.HASHTAGS_INTERES.items():
        rows.append({"hashtag": "#" + tag, "veces": int(hv.get(tag, 0)), "categoría": cat})
    hi = pd.DataFrame(rows).sort_values("veces")
    fig = px.bar(hi, x="veces", y="hashtag", color="categoría", orientation="h",
                 color_discrete_map=DC.CAT_COLORS)
    fig.update_layout(height=460, margin=dict(l=0, r=0, t=10, b=0), legend_title_text="",
                      legend=dict(orientation="h", y=-0.12))
    st.plotly_chart(fig, width="stretch")

    st.subheader("Desarrollo en el tiempo")
    st.caption("Publicaciones por semana que difaman a cada candidato (desde nov. 2025).")
    parts = []
    for mask, lab, col in [(anti_ivan, DC.GROUPS["anti_ivan"]["label"], RED),
                           (anti_abe, DC.GROUPS["anti_abe"]["label"], AMBER)]:
        s = posts[mask].set_index("dt").resample("W").size()
        parts.append(pd.DataFrame({"semana": s.index, "publicaciones": s.values, "grupo": lab}))
    ts = pd.concat(parts)
    st.plotly_chart(since(px.line(ts, x="semana", y="publicaciones", color="grupo",
                    color_discrete_map={DC.GROUPS["anti_ivan"]["label"]: RED,
                                        DC.GROUPS["anti_abe"]["label"]: AMBER})), width="stretch")

# ======================================================== PANEL 2
with p2:
    n_iv, n_ab = int(anti_ivan.sum()), int(anti_abe.sum())
    base_iv, base_ab = int(ivan_subj.sum()), int(abe_subj.sum())
    rate_iv = n_iv / max(base_iv, 1)
    rate_ab = n_ab / max(base_ab, 1)

    st.subheader("Difamar a Cepeda es estructuralmente más probable")
    c = st.columns(2)
    with c[0]:
        st.markdown(f"<div style='font-size:42px;font-weight:600;color:{RED}'>1 de cada {round(1/max(rate_iv,1e-9))}</div>"
                    f"publicaciones sobre <b>Cepeda</b> lo difama<br><span style='color:#888'>"
                    f"({n_iv} de {base_iv} · {100*rate_iv:.1f}%)</span>", unsafe_allow_html=True)
    with c[1]:
        st.markdown(f"<div style='font-size:42px;font-weight:600;color:{AMBER}'>1 de cada {round(1/max(rate_ab,1e-9))}</div>"
                    f"publicaciones sobre <b>Abelardo</b> lo difama<br><span style='color:#888'>"
                    f"({n_ab} de {base_ab} · {100*rate_ab:.1f}%)</span>", unsafe_allow_html=True)
    st.markdown(f"**La difamación contra Cepeda es ~{rate_iv/max(rate_ab,1e-9):.1f} veces más probable** "
                "que la difamación contra Abelardo, en proporción a cuánto se habla de cada uno.")
    rr = pd.DataFrame({"candidato": ["Cepeda", "Abelardo"], "tasa": [rate_iv, rate_ab]})
    fig = px.bar(rr, x="tasa", y="candidato", orientation="h", text="tasa",
                 color="candidato", color_discrete_map={"Cepeda": RED, "Abelardo": AMBER})
    fig.update_traces(texttemplate="%{text:.1%}", textposition="outside")
    fig.update_layout(height=200, showlegend=False, margin=dict(l=0, r=0, t=6, b=0),
                      xaxis_tickformat=".0%", xaxis_title="tasa de difamación", yaxis_title=None)
    st.plotly_chart(fig, width="stretch")

    st.divider()
    st.subheader("La difamación contra Cepeda va de la mano de la campaña de Abelardo")
    co_iv = int((anti_ivan & pro_abe).sum())
    co_ab = int((anti_abe & pro_pet).sum())
    c = st.columns(2)
    c[0].metric("Difamación a Cepeda CON hashtags de Abelardo",
                f"{100*co_iv/max(n_iv,1):.0f}%", f"{co_iv} de {n_iv} publicaciones")
    c[1].metric("Difamación a Abelardo CON hashtags de Petro",
                f"{100*co_ab/max(n_ab,1):.0f}%", f"{co_ab} de {n_ab} publicaciones")
    st.caption("La difamación contra Cepeda aparece junto a los hashtags de la campaña de "
               "Abelardo mucho más seguido que el caso inverso.")

    st.markdown("**Hashtags que acompañan a la difamación contra Cepeda**")
    vids = set(posts[anti_ivan]["video_id"])
    comp = hashtags[hashtags["video_id"].isin(vids)]["hashtag"].value_counts().head(12)

    def categoria(h):
        import re
        if re.search(DC.CAMPAIGN["abelardo"]["rx"], h):
            return "Campaña de Abelardo"
        if re.search(DC.CAMPAIGN["petro"]["rx"], h):
            return "Campaña de Petro"
        # difamatorio solo si contiene un término-insulto (no #fueracepeda)
        if re.search(r"guerriller|terror|asesin", h):
            return "Difamación contra Cepeda"
        return "Otro"
    cd = pd.DataFrame({"hashtag": ["#" + h for h in comp.index], "veces": comp.values})
    cd["categoría"] = [categoria(h) for h in comp.index]
    cd = cd.sort_values("veces")
    fig = px.bar(cd, x="veces", y="hashtag", color="categoría", orientation="h",
                 color_discrete_map={**DC.CAT_COLORS, "Otro": "#B4B2A9"})
    fig.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0), legend_title_text="",
                      legend=dict(orientation="h", y=-0.15))
    st.plotly_chart(fig, width="stretch")

    st.markdown("**Cómo se conectan los hashtags difamatorios con los de la campaña**")
    st.caption("🔴 difamación contra Cepeda · 🟠 campaña de Abelardo. Cada línea = aparecer "
               "en la misma publicación.")
    DEF = r"guerriller|terror|asesin"   # tags difamatorios (excluye #fueracepeda)
    ABE = DC.CAMPAIGN["abelardo"]["rx"]
    pairs = {}
    for _, grp in hashtags[hashtags["video_id"].isin(vids)].groupby("video_id"):
        tags = set(grp["hashtag"])
        import re
        d = [t for t in tags if re.search(DEF, t)]
        a = [t for t in tags if re.search(ABE, t)]
        for x, y in ((x, y) for x in d for y in a):
            pairs[(x, y)] = pairs.get((x, y), 0) + 1
    if pairs:
        freq = hashtags["hashtag"].value_counts()
        nodes = {x for x, _ in pairs} | {y for _, y in pairs}
        net = Network(height="420px", width="100%", bgcolor="#ffffff", font_color="#222",
                      cdn_resources="in_line")
        net.barnes_hut(gravity=-22000, spring_length=180)
        fmax = max((freq.get(n, 1) for n in nodes), default=1) or 1
        import re
        for n in nodes:
            isd = bool(re.search(DEF, n))
            net.add_node(n, label="#" + n, color=RED if isd else AMBER, shape="dot",
                         size=12 + 24 * (freq.get(n, 1) / fmax))
        for (x, y), w in pairs.items():
            net.add_edge(x, y, value=float(w))
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as fh:
            fh.write(net.generate_html()); path = fh.name
        components.html(Path(path).read_text(encoding="utf-8"), height=440)
    else:
        st.info("Sin co-ocurrencias suficientes con los términos actuales.")

# ======================================================== PANEL 3
with p3:
    st.subheader("Cómo se construyó este tablero")
    st.write(DC.METODOLOGIA)
    st.write(f"**Periodo observado:** {posts['dt'].min().date()} → {posts['dt'].max().date()} · "
             f"{len(posts):,} publicaciones · {posts['username'].nunique()} cuentas.")
    st.markdown("**Definiciones usadas** (editables en «Ajustes avanzados»)")
    for g in DC.GROUPS.values():
        st.markdown(f"- <span style='color:{g['color']}'>●</span> **{g['label']}** — {g['criterio']}",
                    unsafe_allow_html=True)
    st.markdown("**Límites de este análisis**")
    for l in DC.LIMITACIONES:
        st.markdown(f"- {l}")

# ======================================================== PANEL: actores
with p4:
    st.subheader("Quién origina y quién amplifica la difamación contra Cepeda")
    st.caption("Dos roles distintos: las cuentas que EMPEZARON a publicar la difamación "
               "(las primeras en el tiempo) y las que le dieron más ALCANCE (más "
               "reproducciones). Para identificar a las cuentas de la campaña usamos los "
               "hashtags difamatorios AFIRMATIVOS (#cepedaguerrillero, #cepedaterrorista, "
               "#cepedaasesino…) que el propio autor etiqueta — así se excluye la cobertura "
               "periodística que solo menciona los términos. Aparecer aquí significa que la "
               "cuenta publicó y etiquetó este contenido; no prueba coordinación ni intención.")

    import re as _re
    _smear = _re.compile(DC.SMEAR_HASHTAG, _re.I)
    smear_vids = set(hashtags[hashtags["hashtag"].apply(lambda h: bool(_smear.search(h)))]["video_id"])
    dfam = posts[posts["video_id"].isin(smear_vids)].copy()
    g = dfam.groupby("username").agg(
        publicaciones=("video_id", "count"),
        reproducciones=("play_count", "sum"),
        primera=("dt", "min"), ultima=("dt", "max")).reset_index()
    g["perfil"] = "https://www.tiktok.com/@" + g["username"]

    m = st.columns(3)
    m[0].metric("Cuentas con hashtags difamatorios", f"{len(g):,}")
    m[1].metric("Publicaciones con hashtag difamatorio", f"{int(g['publicaciones'].sum()):,}")
    m[2].metric("Reproducciones de esa difamación", fmt(g["reproducciones"].sum()))

    LINKCOL = {"perfil": st.column_config.LinkColumn("perfil", display_text="abrir")}

    st.divider()
    st.subheader("🌱 Originadores — las primeras cuentas en publicar la difamación")
    orig = g.sort_values("primera").head(12).copy()
    orig["primera publicación"] = orig["primera"].dt.strftime("%Y-%m-%d")
    orig["reproducciones"] = orig["reproducciones"].map(fmt)
    st.dataframe(orig[["username", "primera publicación", "publicaciones", "reproducciones", "perfil"]],
                 width="stretch", hide_index=True, column_config=LINKCOL)

    st.divider()
    st.subheader("📣 Amplificadores — las cuentas que le dieron más alcance")
    amp = g.sort_values("reproducciones", ascending=False).head(12).copy()
    fig = px.bar(amp.sort_values("reproducciones"), x="reproducciones", y="username",
                 orientation="h", text="reproducciones", color_discrete_sequence=[RED])
    fig.update_traces(texttemplate="%{text:.2s}", textposition="outside")
    fig.update_layout(height=420, margin=dict(l=0, r=0, t=10, b=0),
                      xaxis_title="reproducciones de sus publicaciones difamatorias", yaxis_title=None)
    st.plotly_chart(fig, width="stretch")
    amp_t = amp.copy()
    amp_t["reproducciones"] = amp_t["reproducciones"].map(fmt)
    st.dataframe(amp_t[["username", "reproducciones", "publicaciones", "perfil"]],
                 width="stretch", hide_index=True, column_config=LINKCOL)

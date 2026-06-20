"""Campaign-tracing dashboard — defamation campaign against Iván Cepeda.

Bilingual (Español / English). Three views:
  1. Dataset overview   — the complete crawl
  2. Campaign           — combined-term co-occurrence + key actors
  3. Hashtag network    — hashtag FLOW (diffusion of a chosen hashtag) + co-use network

Run:  streamlit run dashboard/app.py
"""
from __future__ import annotations

import re
import sys
import tempfile
from collections import Counter
from itertools import product
from pathlib import Path

import networkx as nx
import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config

st.set_page_config(page_title="Campaña Cepeda · TikTok", layout="wide")

TIMELINE_START = pd.Timestamp("2025-11-01")
ROLE_COLORS = {"origin": "#E24B4A", "amplifier": "#EF9F27",
               "spreader": "#378ADD", "target/other": "#888780"}
ROLE_ORDER = ["origin", "amplifier", "spreader", "target/other"]
ENGAGE = ["play_count", "digg_count", "share_count", "comment_count"]
SUBJECTS = {"Iván Cepeda": r"cepeda",
            "Pacto Histórico": r"pacto\s*hist[oó]rico|pactohistorico"}
CORE_SMEARS = {"guerrillero": r"guerriller", "FARC": r"\bfarc\b",
               "terrorista": r"terrorist|terror", "asesino": r"asesin"}
CAMP_TAG_RX = re.compile(r"cepeda|pacto|guerriller|\bfarc\b|terror|asesin|castrochav|"
                         r"narco|bandido|crimin|mamerto|abelardo|espriella|firmespor|"
                         r"fueracepeda|fuerapetro", re.I)
# defamation hashtags vs Abelardo-campaign hashtags (for the integration view)
DEF_TAG = re.compile(r"fueracepeda|cepeda.*(guerr|terror|farc|asesin|bandid|crimin)|"
                     r"(guerr|terror|farc|asesin)", re.I)
ABE_TAG = re.compile(r"abelardo|espriella|firmespor", re.I)

# --------------------------------------------------------------- translations
TR = {
"es": {
 "title": "Rastreo de la campaña de difamación contra Iván Cepeda",
 "subtitle": "Propagación de propaganda de derecha (guerrillero / FARC / terrorista / asesino…) "
             "y su vínculo con la campaña de Abelardo de la Espriella · línea de tiempo desde nov. 2025",
 "lang": "Idioma / Language",
 "tab1": "① Panorama de datos", "tab2": "② Campaña", "tab3": "③ Red de hashtags",
 "complete": "Conjunto de datos completo",
 "Posts": "Publicaciones", "Accounts": "Cuentas", "Views": "Reproducciones",
 "Likes": "Me gusta", "Comments": "Comentarios", "Shares": "Compartidos",
 "span": "Período {a} → {b} · 242 de 423 cuentas con historial completo de videos (extracción ~57%)",
 "posts_wk": "Publicaciones por semana", "views_wk": "Reproducciones por semana",
 "top_actors": "Cuentas más vistas del conjunto", "views_lbl": "reproducciones", "actor": "cuenta",
 "cooc_h": "Co-ocurrencia de términos combinados",
 "cooc_cap": "Publicaciones donde el sujeto Y un insulto (guerrillero / FARC / terrorista / "
             "asesin*) aparecen juntos, en texto + hashtags.",
 "cep_slur": "Iván Cepeda + insulto", "pac_slur": "Pacto Histórico + insulto",
 "either": "Cualquier encuadre", "both": "Ambos en una publicación",
 "slur": "insulto", "subject": "sujeto", "posts_n": "publicaciones",
 "fr_cep": "Cepeda + insulto", "fr_pac": "Pacto Histórico + insulto", "framing": "encuadre",
 "camp_reach_h": "Cuentas y alcance de la campaña",
 "camp_actors": "Cuentas de la campaña", "camp_views": "Reproducciones de la campaña",
 "abelardo": "Publicaciones ligadas a Abelardo",
 "top_tags": "Hashtags principales de la campaña", "count": "frecuencia",
 "key_actors": "Cuentas clave",
 "flow_h": "Flujo de un hashtag — cómo se difunde y quiénes lo impulsan",
 "flow_cap": "Elige un hashtag y observa su difusión en orden temporal. La ESTRELLA es la cuenta "
             "de origen (primera en usarlo); las flechas conectan cada cuenta con la cuenta previa "
             "de mayor alcance (árbol de difusión inferido, no influencia probada).",
 "pick_tag": "Hashtag", "reveal": "Mostrar las primeras N cuentas (orden temporal)",
 "origin_m": "Cuenta de origen", "adopters_m": "Cuentas que lo usaron", "timespan_m": "Período",
 "imp_actors": "Cuentas importantes (mayor alcance)", "first_use": "primer uso",
 "order": "orden", "reach": "alcance", "followers": "seguidores", "role": "rol",
 "integ_h": "La difamación es parte integral de la campaña de Abelardo",
 "integ_cap": "Los hashtags difamatorios contra Cepeda aparecen junto a los de la campaña de "
              "Abelardo de la Espriella en las mismas publicaciones y cuentas — no son fenómenos separados.",
 "m_both": "Publicaciones que combinan ambos", "m_pct_posts": "% difamatorias que promueven a Abelardo",
 "m_both_acc": "Cuentas que publican ambos", "m_pct_acc": "% de cuentas difamatorias pro-Abelardo",
 "cooc_net_cap": "Cada enlace une un hashtag difamatorio (rojo) con un hashtag de la campaña de "
                 "Abelardo (ámbar) que aparecen en la misma publicación. Grosor = nº de publicaciones.",
 "leg_def": "hashtag difamatorio", "leg_abe": "campaña de Abelardo",
 "top_pairs": "Principales co-ocurrencias",
 "pair_def": "hashtag difamatorio", "pair_abe": "hashtag de Abelardo", "pair_posts": "publicaciones",
 "net_h": "Red de co-uso de hashtags (estructura completa)",
 "node_size": "Tamaño del nodo", "min_shared": "Mín. hashtags compartidos",
 "node_color_role": "Color del nodo = rol", "nodes_links": "{n} cuentas · {e} enlaces (≥{w} hashtags compartidos)",
 "bridges": "Puentes (mayor intermediación)", "betweenness": "intermediación",
 "adopt_h": "Cómo se propagan los hashtags difamatorios (acumulado)",
 "cumposts": "publicaciones acumuladas",
 "origins_h": "Cuentas de origen — dónde empieza la narrativa",
 "no_edges": "Sin enlaces con este umbral — baja el control.",
 "roles": {"origin": "origen", "amplifier": "amplificador", "spreader": "difusor", "target/other": "objetivo/otro"},
 "cols": {"username": "cuenta", "role": "rol", "n_campaign_posts": "publicaciones",
          "seeder_score": "sembrados", "campaign_reach": "alcance", "diff_betweenness": "intermediación",
          "n_abelardo_posts": "pub. Abelardo", "fans": "seguidores", "community": "comunidad",
          "actor": "cuenta", "betw": "intermediación"},
},
"en": {
 "title": "Tracing the defamation campaign against Iván Cepeda",
 "subtitle": "Right-wing propaganda propagation (guerrillero / FARC / terrorista / asesino…) "
             "and its link to the Abelardo de la Espriella campaign · timeline from Nov 2025",
 "lang": "Idioma / Language",
 "tab1": "① Dataset overview", "tab2": "② Campaign", "tab3": "③ Hashtag network",
 "complete": "Complete dataset",
 "Posts": "Posts", "Accounts": "Accounts", "Views": "Views",
 "Likes": "Likes", "Comments": "Comments", "Shares": "Shares",
 "span": "Span {a} → {b} · 242 of 423 accounts have full video history (crawl ~57%)",
 "posts_wk": "Posts per week", "views_wk": "Views per week",
 "top_actors": "Most-viewed accounts in the dataset", "views_lbl": "views", "actor": "account",
 "cooc_h": "Combined-term co-occurrence",
 "cooc_cap": "Posts where the subject AND a slur (guerrillero / FARC / terrorista / asesin*) "
             "appear together, in caption + hashtags.",
 "cep_slur": "Iván Cepeda + slur", "pac_slur": "Pacto Histórico + slur",
 "either": "Either framing", "both": "Both in one post",
 "slur": "slur", "subject": "subject", "posts_n": "posts",
 "fr_cep": "Cepeda + slur", "fr_pac": "Pacto Histórico + slur", "framing": "framing",
 "camp_reach_h": "Campaign accounts & reach",
 "camp_actors": "Campaign accounts", "camp_views": "Campaign views",
 "abelardo": "Abelardo-linked posts",
 "top_tags": "Top campaign hashtags", "count": "count",
 "key_actors": "Key accounts",
 "flow_h": "Hashtag flow — how it spreads and who drives it",
 "flow_cap": "Pick a hashtag and watch it diffuse in time order. The STAR is the origin account "
             "(first to use it); arrows link each account to the highest-reach earlier adopter "
             "(inferred diffusion tree, not proven influence).",
 "pick_tag": "Hashtag", "reveal": "Show first N accounts (time order)",
 "origin_m": "Origin account", "adopters_m": "Accounts that used it", "timespan_m": "Time span",
 "imp_actors": "Important accounts (highest reach)", "first_use": "first use",
 "order": "order", "reach": "reach", "followers": "followers", "role": "role",
 "integ_h": "Defamation is an integral part of the Abelardo campaign",
 "integ_cap": "The anti-Cepeda smear hashtags appear alongside the Abelardo de la Espriella campaign "
              "hashtags in the same posts and accounts — they are not separate phenomena.",
 "m_both": "Posts combining both", "m_pct_posts": "% of defamation posts promoting Abelardo",
 "m_both_acc": "Accounts posting both", "m_pct_acc": "% of defamation accounts pro-Abelardo",
 "cooc_net_cap": "Each link joins a defamation hashtag (red) with an Abelardo campaign hashtag "
                 "(amber) appearing in the same post. Thickness = number of posts.",
 "leg_def": "defamation hashtag", "leg_abe": "Abelardo campaign",
 "top_pairs": "Top co-occurrences",
 "pair_def": "defamation hashtag", "pair_abe": "Abelardo hashtag", "pair_posts": "posts",
 "net_h": "Hashtag co-use network (full structure)",
 "node_size": "Node size", "min_shared": "Min shared hashtags",
 "node_color_role": "Node colour = role", "nodes_links": "{n} accounts · {e} links (≥{w} shared hashtags)",
 "bridges": "Bridges (top betweenness)", "betweenness": "betweenness",
 "adopt_h": "How the smear hashtags spread (cumulative)",
 "cumposts": "cumulative posts",
 "origins_h": "Origin accounts — where the narrative starts",
 "no_edges": "No links at this threshold — lower the control.",
 "roles": {"origin": "origin", "amplifier": "amplifier", "spreader": "spreader", "target/other": "target/other"},
 "cols": {"username": "account", "role": "role", "n_campaign_posts": "campaign posts",
          "seeder_score": "seeded", "campaign_reach": "reach", "diff_betweenness": "betweenness",
          "n_abelardo_posts": "Abelardo posts", "fans": "followers", "community": "community",
          "actor": "account", "betw": "betweenness"},
},
}


def fmt(n) -> str:
    n = float(n)
    for div, suf in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(n) >= div:
            return f"{n/div:.1f}{suf}"
    return f"{int(n):,}"


@st.cache_data
def load():
    posts = pd.read_csv(config.PROCESSED / "posts_campaign.csv")
    posts["dt"] = pd.to_datetime(posts["timestamp"], unit="s")
    for c in ENGAGE:
        posts[c] = pd.to_numeric(posts[c], errors="coerce").fillna(0)
    actors = pd.read_csv(config.PROCESSED / "actor_campaign.csv")
    ht = pd.read_csv(config.PROCESSED / "hashtags.csv")
    return posts, actors, ht


@st.cache_data
def load_hashtag_graph():
    fp = config.NETWORKS / "campaign_shared_hashtag.graphml"
    return nx.read_graphml(fp) if fp.exists() else nx.Graph()


@st.cache_data
def cooccurrence():
    p = pd.read_csv(config.PROCESSED / "posts_campaign.csv").fillna("")
    p["dt"] = pd.to_datetime(p["timestamp"], unit="s")
    t = p["search_text"].astype(str).str.lower()
    any_slur = t.str.contains("|".join(CORE_SMEARS.values()), regex=True)
    mat = pd.DataFrame(index=list(SUBJECTS), columns=list(CORE_SMEARS), dtype=int)
    for sn, srx in SUBJECTS.items():
        hs = t.str.contains(srx, regex=True)
        for mn, mrx in CORE_SMEARS.items():
            mat.loc[sn, mn] = int((hs & t.str.contains(mrx, regex=True)).sum())
        p[sn] = hs & any_slur
    return mat, p[["dt"] + list(SUBJECTS)]


posts, actors, ht = load()
camp = posts[posts["is_campaign"]].copy()
campaign_vids = set(camp["video_id"])
max_dt = posts["dt"].max()
REACH = dict(zip(actors["username"], pd.to_numeric(actors["campaign_reach"], errors="coerce").fillna(0)))
FANS = dict(zip(actors["username"], pd.to_numeric(actors["fans"], errors="coerce").fillna(0)))
ROLE = dict(zip(actors["username"], actors["role"]))
# campaign hashtag → ordered adopters (first use per account)
cht = ht[ht["video_id"].isin(campaign_vids)].merge(camp[["video_id", "dt"]], on="video_id")

# language selector
lang = "es" if st.sidebar.radio(TR["es"]["lang"], ["Español", "English"], index=0) == "Español" else "en"
T = TR[lang]
def tr(k): return T.get(k, k)
def col_rename(df): return df.rename(columns=T["cols"])
def role_es(df, c="role"):
    if c in df.columns:
        df = df.copy(); df[c] = df[c].map(T["roles"]).fillna(df[c])
    return df


def since_2025(fig):
    fig.update_xaxes(range=[TIMELINE_START, max_dt])
    fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0))
    return fig


st.title(tr("title"))
st.caption(tr("subtitle"))
t1, t2, t3 = st.tabs([tr("tab1"), tr("tab2"), tr("tab3")])

# ====================================================================== T1
with t1:
    st.subheader(tr("complete"))
    m = st.columns(6)
    for col, key, val in zip(m, ["Posts", "Accounts", "Views", "Likes", "Comments", "Shares"],
                             [len(posts), posts["username"].nunique(), posts["play_count"].sum(),
                              posts["digg_count"].sum(), posts["comment_count"].sum(),
                              posts["share_count"].sum()]):
        col.metric(tr(key), fmt(val))
    st.caption(T["span"].format(a=posts["dt"].min().date(), b=posts["dt"].max().date()))

    a, b = st.columns(2)
    with a:
        st.subheader(tr("posts_wk"))
        wk = posts.set_index("dt").resample("W").size().rename("y").reset_index()
        st.plotly_chart(since_2025(px.area(wk, x="dt", y="y")), width="stretch")
    with b:
        st.subheader(tr("views_wk"))
        vw = posts.set_index("dt")["play_count"].resample("W").sum().rename("y").reset_index()
        st.plotly_chart(since_2025(px.area(vw, x="dt", y="y", color_discrete_sequence=["#00CC96"])),
                        width="stretch")

    st.subheader(tr("top_actors"))
    top = posts.groupby("username")["play_count"].sum().sort_values(ascending=False).head(15).reset_index()
    top.columns = [tr("actor"), tr("views_lbl")]
    st.plotly_chart(px.bar(top, x=tr("views_lbl"), y=tr("actor"), orientation="h").update_layout(
        height=420, margin=dict(l=0, r=0, t=10, b=0), yaxis=dict(autorange="reversed")), width="stretch")

# ====================================================================== T2
with t2:
    mat, flags = cooccurrence()
    cep_n = int(flags["Iván Cepeda"].sum()); pac_n = int(flags["Pacto Histórico"].sum())
    either_n = int((flags["Iván Cepeda"] | flags["Pacto Histórico"]).sum())
    both_n = int((flags["Iván Cepeda"] & flags["Pacto Histórico"]).sum())

    st.subheader(tr("cooc_h"))
    st.caption(tr("cooc_cap"))
    m = st.columns(4)
    m[0].metric(tr("cep_slur"), fmt(cep_n)); m[1].metric(tr("pac_slur"), fmt(pac_n))
    m[2].metric(tr("either"), fmt(either_n)); m[3].metric(tr("both"), fmt(both_n))

    a, b = st.columns(2)
    with a:
        fig = px.imshow(mat, text_auto=True, color_continuous_scale="Reds",
                        labels=dict(x=tr("slur"), y=tr("subject"), color=tr("posts_n")), aspect="auto")
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), coloraxis_showscale=False)
        st.plotly_chart(fig, width="stretch")
    with b:
        wk = flags.set_index("dt").resample("W")[list(SUBJECTS)].sum().rename(
            columns={"Iván Cepeda": tr("fr_cep"), "Pacto Histórico": tr("fr_pac")}).reset_index()
        wkl = wk.melt("dt", var_name=tr("framing"), value_name=tr("posts_n"))
        st.plotly_chart(since_2025(px.line(wkl, x="dt", y=tr("posts_n"), color=tr("framing"),
                        color_discrete_map={tr("fr_cep"): "#E24B4A", tr("fr_pac"): "#EF9F27"})),
                        width="stretch")

    st.divider()
    st.subheader(tr("camp_reach_h"))
    m = st.columns(3)
    m[0].metric(tr("camp_actors"), fmt(camp["username"].nunique()))
    m[1].metric(tr("camp_views"), fmt(camp["play_count"].sum()))
    m[2].metric(tr("abelardo"), fmt(posts["is_abelardo"].sum()))

    st.subheader(tr("top_tags"))
    th = ht[ht["video_id"].isin(campaign_vids)]["hashtag"].value_counts().head(12).reset_index()
    th.columns = ["hashtag", tr("count")]
    st.plotly_chart(px.bar(th, x=tr("count"), y="hashtag", orientation="h").update_layout(
        height=340, margin=dict(l=0, r=0, t=10, b=0), yaxis=dict(autorange="reversed")), width="stretch")

    st.subheader(tr("key_actors"))
    cols = ["username", "role", "n_campaign_posts", "seeder_score", "campaign_reach",
            "n_abelardo_posts", "fans", "community"]
    view = actors[actors["n_campaign_posts"] > 0][cols].sort_values("campaign_reach", ascending=False)
    st.dataframe(col_rename(role_es(view)), width="stretch", height=340)

# ====================================================================== T3
with t3:
    # ---- defamation ↔ Abelardo integration (co-occurrence) ----
    st.subheader(tr("integ_h"))
    st.caption(tr("integ_cap"))
    both_posts = int((posts["is_campaign"] & posts["is_abelardo"]).sum())
    n_def = int(posts["is_campaign"].sum())
    def_acc = set(camp["username"])
    abe_acc = set(posts[posts["is_abelardo"]]["username"])
    m = st.columns(4)
    m[0].metric(tr("m_both"), fmt(both_posts))
    m[1].metric(tr("m_pct_posts"), f"{100 * both_posts / max(n_def, 1):.0f}%")
    m[2].metric(tr("m_both_acc"), fmt(len(def_acc & abe_acc)))
    m[3].metric(tr("m_pct_acc"), f"{100 * len(def_acc & abe_acc) / max(len(def_acc), 1):.0f}%")

    pairs = Counter()
    for tags in ht.groupby("video_id")["hashtag"].apply(set):
        d = {t for t in tags if DEF_TAG.search(t)}
        a = {t for t in tags if ABE_TAG.search(t)}
        for x, y in product(d, a):
            pairs[(x, y)] += 1

    st.caption(tr("cooc_net_cap"))
    st.markdown(f"<span style='color:#E24B4A'>● {tr('leg_def')}</span> &nbsp;&nbsp; "
                f"<span style='color:#EF9F27'>● {tr('leg_abe')}</span>", unsafe_allow_html=True)
    left, right = st.columns([3, 2])
    with left:
        if pairs:
            freq = ht["hashtag"].value_counts()
            nodes = {x for x, _ in pairs} | {y for _, y in pairs}
            fmax = max((freq.get(n, 1) for n in nodes), default=1) or 1
            net = Network(height="520px", width="100%", bgcolor="#ffffff",
                          font_color="#222", cdn_resources="in_line")
            net.barnes_hut(gravity=-24000, spring_length=180)
            for n in nodes:
                is_def = bool(DEF_TAG.search(n))
                net.add_node(n, label="#" + n, shape="dot",
                             color="#E24B4A" if is_def else "#EF9F27",
                             size=12 + 26 * (freq.get(n, 1) / fmax),
                             title=f"#{n} · {int(freq.get(n, 0))} {tr('posts_n')}")
            for (x, y), w in pairs.items():
                net.add_edge(x, y, value=float(w), title=f"{w} {tr('posts_n')}")
            with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as fh:
                fh.write(net.generate_html()); path = fh.name
            components.html(Path(path).read_text(encoding="utf-8"), height=540)
        else:
            st.info(tr("no_edges"))
    with right:
        st.markdown("**" + tr("top_pairs") + "**")
        tp = pd.DataFrame([{"a": "#" + d, "b": "#" + a, "c": c}
                           for (d, a), c in pairs.most_common(15)])
        if not tp.empty:
            tp.columns = [tr("pair_def"), tr("pair_abe"), tr("pair_posts")]
        st.dataframe(tp, width="stretch", hide_index=True, height=440)

    st.divider()
    # ---- full co-use network ----
    st.subheader(tr("net_h"))
    g = load_hashtag_graph()
    cc = st.columns([1, 1, 2])
    size_by = cc[0].selectbox(tr("node_size"), ["graph_betweenness", "campaign_reach", "fans"])
    weights = [d.get("weight", 1) for *_, d in g.edges(data=True)] or [1]
    min_w = cc[1].slider(tr("min_shared"), 1, int(max(2, max(weights))), 2)
    st.markdown(tr("node_color_role") + " · " + " · ".join(
        f"<span style='color:{ROLE_COLORS[r]}'>● {T['roles'][r]}</span>" for r in ROLE_ORDER),
        unsafe_allow_html=True)
    edges = [(a, b, d) for a, b, d in g.edges(data=True) if d.get("weight", 1) >= min_w]
    sub = nx.Graph(); sub.add_edges_from(edges)
    st.caption(T["nodes_links"].format(n=sub.number_of_nodes(), e=len(edges), w=min_w))
    left, right = st.columns([3, 1])
    with left:
        if edges:
            vals = [g.nodes[n].get(size_by, 0) or 0 for n in sub.nodes]
            vmax = max(vals) or 1
            net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="#222",
                          cdn_resources="in_line")
            net.barnes_hut(gravity=-14000, spring_length=150)
            for n in sub.nodes:
                a = g.nodes[n]
                net.add_node(n, label=n, color=ROLE_COLORS.get(a.get("role", "target/other")),
                             size=8 + 30 * ((a.get(size_by, 0) or 0) / vmax),
                             title=(f"@{n} · {T['roles'].get(a.get('role','spreader'))}\n"
                                    f"{tr('reach')}: {fmt(a.get('campaign_reach',0))} · "
                                    f"{tr('betweenness')}: {a.get('graph_betweenness',0):.4f}"))
            for x, y, d in edges:
                net.add_edge(x, y, value=float(d.get("weight", 1)))
            with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as fh:
                fh.write(net.generate_html()); path = fh.name
            components.html(Path(path).read_text(encoding="utf-8"), height=620)
        else:
            st.info(tr("no_edges"))
    with right:
        st.markdown("**" + tr("bridges") + "**")
        bet = pd.DataFrame([(n, round(d.get("graph_betweenness", 0), 4)) for n, d in g.nodes(data=True)],
                           columns=["actor", "betw"]).sort_values("betw", ascending=False).head(12)
        st.dataframe(col_rename(bet), width="stretch", hide_index=True, height=300)

    st.subheader(tr("adopt_h"))
    top_tags = cht["hashtag"].value_counts().head(6).index.tolist()
    curves = []
    for h in top_tags:
        s = cht[cht["hashtag"] == h].sort_values("dt").assign(n=1)
        s["n"] = s["n"].cumsum()
        curves.append(s[["dt", "n"]].assign(hashtag=h))
    if curves:
        cdf = pd.concat(curves)
        st.plotly_chart(since_2025(px.line(cdf, x="dt", y="n", color="hashtag",
                        labels={"n": tr("cumposts")})), width="stretch")

    st.subheader(tr("origins_h"))
    oc = actors[actors["role"] == "origin"][
        ["username", "n_campaign_posts", "seeder_score", "campaign_reach",
         "n_abelardo_posts", "fans", "community"]].head(15)
    st.dataframe(col_rename(oc), width="stretch", hide_index=True)

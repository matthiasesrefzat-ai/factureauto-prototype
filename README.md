import streamlit as st
import pandas as pd
from fpdf import FPDF
import zipfile
import io
from datetime import datetime
import re
import base64
import json
import requests
import os

st.set_page_config(page_title="FactureAuto", page_icon="⚡", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Instrument+Sans:wght@300;400;500;600&display=swap');
:root{--bg:#0d0d0d;--s:#161616;--s2:#1e1e1e;--b:#2a2a2a;--a:#c8f135;--a2:#35f1c8;--t:#f0f0f0;--m:#6b6b6b;}
html,body,[class*="css"]{font-family:'Instrument Sans',sans-serif;color:var(--t);}
.stApp{background:var(--bg);background-image:radial-gradient(ellipse 60% 40% at 10% 0%,rgba(200,241,53,.07) 0%,transparent 60%),radial-gradient(ellipse 40% 30% at 90% 100%,rgba(53,241,200,.07) 0%,transparent 60%);}
.block-container{padding-top:2.5rem!important;padding-bottom:4rem!important;max-width:700px!important;}
.hdr{margin-bottom:2rem;}
.hdr-tag{font-size:.62rem;letter-spacing:4px;text-transform:uppercase;color:var(--m);margin-bottom:.4rem;}
.hdr-title{font-family:'Syne',sans-serif;font-size:3rem;font-weight:800;line-height:1;color:var(--t);}
.hdr-title span{color:var(--a);}
.hdr-sub{font-size:.88rem;color:var(--m);margin-top:.5rem;font-weight:300;}
.hdr-line{height:1px;background:linear-gradient(90deg,var(--a) 0%,transparent 70%);margin-top:1.5rem;}
.stats{display:flex;gap:.8rem;margin:1.2rem 0;}
.stat{flex:1;background:var(--s2);border:1px solid var(--b);border-radius:12px;padding:1rem;text-align:center;}
.stat-n{font-family:'Syne',sans-serif;font-size:2rem;font-weight:700;color:var(--a);line-height:1;}
.stat-l{font-size:.62rem;letter-spacing:2px;text-transform:uppercase;color:var(--m);margin-top:3px;}
.stTabs [data-baseweb="tab-list"]{background:var(--s)!important;border:1px solid var(--b)!important;border-radius:12px!important;padding:4px!important;gap:2px!important;}
.stTabs [data-baseweb="tab"]{font-family:'Instrument Sans',sans-serif!important;font-size:.78rem!important;font-weight:500!important;color:var(--m)!important;border-radius:8px!important;padding:.45rem .9rem!important;}
.stTabs [aria-selected="true"]{background:var(--a)!important;color:#0d0d0d!important;font-weight:600!important;}
.stTabs [data-baseweb="tab-panel"]{padding-top:1.2rem!important;}
.stTextInput>div>div>input,.stTextArea>div>div>textarea{background:var(--s2)!important;border:1px solid var(--b)!important;border-radius:10px!important;color:var(--t)!important;font-family:'Instrument Sans',sans-serif!important;}
.stTextInput>div>div>input:focus,.stTextArea>div>div>textarea:focus{border-color:var(--a)!important;box-shadow:0 0 0 2px rgba(200,241,53,.15)!important;}
.stButton>button{font-family:'Instrument Sans',sans-serif!important;font-weight:600!important;border-radius:10px!important;border:none!important;padding:.65rem 1.2rem!important;width:100%!important;transition:all .15s!important;}
.stButton>button[kind="primary"]{background:var(--a)!important;color:#0d0d0d!important;}
.stButton>button[kind="primary"]:hover{background:#b8e020!important;transform:translateY(-1px);}
.stButton>button[kind="secondary"]{background:var(--s2)!important;color:var(--t)!important;border:1px solid var(--b)!important;}
.stButton>button[kind="secondary"]:hover{border-color:var(--a)!important;color:var(--a)!important;}
.stDownloadButton>button{font-family:'Instrument Sans',sans-serif!important;font-weight:600!important;border-radius:10px!important;background:var(--a2)!important;color:#0d0d0d!important;width:100%!important;padding:.8rem!important;border:none!important;}
[data-testid="stFileUploader"]{background:var(--s2)!important;border:2px dashed var(--b)!important;border-radius:14px!important;}
[data-testid="stFileUploader"]:hover{border-color:var(--a)!important;}
.stCheckbox{background:var(--s)!important;border:1px solid var(--b)!important;border-radius:10px!important;padding:.5rem .8rem!important;margin-bottom:.3rem!important;}
.stCheckbox label{color:var(--t)!important;}
.stSuccess{background:rgba(200,241,53,.08)!important;border:1px solid rgba(200,241,53,.2)!important;border-radius:10px!important;}
.stWarning{background:rgba(255,180,0,.08)!important;border:1px solid rgba(255,180,0,.2)!important;border-radius:10px!important;}
.stError{border-radius:10px!important;}
.stInfo{background:var(--s2)!important;border:1px solid var(--b)!important;border-radius:10px!important;}
.streamlit-expanderHeader{background:var(--s)!important;border:1px solid var(--b)!important;border-radius:10px!important;color:var(--t)!important;}
hr{border:none!important;border-top:1px solid var(--b)!important;margin:1.5rem 0!important;}
.stCaption{color:var(--m)!important;font-size:.75rem!important;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hdr">
  <div class="hdr-tag">Outil de facturation automatique</div>
  <div class="hdr-title">Facture<span>Auto</span></div>
  <div class="hdr-sub">Relevés bancaires → Factures PDF professionnelles</div>
  <div class="hdr-line"></div>
</div>
""", unsafe_allow_html=True)

with st.expander("⚙️  Paramètres société", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        company_name    = st.text_input("Nom de la société", "Ma Société SARL")
        company_siret   = st.text_input("SIRET", "123 456 789 00012")
    with c2:
        company_address = st.text_area("Adresse", "12 rue des Entrepreneurs\n75001 Paris", height=90)
        tva_rate        = st.select_slider("TVA (%)", options=[0,5,10,20], value=20)

# Clé API depuis secrets Streamlit Cloud ou saisie manuelle
api_key = st.secrets.get("ANTHROPIC_API_KEY", "") if hasattr(st, "secrets") else ""
if not api_key:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")

st.markdown("<hr>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# Parsers
# ══════════════════════════════════════════════════════════════════

def extraire_client(texte):
    t = str(texte).upper()
    t = re.sub(r'\b(VIR(EMENT)?|PRLV|SEPA|RECU|CARTE|CB|RETRAIT|AVOIR|REMISE|CHEQUE|CHQ|PAIEMENT|REGLEMENT|ABONNEMENT|DOC|TXT|PID)\b',' ',t)
    t = re.sub(r'\d',' ',t)
    m = re.search(r'([A-Z][A-Z\s\-]{3,})',t)
    return m.group(1).strip()[:40] if m else "Client inconnu"

def parse_montant(s):
    s = str(s).replace('\u00a0','').replace(' ','').replace(',','.')
    s = re.sub(r'[^\d.\-+]','',s)
    try: return float(s)
    except: return None

def parse_qonto(texte):
    LIGNE = re.compile(r'"(\d{2}/\d{2})\s+(.+?)\s+([\-\+]\s*[\d\s]+\.?\d*)\s+EUR"')
    MONT  = re.compile(r'([+\-])\s*([\d\s]+\.?\d*)')
    res   = []
    annee = str(datetime.now().year)
    for line in texte.splitlines():
        m = LIGNE.match(line.strip())
        if not m: continue
        mm = MONT.match(m.group(3).strip())
        if not mm: continue
        sign = 1 if mm.group(1)=='+' else -1
        val  = float(mm.group(2).replace(' ','')) * sign
        res.append({"date_aff": m.group(1)+"/"+annee,
                    "client":   extraire_client(m.group(2).strip()),
                    "montant":  val})
    return pd.DataFrame(res) if res else None

def parse_csv(texte):
    lignes = [l for l in texte.strip().splitlines() if l.strip()]
    if not lignes: return None
    sep = ";" if texte[:500].count(";") >= texte[:500].count(",") else ","
    mots = ["date","libelle","libellé","montant","amount","credit","debit","description","label","motif","operation","solde"]
    debut = 0
    for i,l in enumerate(lignes):
        cols = [c.strip().strip('"').lower() for c in l.split(sep)]
        if any(any(k in c for k in mots) for c in cols):
            debut = i; break
    try:
        df = pd.read_csv(io.StringIO("\n".join(lignes[debut:])), sep=sep, decimal=",", quotechar='"')
    except: return None
    df.columns = [c.strip().strip('"').lower() for c in df.columns]
    mc = next((c for c in df.columns if any(k in c for k in ["montant","amount","crédit","credit","débit","debit"])),None)
    if not mc: return None
    df["montant"] = df[mc].apply(lambda x: parse_montant(str(x)))
    lc = next((c for c in df.columns if any(k in c for k in ["libelle","libellé","description","label","motif","operation","opération"])),None)
    dc = next((c for c in df.columns if "date" in c or "jour" in c),None)
    df["client"]   = df[lc].apply(extraire_client) if lc else "Client inconnu"
    df["date_aff"] = df[dc].astype(str) if dc else datetime.now().strftime("%d/%m/%Y")
    return df

def parse_texte_brut(texte):
    DATE_RE    = re.compile(r'\b(\d{1,2}[/\-\.]\d{1,2}(?:[/\-\.]\d{2,4})?)\b')
    MONTANT_RE = re.compile(r'([+\-]?\s?\d{1,3}(?:[\s\u00a0]\d{3})*(?:[,\.]\d{1,2})?)\s*(?:EUR|€)?')
    res = []
    for ligne in texte.strip().splitlines():
        ligne = ligne.strip()
        if not ligne: continue
        dm = DATE_RE.search(ligne)
        if not dm: continue
        ms = MONTANT_RE.findall(ligne)
        if not ms: continue
        m = parse_montant(ms[-1].replace(' ','').replace('\u00a0',''))
        if m is None: continue
        lib = MONTANT_RE.sub('', ligne[dm.end():]).strip(' €-+')
        res.append({"date_aff": dm.group(1), "client": extraire_client(lib or ligne), "montant": m})
    return pd.DataFrame(res) if res else None

def parse_auto(texte):
    df = parse_qonto(texte)
    if df is not None and not df.empty: return df, "Qonto"
    df = parse_csv(texte)
    if df is not None and not df.empty: return df, "CSV"
    df = parse_texte_brut(texte)
    if df is not None and not df.empty: return df, "Texte"
    return None, None

def parse_bytes(data):
    for enc in ["utf-8","latin-1","cp1252"]:
        try:
            df, fmt = parse_auto(data.decode(enc))
            if df is not None: return df, fmt
        except: continue
    return None, None

def lire_pdf(data):
    try:
        import pdfplumber
        texte = []
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t: texte.append(t)
        if texte:
            df, fmt = parse_auto("\n".join(texte))
            if df is not None: return df, fmt
        return None, None
    except Exception as e:
        return None, None

def normaliser(df, source):
    df = df.copy()
    if "date_aff" not in df.columns: df["date_aff"] = datetime.now().strftime("%d/%m/%Y")
    if "client" not in df.columns:   df["client"]   = "Client inconnu"
    df["source"] = source
    return df

# ══════════════════════════════════════════════════════════════════
# Extraction Claude Vision (pour images)
# ══════════════════════════════════════════════════════════════════

def extraire_via_claude(image_bytes, media_type):
    if not api_key:
        return None
    prompt = """Analyse ce relevé bancaire et extrais TOUTES les transactions.
Réponds UNIQUEMENT avec un JSON valide, sans texte avant ou après :
[{"date": "JJ/MM/AAAA", "libelle": "libellé complet", "montant": 1234.56}]
Montants positifs = crédits, négatifs = débits.
Année si absente : """ + str(datetime.now().year)

    content = [
        {"type": "image", "source": {"type": "base64", "media_type": media_type,
         "data": base64.b64encode(image_bytes).decode()}},
        {"type": "text", "text": prompt}
    ]
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": "claude-opus-4-5", "max_tokens": 4096,
              "messages": [{"role": "user", "content": content}]},
        timeout=60
    )
    if resp.status_code != 200:
        raise Exception("Erreur API : " + resp.text[:200])
    texte = resp.json()["content"][0]["text"].strip()
    texte = re.sub(r'^```json\s*','',texte)
    texte = re.sub(r'```$','',texte).strip()
    data  = json.loads(texte)
    rows  = [{"date_aff": str(i.get("date","")),
              "client":   extraire_client(str(i.get("libelle",""))),
              "montant":  float(i.get("montant",0))} for i in data]
    return pd.DataFrame(rows) if rows else None

# ══════════════════════════════════════════════════════════════════
# Génération facture PDF
# ══════════════════════════════════════════════════════════════════

def generer_facture(row, numero):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(13,13,13)
    pdf.rect(0,0,210,38,'F')
    pdf.set_font("Helvetica","B",20)
    pdf.set_text_color(200,241,53)
    pdf.set_y(8)
    pdf.cell(0,10,"FACTURE",ln=1,align="C")
    pdf.set_font("Helvetica","",8)
    pdf.set_text_color(180,180,180)
    num = "N° FACT-"+datetime.now().strftime("%Y%m")+"-"+str(numero).zfill(4)
    pdf.cell(0,6,num+"   ·   "+str(row.get("date_aff",datetime.now().strftime("%d/%m/%Y"))),ln=1,align="C")
    pdf.ln(10)
    pdf.set_text_color(30,30,30); pdf.set_font("Helvetica","B",9)
    pdf.set_x(14); pdf.cell(88,5,"ÉMETTEUR",ln=0); pdf.cell(88,5,"DESTINATAIRE",ln=1)
    pdf.set_font("Helvetica","",9); pdf.set_text_color(80,80,80)
    for a,c in zip([company_name, company_address.replace("\n"," — "), "SIRET : "+company_siret],
                   [str(row["client"]),"",""]):
        pdf.set_x(14); pdf.cell(88,5,a,ln=0); pdf.cell(88,5,c,ln=1)
    pdf.ln(6)
    pdf.set_draw_color(200,241,53); pdf.set_line_width(0.6)
    pdf.line(14,pdf.get_y(),196,pdf.get_y()); pdf.ln(5)
    pdf.set_fill_color(13,13,13); pdf.set_text_color(200,241,53); pdf.set_font("Helvetica","B",8)
    pdf.set_x(14)
    pdf.cell(100,7,"DESCRIPTION",0,fill=True)
    pdf.cell(32,7,"HT",0,align="R",fill=True)
    pdf.cell(22,7,"TVA",0,align="R",fill=True)
    pdf.cell(32,7,"TTC",0,align="R",fill=True); pdf.ln(7)
    mht  = round(row["montant"]/(1+tva_rate/100),2) if tva_rate>0 else round(row["montant"],2)
    mtva = round(row["montant"]-mht,2)
    mttc = round(row["montant"],2)
    pdf.set_fill_color(245,245,240); pdf.set_text_color(30,30,30); pdf.set_font("Helvetica","",9)
    pdf.set_x(14)
    pdf.cell(100,8,"Prestation de services",0,fill=True)
    pdf.cell(32,8,str(mht)+" EUR",0,align="R",fill=True)
    pdf.cell(22,8,str(tva_rate)+"%",0,align="R",fill=True)
    pdf.cell(32,8,str(mttc)+" EUR",0,align="R",fill=True); pdf.ln(10)
    pdf.set_draw_color(220,220,210); pdf.set_line_width(0.3)
    pdf.line(14,pdf.get_y(),196,pdf.get_y()); pdf.ln(3)
    pdf.set_x(130); pdf.set_font("Helvetica","",8); pdf.set_text_color(120,120,120)
    pdf.cell(36,5,"Sous-total HT",ln=0); pdf.cell(36,5,str(mht)+" EUR",align="R",ln=1)
    pdf.set_x(130); pdf.cell(36,5,"TVA "+str(tva_rate)+"%",ln=0); pdf.cell(36,5,str(mtva)+" EUR",align="R",ln=1)
    pdf.ln(2)
    pdf.set_fill_color(200,241,53); pdf.set_x(120)
    pdf.set_font("Helvetica","B",10); pdf.set_text_color(13,13,13)
    pdf.cell(76,10,"  TOTAL TTC   "+str(mttc)+" EUR",align="R",fill=True,ln=1)
    pdf.ln(14)
    pdf.set_font("Helvetica","I",7); pdf.set_text_color(160,155,145); pdf.set_x(14)
    pdf.cell(0,4,"Facture payable sous 30 jours — Merci pour votre confiance.",ln=1)
    if tva_rate==0:
        pdf.set_x(14); pdf.cell(0,4,"TVA non applicable, art. 293 B du CGI",ln=1)
    return bytes(pdf.output())

# ══════════════════════════════════════════════════════════════════
# Affichage résultats
# ══════════════════════════════════════════════════════════════════

def afficher_resultats(enc, cle):
    total = enc["montant"].sum()
    st.markdown(f"""
    <div class="stats">
      <div class="stat"><div class="stat-n">{len(enc)}</div><div class="stat-l">Encaissements</div></div>
      <div class="stat"><div class="stat-n">{total:,.0f} €</div><div class="stat-l">Total brut</div></div>
      <div class="stat"><div class="stat-n">{round(total/(1+tva_rate/100),0):,.0f} €</div><div class="stat-l">Total HT</div></div>
    </div>""", unsafe_allow_html=True)
    st.markdown("**Sélectionnez les lignes à facturer**")
    sels = []
    for i,row in enc.iterrows():
        label = str(row["client"])+"  ·  "+str(round(row["montant"],2))+" €  ·  "+str(row["date_aff"])
        if st.checkbox(label, value=True, key=cle+"_c"+str(i)): sels.append(i)
    st.markdown("<hr>", unsafe_allow_html=True)
    st.write(str(len(sels))+" facture(s) sélectionnée(s)")
    if st.button("⚡  Générer "+str(len(sels))+" facture(s)", type="primary", use_container_width=True, key=cle+"_g"):
        if not sels: st.warning("Sélectionnez au moins une ligne.")
        else:
            zb = io.BytesIO()
            with zipfile.ZipFile(zb,"w",zipfile.ZIP_DEFLATED) as zf:
                for i,idx in enumerate(sels,1):
                    row = enc.loc[idx].to_dict()
                    cs  = re.sub(r'[^A-Za-z0-9_-]','_',str(row["client"])[:20])
                    zf.writestr("FACT_"+cs+"_"+datetime.now().strftime("%Y%m%d")+".pdf", generer_facture(row,i))
            zb.seek(0)
            st.success("✅  "+str(len(sels))+" facture(s) générée(s) !")
            st.download_button("📥  Télécharger ZIP", data=zb.getvalue(),
                file_name="factures_"+datetime.now().strftime("%Y%m%d_%H%M")+".zip",
                mime="application/zip", use_container_width=True, key=cle+"_d")

def multi_texte(cle, ph):
    if cle+"_n" not in st.session_state: st.session_state[cle+"_n"] = 1
    txts = []
    for i in range(st.session_state[cle+"_n"]):
        txts.append(st.text_area("Relevé "+str(i+1), height=160, key=cle+"_t"+str(i), placeholder=ph))
    c1,c2 = st.columns(2)
    with c1:
        if st.button("➕ Ajouter", use_container_width=True, key=cle+"_a"):
            st.session_state[cle+"_n"] += 1; st.rerun()
    with c2:
        if st.session_state[cle+"_n"] > 1:
            if st.button("➖ Supprimer", use_container_width=True, key=cle+"_r"):
                st.session_state[cle+"_n"] -= 1; st.rerun()
    return txts

# ══════════════════════════════════════════════════════════════════
# ONGLETS
# ══════════════════════════════════════════════════════════════════

tab1, tab2, tab3 = st.tabs(["📁 Upload fichier", "📋 Coller le texte", "🖼️ Analyse image"])

# ── Onglet 1 : Upload (fonctionne bien sur Streamlit Cloud) ──────
with tab1:
    st.caption("Uploadez vos fichiers PDF ou CSV — fonctionne sur mobile et PC")
    ups = st.file_uploader(
        "Glissez vos relevés ici",
        type=["pdf","csv"],
        accept_multiple_files=True,
        key="upl",
        label_visibility="collapsed"
    )
    if ups:
        if st.button("📊  Analyser les fichiers", type="secondary", use_container_width=True, key="b_u"):
            tous = []
            for f in ups:
                data = f.read()
                nom  = f.name
                if nom.lower().endswith(".pdf"):
                    df, fmt = lire_pdf(data)
                    if df is not None:
                        df = normaliser(df, nom); tous.append(df)
                        st.success("✅ "+nom+" — "+str(len(df))+" lignes ("+str(fmt)+")")
                    else:
                        st.warning("⚠️ "+nom+" : format non reconnu. Essayez l'onglet 'Coller le texte'.")
                else:
                    df, fmt = parse_bytes(data)
                    if df is not None:
                        df = normaliser(df, nom); tous.append(df)
                        st.success("✅ "+nom+" — "+str(len(df))+" lignes ("+str(fmt)+")")
                    else:
                        st.warning("⚠️ "+nom+" : format non reconnu.")
            if tous:
                c = pd.concat(tous, ignore_index=True)
                e = c[c["montant"]>0].copy().reset_index(drop=True)
                st.session_state["e_u"] = e if not e.empty else None
    if st.session_state.get("e_u") is not None:
        afficher_resultats(st.session_state["e_u"], "u")

# ── Onglet 2 : Copier-coller ─────────────────────────────────────
with tab2:
    st.caption("Copiez le contenu de votre relevé et collez-le ici")
    with st.expander("💡 Comment faire depuis Qonto"):
        st.markdown("""
1. Dans Qonto → **Transactions** → **Exporter**
2. Choisissez **CSV** → envoyez par email
3. Ouvrez le CSV → **Sélectionner tout** → **Copier**
4. Collez ici et appuyez sur **Analyser**
        """)
    txts = multi_texte("p", "Collez ici le contenu de votre relevé CSV ou PDF...")
    if st.button("📊  Analyser", type="secondary", use_container_width=True, key="b_p"):
        tous = []
        for i,t in enumerate(txts):
            if not t.strip(): continue
            df, fmt = parse_auto(t)
            if df is not None and not df.empty:
                df = normaliser(df, "Relevé "+str(i+1))
                tous.append(df)
                st.success("✅ Relevé "+str(i+1)+" — "+str(len(df))+" lignes ("+str(fmt)+")")
            else:
                st.warning("Relevé "+str(i+1)+" : format non reconnu.")
        if tous:
            c = pd.concat(tous, ignore_index=True)
            e = c[c["montant"]>0].copy().reset_index(drop=True)
            st.session_state["e_p"] = e if not e.empty else None
    if st.session_state.get("e_p") is not None:
        afficher_resultats(st.session_state["e_p"], "p")

# ── Onglet 3 : Analyse image via Claude ──────────────────────────
with tab3:
    st.caption("Uploadez une image de votre relevé — Claude extrait les transactions automatiquement")
    if not api_key:
        st.warning("⚠️ Clé API Anthropic non configurée. Ajoutez `ANTHROPIC_API_KEY` dans les Secrets Streamlit Cloud.")
    else:
        img_up = st.file_uploader(
            "Image de votre relevé (JPG, PNG)",
            type=["jpg","jpeg","png","webp"],
            key="img_up",
            label_visibility="collapsed"
        )
        if img_up:
            data = img_up.read()
            st.image(data, caption="Aperçu", use_container_width=True)
            if st.button("🔍  Extraire via Claude", type="primary", use_container_width=True, key="b_img"):
                with st.spinner("Claude analyse votre relevé..."):
                    try:
                        ext  = img_up.name.lower().split(".")[-1]
                        mime = {"jpg":"image/jpeg","jpeg":"image/jpeg","png":"image/png","webp":"image/webp"}.get(ext,"image/jpeg")
                        df   = extraire_via_claude(data, mime)
                        if df is not None and not df.empty:
                            df = normaliser(df, img_up.name)
                            e  = df[df["montant"]>0].copy().reset_index(drop=True)
                            st.session_state["e_img"] = e if not e.empty else None
                            st.success("✅ "+str(len(df))+" transactions extraites !")
                        else:
                            st.warning("Aucune transaction trouvée sur cette image.")
                    except Exception as ex:
                        st.error("Erreur : "+str(ex))
        if st.session_state.get("e_img") is not None:
            afficher_resultats(st.session_state["e_img"], "img")

st.markdown("<hr>", unsafe_allow_html=True)
st.caption("FactureAuto · Streamlit Community Cloud · Données traitées localement")

import re
from datetime import datetime
import pdfplumber
import io

def extraire_client(texte):
    t = str(texte).upper()
    
    # Mots à supprimer des noms de client
    mots_suppression = [
        r'\b(VIR|PRLV|SEPA|RECU|CARTE|CB|CHQ|PAIEMENT|REGLEMENT)',
        r'\b(ABONNEMENT|DOC|TXT|PID|FRAIS)\b'
    ]
    
    for pattern in mots_suppression:
        t = re.sub(pattern, ' ', t)
    
    # Supprimer les chiffres pour garder le nom propre
    t = re.sub(r'\d', ' ', t)
    
    # Extraction du nom client
    m = re.search(r'([A-Z][A-Z\s\-]{2,})', t)
    return m.group(1).strip()[:40] if m else "Client inconnu"

def parse_montant(s):
    s = str(s).replace('\u00a0', '').replace(' ', '').replace(',', '.')
    # Nettoyer les caractères non numériques
    s = re.sub(r'[^\d.\-+]', '', s)
    
    try:
        val = float(s)
        return val if abs(val) < 1e15 else None
    except (ValueError, TypeError):
        return None

def parse_qonto_pdf(texte):
    lignes = texte.strip().splitlines()
    annee = str(datetime.now().year)
    
    DATE_RE = re.compile(r'^(\d{2}/\d{2})\s+(.+)$')
    MONT_RE = re.compile(r'^([+\-])\s*([\d\s]+\.?\d*)\s*EUR$')
    
    res = []
    i = 0
    
    while i < len(lignes):
        ligne = lignes[i].strip()
        dm = DATE_RE.match(ligne)
        
        if dm:
            date = dm.group(1) + "/" + annee
            client = dm.group(2).strip()
            
            for j in range(i+1, min(i+4, len(lignes))):
                l = lignes[j].strip()
                mm = MONT_RE.match(l)
                
                if mm:
                    sign = 1 if mm.group(1) == "+" else -1
                    val = float(mm.group(2).replace(" ", "")) * sign
                    
                    # Filtrer uniquement les encaissements (>0)
                    if val > 0:
                        res.append({
                            "date": date, 
                            "client": client[:40], 
                            "montant": val
                        })
                    
                    i = j
                    break
        
        i += 1
    
    return res

def parse_qonto_csv(texte):
    lignes = [l for l in texte.strip().splitlines() if l.strip()]
    
    if not lignes:
        return []
    
    sep = ";" if texte[:500].count(";") >= texte[:500].count(",") else ","
    
    mots = ["date", "libelle", "montant", "credit", "debit", "operation"]
    
    debut = 0
    for i, l in enumerate(lignes):
        cols = [c.strip().strip('"').lower() for c in l.split(sep)]
        
        if any(any(k in c for k in mots) for c in cols):
            debut = i
            break
    
    headers = [c.strip().strip('"').lower() for c in lignes[debut].split(sep)]
    
    mc = next((c for c in headers if any(k in c for k in ["montant", "credit", "debit"])), None)
    lc = next((c for c in headers if any(k in c for k in ["libelle", "description", "operation"])), None)
    dc = next((c for c in headers if "date" in c or "jour" in c), None)
    
    if not mc:
        return []
    
    res = []
    for ligne in lignes[debut+1:]:
        cells = [c.strip().strip('"') for c in ligne.split(sep)]
        
        if len(cells) < len(headers):
            continue
        
        row = dict(zip(headers, cells))
        val = parse_montant(row.get(mc, ""))
        
        if val is None or val <= 0:
            continue
        
        res.append({
            "date": row.get(dc, datetime.now().strftime("%d/%m/%Y")) if dc else datetime.now().strftime("%d/%m/%Y"),
            "client": extraire_client(row.get(lc, "")) if lc else "Client inconnu",
            "montant": val
        })
    
    return res

def parse_texte_brut(texte):
    DATE_RE = re.compile(r'\b(\d{1,2}[/\-\.]\d{1,2}(?:[/\-\.]\d{2,4})?)\b')
    MONTANT_RE = re.compile(r'([+\-]?\s?\d{1,3}(?:[\s\u00a0]\d{3})*(?:[,\.]\d{1,2})?)\s*(?:EUR|€)?')
    
    res = []
    
    for ligne in texte.strip().splitlines():
        ligne = ligne.strip()
        
        if not ligne:
            continue
        
        dm = DATE_RE.search(ligne)
        
        if not dm:
            continue
        
        ms = MONTANT_RE.findall(ligne)
        
        if not ms:
            continue
        
        m = parse_montant(ms[-1].replace(' ', '').replace('\u00a0', ''))
        
        if m is None or m <= 0:
            continue
        
        lib = MONTANT_RE.sub('', ligne[dm.end():]).strip(' €-+')
        
        res.append({
            "date": dm.group(1), 
            "client": extraire_client(lib or ligne), 
            "montant": m
        })
    
    return res

def parse_auto(texte):
    r = parse_qonto_csv(texte)  # Essayez CSV d'abord pour Qonto
    if r:
        return r
    
    r = parse_qonto_pdf(texte)
    if r:
        return r
    
    return parse_texte_brut(texte)

def lire_pdf(data):
    try:
        texte = []
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    texte.append(t)
        
        return parse_auto("\n".join(texte))
    
    except Exception as e:
        print(f"[Erreur PDF] {e}")
        return []

def lire_csv(data):
    for enc in ["utf-8", "latin-1", "cp1252"]:
        try:
            texte = data.decode(enc)
            return parse_auto(texte)
        except:
            continue
    
    return []

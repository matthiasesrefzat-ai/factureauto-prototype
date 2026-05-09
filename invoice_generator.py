from fpdf import FPDF
import re

class InvoiceGenerator:
    def __init__(self, company, tva_rate):
        self.company = company
        self.tva_rate = tva_rate / 100.0
    
    def generer_facture(self, row, numero, mode='individuel', txs=None):
        pdf = FPDF()
        pdf.add_page()
        
        num = "N FACT-" + datetime.now().strftime("%Y%m") + "-" + str(numero).zfill(4)
        date_str = row.get("date", "") if mode == 'individuel' else txs[0].get("date", "") if txs else ""
        periode = f"Du {txs[0].get('date', '')} au {txs[-1].get('date', '')}" if txs and len(txs) > 1 else date_str
        
        # --- Header ---
        pdf.set_fill_color(13, 13, 13)
        pdf.rect(0, 0, 210, 45, 'F')
        
        pdf.set_font("Helvetica", "B", 20)
        pdf.set_text_color(200, 241, 53)
        pdf.set_y(10)
        pdf.cell(0, 11, "FACTURE", ln=1, align="C")
        
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(170, 170, 170)
        pdf.cell(0, 5, f"{num}   |   Date : {periode}", ln=1, align="C")
        
        pdf.ln(12)
        
        # --- Emetteur / Destinataire ---
        pdf.set_text_color(80, 80, 80)
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_x(14)
        pdf.cell(88, 4, "EMETTEUR", ln=0)
        pdf.cell(88, 4, "DESTINATAIRE", ln=1)
        
        pdf.ln(2)
        
        name = str(self.company.get("name", ""))[:45]
        addr = str(self.company.get("address", "")).replace("\n", " - ")[:60]
        siret = "SIRET : " + str(self.company.get("siret", ""))
        
        client = str(row.get("client", "")).strip()[:45] if mode == 'individuel' else str(row.get("client", ""))[:45]
        
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(20, 20, 20)
        pdf.set_x(14)
        pdf.cell(88, 5, name, ln=0)
        pdf.cell(88, 5, client, ln=1)
        
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(100, 100, 100)
        pdf.set_x(14)
        pdf.cell(88, 5, addr[:60], ln=1)
        pdf.set_x(14)
        pdf.cell(88, 5, siret, ln=1)
        
        pdf.ln(5)
        
        # --- Separateur ---
        pdf.set_draw_color(200, 241, 53)
        pdf.set_line_width(0.6)
        pdf.line(14, pdf.get_y(), 196, pdf.get_y())
        pdf.ln(5)
        
        # --- En-tête Tableau ---
        pdf.set_fill_color(13, 13, 13)
        pdf.set_text_color(200, 241, 53)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_x(14)
        
        headers = ["DESCRIPTION", "DATE" if mode == 'groupe' else "", "HT", "TVA", "TTC"]
        for h in headers:
            col_w = 70 if h == "DESCRIPTION" else (30 if h == "DATE" else 28)
            pdf.cell(col_w, 8, h, border=1, fill=True, align="R" if h in ["HT", "TVA", "TTC"] else "")
        
        pdf.ln(8)
        
        # --- Ligne Prestation ---
        tva = self.tva_rate / 100.0
        
        mht = round(row["montant"] / (1 + tva), 2) if tva > 0 else round(row["montant"], 2)
        mtva = round(row["montant"] - mht, 2)
        mttc = round(row["montant"], 2)
        
        pdf.set_fill_color(248, 248, 244)
        pdf.set_text_color(20, 20, 20)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_x(14)
        
        desc = "Prestation de services" if mode == 'individuel' else row["client"][:40]
        date_tx = txs[0].get("date", "") if mode == 'groupe' and txs else ""
        
        pdf.cell(70, 8, desc, border=1, fill=True)
        pdf.cell(30, 8, str(date_tx), border=1, align="C", fill=True) if mode == 'groupe' else pdf.cell(30, 8, "", border=1, align="C")
        pdf.cell(28, 8, str(mht) + " EUR", border=1, align="R", fill=True)
        pdf.cell(22, 8, str(tva_rate) + "%", border=1, align="R", fill=True)
        pdf.cell(28, 8, str(mttc) + " EUR", border=1, align="R", fill=True)
        
        pdf.ln(11)
        
        # --- Pagination automatique ---
        max_y = 260
        if pdf.get_y() > max_y:
            pdf.add_page()
        
        # --- Totaux ---
        pdf.set_draw_color(220, 215, 205)
        pdf.set_line_width(0.3)
        pdf.line(14, pdf.get_y(), 196, pdf.get_y())
        pdf.ln(4)
        
        total_ht = mht if mode == 'individuel' else sum(t["montant"] / (1 + tva) for t in txs) if txs else 0
        total_tva = mtva if mode == 'individuel' else round(sum(t["montant"] for t in txs) - total_ht, 2) if txs else 0
        total_ttc = mttc if mode == 'individuel' else round(sum(t["montant"] for t in txs), 2) if txs else 0
        
        pdf.set_x(130)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(130, 125, 115)
        pdf.cell(36, 5, "Sous-total HT", ln=0)
        pdf.cell(36, 5, str(total_ht) + " EUR", align="R", ln=1)
        
        pdf.set_x(130)
        pdf.cell(36, 5, f"TVA {tva_rate}%", ln=0)
        pdf.cell(36, 5, str(total_tva) + " EUR", align="R", ln=1)
        
        pdf.ln(2)
        
        pdf.set_fill_color(200, 241, 53)
        pdf.set_x(120)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(13, 13, 13)
        pdf.cell(76, 12, f"TOTAL TTC {total_ttc} EUR", align="R", fill=True, ln=1)
        
        pdf.ln(18)
        
        # --- Pied ---
        pdf.set_font("Helvetica", "I", 7)
        pdf.set_text_color(160, 155, 145)
        pdf.set_x(14)
        pdf.cell(0, 4, "Facture payable sous 30 jours - Merci pour votre confiance.", ln=1)
        
        if tva_rate == 0:
            pdf.set_x(14)
            pdf.cell(0, 4, "TVA non applicable, art. 293 B du CGI", ln=1)
        
        return bytes(pdf.output())

def generer_facture_groupee(clients_txs_list, company, tva_rate):
    from datetime import datetime
    import zipfile
    import re
    
    pdf_gen = InvoiceGenerator(company, tva_rate)
    zip_buf = io.BytesIO()
    
    with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for i, (client_name, txs) in enumerate(clients_txs_list.items(), 1):
            total_ttc = sum(t["montant"] for t in txs)
            
            # Créer une facture unique pour le groupe
            pdf_bytes = generer_facture_groupe_single(client_name, txs, i, company, tva_rate)
            
            client_safe = re.sub(r'[^A-Za-z0-9_-]', '_', str(client_name)[:20])
            fname = f"FACT_GROUPE_{client_safe}_{datetime.now().strftime('%Y%m%d')}.pdf"
            zf.writestr(fname, pdf_bytes)
    
    zip_buf.seek(0)
    return zip_buf

def generer_facture_groupe_single(client_name, txs, numero, company, tva_rate):
    from fpdf import FPDF
    total = sum(t["montant"] for t in txs)
    tva = tva_rate / 100.0
    
    pdf = FPDF()
    pdf.add_page()
    
    num = "N FACT-" + datetime.now().strftime("%Y%m") + "-" + str(numero).zfill(4)
    
    # Header identique à la version individuelle
    pdf.set_fill_color(13, 13, 13)
    pdf.rect(0, 0, 210, 45, 'F')
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(200, 241, 53)
    pdf.set_y(10)
    pdf.cell(0, 11, "FACTURE", ln=1, align="C")
    
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(170, 170, 170)
    d1 = txs[0].get("date", "")
    d2 = txs[-1].get("date", "")
    periode = f"{d1} au {d2}" if len(txs) > 1 else d1
    pdf.cell(0, 5, f"{num}   |   Période : {periode}", ln=1, align="C")
    
    pdf.ln(12)
    
    # Emetteur / Destinataire
    pdf.set_text_color(80, 80, 80)
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_x(14)
    pdf.cell(88, 4, "EMETTEUR", ln=0)
    pdf.cell(88, 4, "DESTINATAIRE", ln=1)
    
    pdf.ln(2)
    
    name = str(company.get("name", ""))[:45]
    addr = str(company.get("address", "")).replace("\n", " - ")[:60]
    siret = "SIRET : " + str(company.get("siret", ""))
    client = str(client_name)[:45]
    
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(20, 20, 20)
    pdf.set_x(14)
    pdf.cell(88, 5, name[:45], ln=0)
    pdf.cell(88, 5, client[:45], ln=1)
    
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.set_x(14)
    pdf.cell(88, 5, addr[:60], ln=1)
    pdf.set_x(14)
    pdf.cell(88, 5, siret, ln=1)
    
    pdf.ln(5)
    
    pdf.set_draw_color(200, 241, 53)
    pdf.set_line_width(0.6)
    pdf.line(14, pdf.get_y(), 196, pdf.get_y())
    pdf.ln(5)
    
    # Tableau
    pdf.set_fill_color(13, 13, 13)
    pdf.set_text_color(200, 241, 53)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_x(14)
    
    headers = ["DESCRIPTION", "DATE", "HT", "TVA", "TTC"]
    for h in headers:
        col_w = 70 if h == "DESCRIPTION" else (30 if h == "DATE" else 28)
        pdf.cell(col_w, 8, h, border=1, fill=True, align="R" if h in ["HT", "TVA", "TTC"] else "")
    
    pdf.ln(8)
    
    # Lignes de transactions
    mttc_total = total
    
    for tx in txs:
        mht = round(tx["montant"] / (1 + tva), 2) if tva > 0 else round(tx["montant"], 2)
        mtva = round(tx["montant"] - mht, 2)
        
        pdf.set_fill_color(248, 248, 244)
        pdf.set_text_color(20, 20, 20)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_x(14)
        
        pdf.cell(70, 8, "Prestation de services", border=1, fill=True)
        pdf.cell(30, 8, str(tx.get("date", "")), border=1, align="C", fill=True)
        pdf.cell(28, 8, f"{mht} EUR", border=1, align="R", fill=True)
        pdf.cell(22, 8, f"{tva_rate}%", border=1, align="R", fill=True)
        pdf.cell(28, 8, f"{mtva + mht} EUR", border=1, align="R", fill=True)
        
        pdf.ln(10)
        
        # Pagination
        max_y = 260
        if pdf.get_y() > max_y:
            pdf.add_page()
    
    # Totaux
    pdf.set_draw_color(220, 215, 205)
    pdf.set_line_width(0.3)
    pdf.line(14, pdf.get_y(), 196, pdf.get_y())
    pdf.ln(4)
    
    total_ht = round(total / (1 + tva), 2) if tva > 0 else round(total, 2)
    total_tva_calc = round(total - total_ht, 2)
    
    pdf.set_x(130)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(130, 125, 115)
    pdf.cell(36, 5, "Sous-total HT", ln=0)
    pdf.cell(36, 5, f"{total_ht} EUR", align="R", ln=1)
    
    pdf.set_x(130)
    pdf.cell(36, 5, f"TVA {tva_rate}%", ln=0)
    pdf.cell(36, 5, f"{total_tva_calc} EUR", align="R", ln=1)
    
    pdf.ln(2)
    
    pdf.set_fill_color(200, 241, 53)
    pdf.set_x(120)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(13, 13, 13)
    pdf.cell(76, 12, f"TOTAL TTC {mttc_total} EUR", align="R", fill=True, ln=1)
    
    pdf.ln(16)
    
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(160, 155, 145)
    pdf.set_x(14)
    pdf.cell(0, 4, "Facture payable sous 30 jours - Merci pour votre confiance.", ln=1)
    
    return bytes(pdf.output())

from io import BytesIO

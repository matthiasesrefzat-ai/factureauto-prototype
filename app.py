from flask import Flask, request, jsonify, send_file, render_template_string, make_response
import os
import re
from datetime import datetime
import zipfile
import logging
from config import Config
from parsers import lire_pdf, lire_csv
from invoice_generator import InvoiceGenerator, generer_facture_groupee

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Dossier uploads et logs
UPLOAD_FOLDER = 'uploads'
LOGS_FOLDER = 'logs'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(LOGS_FOLDER, exist_ok=True)

@app.route('/')
def index():
    """Point d'entrée principal"""
    return render_template_string(HTML_PAGE)

@app.route('/analyser', methods=['POST'])
def analyser():
    """Analyse des fichiers uploadés"""
    try:
        files = request.files.getlist('files')
        
        if not files:
            response = make_response(jsonify({'error': 'Aucun fichier reçu'}), 400)
            response.headers['X-Error'] = 'aucun_fichier'
            return response
        
        # Limite de fichiers par requête
        if len(files) > app.config['MAX_UPLOADS_PER_REQUEST']:
            logger.warning(f"Trop de fichiers: {len(files)}")
            response = make_response(jsonify({'error': f'Maximum {app.config["MAX_UPLOADS_PER_REQUEST"]} fichiers autorisés'}), 400)
            return response
        
        all_transactions = []
        
        for f in files:
            # Vérification extension fichier
            nom = f.filename.lower()
            
            if not (nom.endswith('.pdf') or nom.endswith('.csv')):
                logger.warning(f"Fichier non autorisé: {f.filename}")
                continue
            
            try:
                data = f.read()
                
                # Traitement PDF
                if nom.endswith('.pdf'):
                    txs = lire_pdf(data)
                else:
                    txs = lire_csv(data)
                
                # Filtrer et ajouter transactions positives
                for tx in txs:
                    if tx.get('montant', 0) > 0 and 'date' in tx and 'client' in tx:
                        all_transactions.append(tx)
                        
            except Exception as e:
                logger.error(f"Erreur traitement fichier {f.filename}: {e}")
        
        # Vérification résultats
        if not all_transactions:
            response = make_response(jsonify({'error': 'Aucun encaissement valide trouvé dans les fichiers.'}), 400)
            return response
        
        # Log du résultat
        logger.info(f"Analyse complète: {len(all_transactions)} transactions trouvées")
        
        return jsonify({
            'success': True,
            'transactions': all_transactions[:100]  # Limite à 100 pour la démo
        })
    
    except Exception as e:
        logger.error(f"Erreur analyse: {str(e)}")
        response = make_response(jsonify({'error': str(e)}), 500)
        return response

@app.route('/generer', methods=['POST'])
def generer():
    """Génération des factures"""
    try:
        data = request.get_json()
        
        if not data or 'transactions' not in data:
            return jsonify({'error': 'Données invalides'}), 400
        
        transactions = data['transactions']
        company = data['company']
        tva_rate = data.get('tva_rate', 20) / 100.0
        mode = data.get('mode', 'individuel')
        
        if not company or not company.get('name'):
            return jsonify({'error': 'Données entreprise requises'}), 400
        
        invoice_gen = InvoiceGenerator(company, tva_rate)
        zip_buf = BytesIO()
        
        with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            if mode == 'groupe':
                # Regroupement par client
                groupes = {}
                for tx in transactions:
                    client = tx['client']
                    if client not in groupes:
                        groupes[client] = []
                    groupes[client].append(tx)
                
                num_total = 1
                for i, (client, group_txs) in enumerate(groupes.items(), 1):
                    pdf_bytes = generer_facture_groupe_single(
                        client, group_txs, 
                        num_total, company, tva_rate * 100
                    )
                    client_safe = re.sub(r'[^A-Za-z0-9_-]', '_', str(client)[:20])
                    fname = f"FACT_GROUPE_{client_safe}_{datetime.now().strftime('%Y%m%d')}.pdf"
                    zf.writestr(fname, pdf_bytes)
                    
            else:
                # Factures individuelles
                for i, tx in enumerate(transactions, 1):
                    pdf_bytes = invoice_gen.generer_facture(
                        tx, i, mode=mode
                    )
                    client_safe = re.sub(r'[^A-Za-z0-9_-]', '_', str(tx['client'])[:20])
                    fname = f"FACT_{client_safe}_{datetime.now().strftime('%Y%m%d')}_{i:04d}.pdf"
                    zf.writestr(fname, pdf_bytes)
        
        zip_buf.seek(0)
        
        response = make_response(send_file(
            zip_buf,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'factures_{datetime.now().strftime("%Y%m%d")}.zip'
        ))
        
        logger.info(f"Facturation générée: {len(transactions)} transactions")
        return response
    
    except Exception as e:
        logger.error(f"Erreur génération factures: {str(e)}")
        return jsonify({'error': str(e)}), 500

HTML_PAGE = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>FactureAuto - Génération automatique de factures</title>
    <style>
        :root {
            --bg: #0a0a0a;
            --card: #141414;
            --border: #252525;
            --primary: #c8f135;
            --secondary: #35f1c8;
            --text: #efefef;
            --muted: #666;
        }
        
        * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
        
        body {
            font-family: 'DM Sans', sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            padding: 0 20px 80px;
        }
        
        .container { max-width: 600px; margin: 0 auto; }
        
        /* Header */
        .header { text-align: center; padding: 40px 20px; }
        .tagline { font-size: 10px; letter-spacing: 4px; text-transform: uppercase; color: var(--muted); margin-bottom: 8px; }
        .title { 
            font-size: 42px; font-weight: 800; 
            background: linear-gradient(135deg, var(--text) 0%, var(--primary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .subtitle { font-size: 13px; color: var(--muted); margin-top: 8px; line-height: 1.5; }
        
        /* Cards */
        .card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 24px;
            margin-bottom: 16px;
        }
        
        .card-title {
            font-size: 11px; letter-spacing: 3px; text-transform: uppercase; 
            color: var(--muted); margin-bottom: 16px; font-weight: 500;
        }
        
        /* Form */
        label { display: block; font-size: 12px; color: var(--muted); margin-bottom: 6px; font-weight: 500; }
        input, textarea, select {
            width: 100%; background: var(--card); border: 1px solid var(--border); 
            border-radius: 12px; color: var(--text); font-size: 15px; padding: 14px 16px;
            outline: none; transition: border-color 0.2s; -webkit-appearance: none;
        }
        input:focus, textarea:focus, select:focus { border-color: var(--primary); }
        
        .row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
        
        /* Upload zone */
        .upload-zone {
            border: 2px dashed var(--border); border-radius: 16px; padding: 32px 20px;
            text-align: center; transition: all 0.2s; cursor: pointer; position: relative;
            background: var(--card);
        }
        .upload-zone:hover { border-color: var(--primary); background: rgba(200, 241, 53, 0.04); }
        
        .upload-icon { font-size: 36px; margin-bottom: 10px; }
        .upload-title { font-size: 15px; font-weight: 600; color: var(--text); margin-bottom: 4px; }
        .upload-sub { font-size: 12px; color: var(--muted); }
        
        .file-list { margin-top: 12px; }
        .file-item {
            display: flex; align-items: center; gap: 10px;
            background: var(--card); border: 1px solid var(--border); 
            border-radius: 10px; padding: 10px 14px; margin-bottom: 8px;
        }
        .file-icon { font-size: 20px; }
        .file-name { flex: 1; font-size: 13px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .file-size { font-size: 11px; color: var(--muted); }
        .file-remove { background: none; border: none; color: var(--muted); font-size: 20px; cursor: pointer; padding: 0 4px; }
        
        /* Progress */
        .progress { display: none; margin-top: 16px; }
        .progress-bar { height: 4px; background: var(--border); border-radius: 99px; overflow: hidden; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, var(--primary), var(--secondary)); border-radius: 99px; width: 0%; transition: width 0.3s; }
        
        /* Buttons */
        button {
            display: block; width: 100%; padding: 16px; 
            border-radius: 14px; font-family: 'DM Sans', sans-serif; 
            font-size: 16px; font-weight: 700; border: none; cursor: pointer;
            transition: all 0.2s; letter-spacing: 0.3px;
        }
        .btn-primary { background: var(--primary); color: #0a0a0a; }
        .btn-primary:hover { background: #b5d92e; }
        .btn-primary:disabled { background: var(--border); color: var(--muted); cursor: not-allowed; }
        
        /* Transactions */
        .stats { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-bottom: 16px; }
        .stat { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 12px; text-align: center; }
        .stat-n { font-family: 'Syne', sans-serif; font-size: 18px; font-weight: 700; color: var(--primary); }
        .stat-l { font-size: 10px; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; margin-top: 2px; }
        
        .tx-item {
            display: flex; align-items: center; gap: 12px; 
            padding: 14px; background: var(--card); border: 1px solid var(--border); 
            border-radius: 12px; margin-bottom: 8px; cursor: pointer; transition: all 0.15s;
        }
        .tx-item.selected { border-color: var(--primary); background: rgba(200, 241, 53, 0.04); }
        
        .tx-check { 
            width: 22px; height: 22px; border-radius: 6px; 
            border: 2px solid var(--border); flex-shrink: 0; display: flex; 
            align-items: center; justify-content: center; transition: all 0.15s;
        }
        .tx-item.selected .tx-check { background: var(--primary); border-color: var(--primary); }
        .tx-check-inner { display: none; color: #0a0a0a; font-size: 13px; font-weight: 900; }
        .tx-item.selected .tx-check-inner { display: block; }
        
        .tx-info { flex: 1; min-width: 0; }
        .tx-client { font-size: 14px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .tx-date { font-size: 11px; color: var(--muted); margin-top: 2px; }
        .tx-amount { font-size: 15px; font-weight: 700; color: var(--primary); white-space: nowrap; }
        
        /* Mode de facturation */
        .mode-options { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 12px; }
        .mode-btn { padding: 14px; border-radius: 10px; font-size: 13px; font-weight: 700; cursor: pointer; }
        .mode-btn.active { background: var(--primary); color: #0a0a0a; }
        
        /* Alerts */
        .alert { padding: 14px 16px; border-radius: 12px; font-size: 13px; margin-bottom: 12px; line-height: 1.5; display: none; }
        .alert-error { background: rgba(255, 80, 80, 0.1); border: 1px solid rgba(255, 80, 80, 0.3); color: #ff8080; }
        .alert-success { background: rgba(200, 241, 53, 0.08); border: 1px solid rgba(200, 241, 53, 0.2); color: var(--primary); }
        
        /* Spinner */
        @keyframes spin { to { transform: rotate(360deg); } }
        .spinner { width: 18px; height: 18px; border: 2px solid rgba(10, 10, 10, 0.3); border-top-color: #0a0a0a; border-radius: 50%; animation: spin 0.7s linear infinite; display: inline-block; vertical-align: middle; margin-right: 8px; }
        
        /* Scroll to bottom */
        .download-section { margin-top: 20px; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <div class="tagline">Facturation automatique</div>
            <h1 class="title">FactureAuto</h1>
            <p class="subtitle">Chargez vos relevés bancaires et générez vos factures en un seul clic</p>
        </header>
        
        <section class="card">
            <h3 class="card-title">Vos informations entreprise</h3>
            <div style="margin-bottom: 12px">
                <label>Nom de l'entreprise *</label>
                <input type="text" id="company_name" value="Ma Société SARL">
            </div>
            <div style="margin-bottom: 12px">
                <label>Adresse</label>
                <textarea id="company_address" rows="3">12 rue des Entrepreneurs
75001 Paris</textarea>
            </div>
            <div class="row">
                <div>
                    <label>SIRET</label>
                    <input type="text" id="company_siret" value="123 456 789 00012">
                </div>
                <div>
                    <label>TVA (%)</label>
                    <select id="tva_rate">
                        <option value="0">0%</option>
                        <option value="5">5%</option>
                        <option value="10">10%</option>
                        <option value="20" selected>20%</option>
                    </select>
                </div>
            </div>
        </section>
        
        <section class="card">
            <h3 class="card-title">Relevés bancaires</h3>
            <div class="upload-zone" id="uploadZone">
                <input type="file" id="fileInput" accept=".pdf,.csv" multiple style="display: none;">
                <div class="upload-icon">📂</div>
                <div class="upload-title">Appuyez pour choisir vos fichiers</div>
                <div class="upload-sub">PDF ou CSV - Fichiers multiples acceptés</div>
            </div>
            
            <div class="file-list" id="fileList"></div>
            
            <div class="progress" id="progress">
                <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
                <p class="alert alert-success" style="display: block;" id="progressText">Analyse en cours...</p>
            </div>
            
            <button class="btn-primary" id="analyzeBtn" style="margin-top: 16px; display: none;" onclick="analyser()">
                Analyser les relevés
            </button>
            
            <div id="alertZone"></div>
        </section>
        
        <section class="card tx-list" id="txCard" style="display: none;">
            <h3 class="card-title">Encaissements détectés</h3>
            
            <div class="stats" id="statsZone"></div>
            
            <button onclick="toggleSelectAll()" style="font-size: 11px; color: var(--primary); background: none; border: none; margin-bottom: 12px; cursor: pointer;">
                Tout sélectionner / Déselectionner
            </button>
            
            <div id="txList"></div>
            
            <select id="modeSelect" style="margin-top: 16px;" onchange="updateMode()">
                <option value="individuel">Une facture par transaction</option>
                <option value="groupe">Une facture par client (groupée)</option>
            </select>
            
            <button class="btn-primary" id="genBtn" onclick="generer()" style="margin-top: 12px; display: none;">
                Générer les factures
            </button>
        </section>
        
        <div class="alert alert-error" id="errorAlert"></div>
        
        <div class="download-section" id="dlSection" style="display: none;">
            <a href="#" class="btn-primary" id="dlBtn">Télécharger le ZIP</a>
        </div>
    </div>
    
    <script>
        var selectedFiles = [];
        var transactions = [];
        var selected = new Set();
        
        // Zone upload
        const uploadZone = document.getElementById('uploadZone');
        const fileInput = document.getElementById('fileInput');
        
        uploadZone.addEventListener('dragover', (e) => { e.preventDefault(); uploadZone.style.borderColor = 'var(--primary)'; });
        uploadZone.addEventListener('dragleave', () => { uploadZone.style.borderColor = 'var(--border)'; });
        uploadZone.addEventListener('drop', (e) => { 
            e.preventDefault(); 
            uploadZone.style.borderColor = 'var(--border)';
            addFiles(e.dataTransfer.files);
        });
        
        fileInput.addEventListener('change', () => {
            addFiles(fileInput.files);
            fileInput.value = '';
        });
        
        function addFiles(files) {
            for (let i = 0; i < files.length; i++) {
                const f = files[i];
                const exists = selectedFiles.some(x => x.name === f.name && x.size === f.size);
                if (!exists) selectedFiles.push(f);
            }
            renderFiles();
        }
        
        function renderFiles() {
            const list = document.getElementById('fileList');
            list.innerHTML = '';
            
            selectedFiles.forEach((f, i) => {
                const size = f.size > 1024*1024 ? (f.size/1024/1024).toFixed(1) + ' MB' : Math.round(f.size/1024) + ' KB';
                const icon = f.name.endsWith('.pdf') ? '📄' : '📊';
                
                const div = document.createElement('div');
                div.className = 'file-item';
                div.innerHTML = `
                    <span class="file-icon">${icon}</span>
                    <span class="file-name">${f.name}</span>
                    <span class="file-size">${size}</span>
                    <button class="file-remove" onclick="removeFile(${i})">×</button>
                `;
                list.appendChild(div);
            });
            
            document.getElementById('analyzeBtn').style.display = selectedFiles.length ? 'block' : 'none';
        }
        
        function removeFile(i) {
            selectedFiles.splice(i, 1);
            renderFiles();
        }
        
        function showAlert(msg, type) {
            const alertZone = document.getElementById('alertZone');
            const dlSection = document.getElementById('dlSection');
            
            if (type === 'error') {
                document.getElementById('errorAlert').textContent = msg;
                document.getElementById('errorAlert').style.display = 'block';
            } else {
                alertZone.innerHTML = `<div class="alert ${type}">${msg}</div>`;
                dlSection.style.display = 'block';
            }
        }
        
        function analyser() {
            if (!selectedFiles.length) return;
            
            const btn = document.getElementById('analyzeBtn');
            const progressFill = document.getElementById('progressFill');
            const progressText = document.getElementById('progressText');
            
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner"></span> Analyse en cours...';
            progressText.style.display = 'block';
            document.getElementById('progress').style.display = 'block';
            
            const form = new FormData();
            selectedFiles.forEach(f => form.append('files', f));
            form.append('company_name', document.getElementById('company_name').value);
            form.append('company_address', document.getElementById('company_address').value);
            form.append('company_siret', document.getElementById('company_siret').value);
            form.append('tva_rate', document.getElementById('tva_rate').value);
            
            fetch('/analyser', { method: 'POST', body: form })
                .then(r => r.json())
                .then(data => {
                    progressFill.style.width = '100%';
                    
                    if (data.error) {
                        showAlert(data.error, 'error');
                        btn.disabled = false;
                        btn.innerHTML = 'Analyser les relevés';
                        return;
                    }
                    
                    transactions = data.transactions;
                    renderTransactions();
                    
                    btn.disabled = false;
                    btn.innerHTML = 'Analyser les relevés';
                    document.getElementById('progress').style.display = 'none';
                })
                .catch(e => {
                    showAlert('Erreur: ' + e.message, 'error');
                    btn.disabled = false;
                    btn.innerHTML = 'Analyser les relevés';
                    document.getElementById('progress').style.display = 'none';
                });
        }
        
        function renderTransactions() {
            if (!transactions.length) {
                showAlert('Aucun encaissement trouvé.', 'error');
                return;
            }
            
            selected = new Set(transactions.map((_, i) => i));
            const total = transactions.reduce((s, t) => s + t.montant, 0);
            
            document.getElementById('statsZone').innerHTML = `
                <div class="stat"><div class="stat-n">${transactions.length}</div><div class="stat-l">Encaissements</div></div>
                <div class="stat"><div class="stat-n">${Math.round(total).toLocaleString('fr')}</div><div class="stat-l">Total EUR</div></div>
                <div class="stat"><div class="stat-n">${Math.round(total * 0.83).toLocaleString('fr')}</div><div class="stat-l">Total HT</div></div>
            `;
            
            const list = document.getElementById('txList');
            list.innerHTML = '';
            
            transactions.forEach((tx, i) => {
                const div = document.createElement('div');
                div.className = 'tx-item selected';
                div.id = `tx-${i}`;
                
                div.onclick = () => toggleTx(i);
                div.innerHTML = `
                    <div class="tx-check"><span class="tx-check-inner">✓</span></div>
                    <div class="tx-info">
                        <div class="tx-client">${tx.client}</div>
                        <div class="tx-date">${tx.date}</div>
                    </div>
                    <div class="tx-amount">${tx.montant.toFixed(2)} EUR</div>
                `;
                
                list.appendChild(div);
            });
            
            document.getElementById('txCard').style.display = 'block';
            document.getElementById('genBtn').style.display = 'block';
            updateMode();
        }
        
        function toggleTx(i) {
            if (selected.has(i)) selected.delete(i);
            else selected.add(i);
            
            const el = document.getElementById(`tx-${i}`);
            if (selected.has(i)) el.classList.add('selected');
            else el.classList.remove('selected');
            
            updateSelectCount();
        }
        
        function toggleSelectAll() {
            if (selected.size === transactions.length) {
                selected.clear();
                transactions.forEach((_, i) => document.getElementById(`tx-${i}`).classList.remove('selected'));
            } else {
                transactions.forEach((_, i) => {
                    selected.add(i);
                    document.getElementById(`tx-${i}`).classList.add('selected');
                });
            }
            
            updateSelectCount();
        }
        
        function updateSelectCount() {
            document.querySelector('.sel-count').textContent = `${selected.size} sélectionné(s)`;
            document.getElementById('genBtn').disabled = selected.size === 0;
        }
        
        function generer() {
            if (!selected.size) return;
            
            const btn = document.getElementById('genBtn');
            const dlSection = document.getElementById('dlSection');
            const dlBtn = document.getElementById('dlBtn');
            
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner"></span> Génération...';
            
            const sel = Array.from(selected).map(i => transactions[i]);
            
            fetch('/generer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    transactions: sel,
                    mode: document.getElementById('modeSelect').value,
                    company: {
                        name: document.getElementById('company_name').value,
                        address: document.getElementById('company_address').value,
                        siret: document.getElementById('company_siret').value
                    },
                    tva_rate: parseInt(document.getElementById('tva_rate').value)
                })
            })
            .then(r => r.blob())
            .then(blob => {
                const url = URL.createObjectURL(blob);
                dlBtn.href = url;
                dlBtn.download = `factures_${new Date().toISOString().slice(0, 10)}.zip`;
                
                dlSection.style.display = 'block';
                dlBtn.textContent = `Télécharger ${selected.size} facture(s) ZIP`;
                
                btn.disabled = false;
                btn.innerHTML = 'Générer les factures';
                
                dlSection.scrollIntoView({ behavior: 'smooth' });
            })
            .catch(e => {
                showAlert('Erreur: ' + e.message, 'error');
                btn.disabled = false;
                btn.innerHTML = 'Générer les factures';
            });
        }
        
        function updateMode() {
            const mode = document.getElementById('modeSelect').value;
            
            if (mode === 'groupe') {
                const uniqueClients = new Set(transactions.map(tx => tx.client));
                const count = `${selected.size}`;
                document.getElementById('genBtn').textContent = `Générer ${uniqueClients.size} facture(s) groupée(s)`;
            } else {
                document.getElementById('genBtn').textContent = `Générer ${selected.size} facture(s)`;
            }
        }
        
        // Initialisation
        if (selectedFiles.length > 0) renderFiles();
    </script>
</body>
</html>'''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

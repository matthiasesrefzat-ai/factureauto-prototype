```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from models import Invoice, InvoiceCreate, InvoiceResponse
from database import get_db, init_db
from datetime import datetime

# Initialisation de l'application FastAPI
app = FastAPI(title="API de Facturation", description="Gestion des factures en asynchrone.")

# ----------------------------------------------------------------------
# DÉPENDANCES ET INITIALISATION
# ----------------------------------------------------------------------

@app.on_event("startup")
async def startup_event():
    """Fonction exécutée au démarrage de l'application."""
    # Initialise la DB au démarrage
    init_db()

def get_db_dependency():
    """Fournit la dépendance de base de données."""
    return get_db()


# ----------------------------------------------------------------------
# ENDPOINTS DE L'API
# ----------------------------------------------------------------------

@app.get("/")
async def read_root():
    """Endpoint de bienvenue."""
    return {"message": "Bienvenue à l'API de Facturation. Utilisez /invoices pour commencer."}

@app.post("/invoices/", response_model=InvoiceResponse, status_code=201)
async def create_invoice(
    invoice_data: InvoiceCreate, db: Session = Depends(get_db_dependency)
):
    """
    Crée une nouvelle facture et déclenche le traitement asynchrone.
    """
    db_invoice = Invoice(
        customer_name=invoice_data.customer_name, 
        amount=invoice_data.amount,
        status="PROCESSING" # Statut initial
    )
    
    # 1. Sauvegarde en DB
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    
    # 2. Déclenchement du traitement en arrière-plan (Simulation asynchrone)
    # Utiliser asyncio.create_task pour ne pas bloquer la réponse HTTP.
    from asyncio import create_task
    import asyncio
    
    # Création de la tâche qui va exécuter le traitement de fond
    asyncio.create_task(process_invoice_async(db_invoice.id, db))
    
    return db_invoice


@app.get("/invoices/", response_model=List[InvoiceResponse])
async def read_all_invoices(db: Session = Depends(get_db_dependency)):
    """Récupère la liste de toutes les factures."""
    invoices = db.query(Invoice).all()
    return invoices

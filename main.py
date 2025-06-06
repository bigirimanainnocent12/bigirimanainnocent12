
from fastapi import FastAPI, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from typing import List
from database import SessionLocal
import models
import query_helper as helpers
import schemas  # Ajouté pour utiliser les schémas Pydantic
import os
from insert_data import import_excel_files, insert_data_details_fermentation, insert_data_donnee_fermentation, import_excel_files_donne_Fermentation

from fastapi.responses import Response



app = FastAPI(
    title="Lallemand oenologie: Fermentation API", 
    description="API pour interroger la base de données Lallemand_oenologie", 
    version="0.2"
)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)
# Initialisation de l'application FastAPI

# Dépendance pour récupérer une session DB
def get_db():
    """
    Cette fonction crée une session de base de données et la ferme après utilisation.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoint de health check
@app.get(
    "/",
    summary="Vérifie si l'API Fermentation fonctionne",
    description="""
    Ce point d'entrée permet de vérifier si l'API Fermentation est
    opérationnelle. 
    """,
    response_description="Un message de confirmation si l'API fonctionne correctement.",
    operation_id="health_check_Fermentation_api",
    tags=["monitoring"],
)
async def root():
    """
    Retourne un message de confirmation indiquant que l'API Fermentation est opérationnelle.
    """
    return {"message": "API Fermentation opérationnelle"}

# Endpoint pour obtenir une fermentation par son Code
@app.get(
    "/fermentation/{Code}",
    summary="Obtenir une fermentation par son Code",
    response_description="Retourne les informations d’une fermentation en utilisant son Code.",
    response_model=List[schemas.FermentationBase],  # Modifié pour retourner une liste de schémas
    tags=["Détails Fermentation"],
)
def read_fermentation(Code: str = Path(..., description="L'identifiant unique d'une Fermentation"), db: Session = Depends(get_db)):
    """
    Retourne les informations d’une fermentation en utilisant son Code.
    Si la fermentation n'est pas trouvée, une exception HTTP 404 est levée.
    """
    donnees = helpers.get_fermentation(db, Code)  
    if donnees:
        result = []
        for donne in donnees:
            result.append(schemas.FermentationBase(
                Code=donne.Code,
                Souche=donne.Souche,
                Milieu=donne.Milieu,
                volume=donne.volume,
                Csg_T=donne.Csg_T,
                Type_fermentation=donne.Type_fermentation
            ))
        return result
    else:
        raise HTTPException(status_code=404, detail=f"Les informations pour cette fermentation {Code} non trouvées")

# Endpoint pour obtenir les données de la fermentation par son Code
@app.get(
    "/donnee/{Code}",
    summary="Obtenir les données de la fermentation",
    response_description="Retourne les données d’une fermentation en utilisant le Code fermentation.",
    response_model=List[schemas.DonneeBase],  
    tags=["Données"],
)
def read_donnee(Code: str = Path(..., description="L'identifiant unique d'une Fermentation"), db: Session = Depends(get_db)):
    """
    Retourne les données d’une fermentation en utilisant le Code fermentation.
    Si les données ne sont pas trouvées, une exception HTTP 404 est levée.
    """
    donnee = helpers.get_donnee(db, Code)
    if donnee:
        result = []
        for donn in donnee:
            result.append(schemas.DonneeBase(
                id=donn.id,
                Temps=donn.Temps,
                CO2=donn.CO2,
                V=donn.V,
                Code=donn.Code
            ))
        return result
    else:
        raise HTTPException(status_code=404, detail=f"données pour cette fermentation {Code} non trouvées")

# Endpoint pour obtenir les données de fermentation et de donnee par son Code
@app.get(
    "/fermentation_donnee/{Code}",
    summary="Obtenir les données de fermentation et de donnee par son Code",
    response_description="Retourne les informations de fermentation et les données associées en utilisant le Code fermentation.",
    response_model=schemas.FermentationDonnee,  
    tags=["Fermentation et Donnée"],
)
def read_fermentation_donnee(Code: str = Path(..., description="L'identifiant unique d'une Fermentation"), db: Session = Depends(get_db)):
    """
    Retourne les informations de fermentation et les données associées en utilisant le Code fermentation.
    Si les informations ne sont pas trouvées, une exception HTTP 404 est levée.
    """
    fermentation = helpers.get_fermentation(db, Code)
    donnee = helpers.get_donnee(db, Code)
    if fermentation and donnee:
        fermentation_result = []
        for f in fermentation:
            fermentation_result.append(schemas.FermentationBase(
                Code=f.Code,
                Souche=f.Souche,
                Milieu=f.Milieu,
                volume=f.volume,
                Csg_T=f.Csg_T,
                Type_fermentation=f.Type_fermentation
            ))
        
        donnee_result = []
        for d in donnee:
            donnee_result.append(schemas.DonneeBase(
                id=d.id,
                Temps=d.Temps,
                CO2=d.CO2,
                V=d.V,
                Code=d.Code
            ))
        
        return schemas.FermentationDonnee(
            fermentation=fermentation_result,
            donnee=donnee_result
        )
    else:
        raise HTTPException(status_code=404, detail=f"Les informations pour cette fermentation {Code} non trouvées")

from dataclasses import dataclass
from typing import Optional


@dataclass()
class Etablissement:
    nic: str # Code nic
    siret: str # Siret de l'établissement
    denomination_unite_legale: str # Dénomination de l'unité légale rattachée
    est_siege: bool # Est-ce que l'établissement est le siège
    enseigne: Optional[str] # Enseigne de l'établissement


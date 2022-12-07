from flask_migrate import Migrate

# XXX: Il est important d'importer les modèles au préalable pour les
# scripts de migration.
from app.models.publication_model import Publication, Acte, PieceJointe
from app.models.entite_pastell_ag import EntitePastellAG
from app.models.parametrage_model import Parametrage

from app.models.mq_budget.parametrage import ParametresDefaultVisualisation

migrate = Migrate()

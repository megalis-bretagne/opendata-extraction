from celery.exceptions import Ignore

from app import celeryapp, db
from app.models.parametrage_model import Parametrage
from app.tasks import api_insee_call

celery = celeryapp.celery


class InseeFailure(Exception):
    pass


@celery.task(name='valorisation_nic_denomination', bind=True)
def valorisation_nic_denomination(self, siren):
    parametrage = Parametrage.query.filter(Parametrage.siren == siren).first()
    if parametrage is None:
        return {'status': 'Ok', 'message': 'Pas de parametrage existant'}
    etablissement = api_insee_call(siren)
    if etablissement is None:
        raise InseeFailure('L\'établisement' + siren + ' n\'existe pas ou api entreprise est injoignable')
    parametrage.nic = etablissement.nic
    parametrage.denomination = etablissement.denominationUniteLegale
    db_sess = db.session
    db_sess.add(parametrage)
    db_sess.commit()

    return {'status': 'Ok', 'message': 'Nic et raison social mis à jour pour ' + siren}


@celery.task(name='valorisation_all_nic_denomination', bind=True)
def valorisation_all_nic_denomination(self):
    all_parametrage = Parametrage.query.all()
    index = 0
    for parametrage in all_parametrage:
        valorisation_nic_denomination.apply_async(args=[parametrage.siren], countdown=(int(index / 1000) * 70))
        index = index + 1
    return {'status': 'Ok', 'message': 'tous les nic et raison social vont être mis à jour'}

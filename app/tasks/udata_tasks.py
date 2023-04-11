import time

from flask import current_app
from app import celeryapp
from app.models.parametrage_model import Parametrage
from app.service.udata.DatasetService import DatasetService
from app.service.udata.OrganizationService import OrganizationService
from app.tasks import generated_scdl_deliberation, generated_decp, SDMException
from app.tasks.datagouv_tasks import generated_scdl_budget

celery = celeryapp.celery


@celery.task(name='publication_udata_budget')
def publication_udata_budget(siren, annee):

    dataset_service = DatasetService()
    organization_service = OrganizationService()
    organization = organization_service.get(siren)
    dataset_budget = organization_service.get_dataset_budget(organization['id'])

    with generated_scdl_budget(siren=siren, annee=annee, flag_active='opendata_active') as csv_filepath:
        if dataset_budget is None:
            dataset_budget = dataset_service.create_dataset_budget(organization)
        if is_scdl_empty(csv_filepath):
            dataset_service.delete_resource_from_fp(dataset_budget, file_path=csv_filepath)
            return {'status': 'OK', 'message': 'budget vide', 'siren': str(siren),
                    'annee': str(annee)}
        
        titre = f"budget-{siren}-{annee}.csv"
        api_opendata_resource_url = _api_opendata_resource_url('scdl/budget', siren, annee)
        resultat = dataset_service.add_resource_budget_url(dataset_budget, titre, api_opendata_resource_url)

        if resultat is None:
            return {'status': 'KO', 'message': 'generation et publication budget', 'siren': str(siren),
                    'annee': str(annee)}
        return {'status': 'OK', 'message': 'generation et publication budget', 'siren': str(siren),
                'annee': str(annee)}


@celery.task(name='publication_udata_deliberation')
def publication_udata_deliberation(siren, annee):

    dataset_service = DatasetService()
    organization_service = OrganizationService()

    organization = organization_service.get(siren)
    dataset_deliberation = organization_service.get_dataset_deliberation(organization['id'])

    with generated_scdl_deliberation(siren = siren, annee = annee, flag_active='opendata_active') as scdl_delib_filepath:
        if dataset_deliberation is None:
            dataset_deliberation = dataset_service.create_dataset_deliberation(organization)
        if is_scdl_empty(scdl_delib_filepath):
            dataset_service.delete_resource_from_fp(dataset_deliberation, file_path=scdl_delib_filepath)
            return {'status': 'OK', 'message': 'deliberation vide', 'siren': str(siren),
                    'annee': str(annee)}

        titre = f"deliberation-{siren}-{annee}.csv"
        api_opendata_resource_url = _api_opendata_resource_url('scdl/deliberation', siren, annee)
        resultat = dataset_service.add_resource_deliberation_url(dataset_deliberation, titre, api_opendata_resource_url)

        if resultat is None:
            return {'status': 'KO', 'message': 'generation et publication deliberation', 'siren': str(siren),
                    'annee': str(annee)}
        return {'status': 'OK', 'message': 'generation et publication deliberation', 'siren': str(siren),
                'annee': str(annee)}


@celery.task(name='publication_udata_decp')
def publication_udata_decp(siren, annee):

    dataset_service = DatasetService()
    organization_service = OrganizationService()

    with generated_decp(annee = annee, siren = siren) as decp_filepath:
        if decp_filepath is None:
            raise SDMException('erreur lors de l\'appel SDM pour l\'annee {} et le siren {}  '.format(annee, siren))
        organization = organization_service.get(siren)
        dataset_decp = organization_service.get_dataset_decp(organization['id'])
        if dataset_decp is None:
            dataset_decp = dataset_service.create_dataset_decp(organization)
        if is_decp_empty(decp_filepath):
            dataset_service.delete_resource_from_fp(dataset_decp, file_path=decp_filepath)
            return {'status': 'OK', 'message': 'decp vide', 'siren': str(siren),
                    'annee': str(annee)}

        titre = f"decp-{siren}{annee}.xml" # XXX: oui, pas de tiret entre siren et années pour decp
        api_opendata_resource_url = _api_opendata_resource_url('decp', siren, annee)
        resultat = dataset_service.add_resource_decp_url(dataset_decp, titre, api_opendata_resource_url)

        if resultat is None:
            return {'status': 'KO', 'message': 'generation et publication decp', 'siren': str(siren),
                    'annee': str(annee)}
        return {'status': 'OK', 'message': 'generation et publication decp', 'siren': str(siren),
                'annee': str(annee)}


@celery.task(name='publication_udata')
def publication_udata(annee=None):
    if annee is None:
        t = time.localtime()
        annee = time.strftime('%Y', t)

    organization_service = OrganizationService()
    sirens = organization_service.get_all_sirens()
    for siren in sirens:
        parametrage = Parametrage.query.filter(Parametrage.siren == siren).first()
        if parametrage is None or parametrage.publication_udata_active:
            publication_udata_deliberation.delay(siren, annee)
            publication_udata_budget.delay(siren, annee)
        publication_udata_decp.delay(siren, annee)


@celery.task(name='publication_udata_decp_histo')
def publication_udata_decp_histo():
    annee_debut = 2014
    t = time.localtime()
    annee_courante = int(time.strftime('%Y', t))

    organization_service = OrganizationService()
    sirens = organization_service.get_all_sirens()
    for siren in sirens:
        annee_a_generer = annee_debut
        while annee_courante >= annee_a_generer:
            publication_udata_decp.delay(siren, str(annee_a_generer))
            annee_a_generer += 1

    return {'status': 'OK', 'message': 'generation et publication decp histo'}


def is_scdl_empty(filename):
    with open(filename, 'r') as fp:
        for count, _ in enumerate(fp):
            if count > 0:
                return False
        return True


def is_decp_empty(filename):
    with open(filename, 'r') as fp:
        for count, line in enumerate(fp):
            if count == 1 and line.startswith("<marches/>"):
                return True
            elif count > 1:
                return False

def _urljoin(*args):
    return "/".join(map(lambda x: str(x).rstrip('/'), args))

def _api_opendata_baseurl():
    catalogue_regional = current_app.config['CATALOGUE_REGIONAL']
    return catalogue_regional['API_OPEN_DATA_BASEURL']

def _api_opendata_resource_url(resource: str, siren: str, annee):
    base: str = _api_opendata_baseurl()
    suffix = f"{resource}/{siren}/{annee}"
    url = _urljoin(base, suffix)
    return url

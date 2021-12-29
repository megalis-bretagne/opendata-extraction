from app import celeryapp
from app.service.udata_megalis.DatasetService import DatasetService
from app.service.udata_megalis.OrganizationService import OrganizationService
from app.tasks import generation_budget, generation_deliberation, generation_decp

celery = celeryapp.celery


@celery.task(name='publication_udata_megalis_budget')
def publication_udata_megalis_budget(siren, annee):
    dataset_service = DatasetService()
    organization_service = OrganizationService()
    filename = generation_budget(siren, annee)
    organization = organization_service.get(siren)
    dataset_budget = organization_service.get_dataset_budget(organization['id'])
    if dataset_budget is None:
        dataset_budget = dataset_service.create_dataset_budget(organization)

    resultat = dataset_service.add_resource_budget(dataset_budget, filename)
    if resultat is None:
        return {'status': 'KO', 'message': 'generation et publication budget', 'siren': str(siren),
                'annee': str(annee)}
    return {'status': 'OK', 'message': 'generation et publication budget', 'siren': str(siren),
            'annee': str(annee)}


@celery.task(name='publication_udata_megalis_deliberation')
def publication_udata_megalis_deliberation(siren, annee):
    dataset_service = DatasetService()
    organization_service = OrganizationService()
    filename = generation_deliberation(siren, annee)
    organization = organization_service.get(siren)
    dataset_deliberation = organization_service.get_dataset_deliberation(organization['id'])
    if dataset_deliberation is None:
        dataset_deliberation = dataset_service.create_dataset_deliberation(organization)

    resultat = dataset_service.add_resource_deliberation(dataset_deliberation, filename)
    if resultat is None:
        return {'status': 'KO', 'message': 'generation et publication deliberation', 'siren': str(siren),
                'annee': str(annee)}
    return {'status': 'OK', 'message': 'generation et publication deliberation', 'siren': str(siren),
            'annee': str(annee)}


@celery.task(name='publication_udata_megalis_decp')
def publication_udata_megalis_decp(siren, annee):
    dataset_service = DatasetService()
    organization_service = OrganizationService()
    filename = generation_decp(annee, siren)
    organization = organization_service.get(siren)
    dataset_decp = organization_service.get_dataset_decp(organization['id'])
    if dataset_decp is None:
        dataset_decp = dataset_service.create_dataset_decp(organization)

    resultat = dataset_service.add_resource_decp(dataset_decp, filename)
    if resultat is None:
        return {'status': 'KO', 'message': 'generation et publication decp', 'siren': str(siren),
                'annee': str(annee)}
    return {'status': 'OK', 'message': 'generation et publication decp', 'siren': str(siren),
            'annee': str(annee)}

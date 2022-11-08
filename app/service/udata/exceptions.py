from typing import Union


class GetOrganisationError(Exception):
    def __init__(self, siren: str, message: str, *args: object) -> None:
        self.siren = siren
        self.message = message
        super().__init__(siren, message, *args)


class OrganisationIntrouvableError(GetOrganisationError):
    def __init__(self, siren: str) -> None:
        msg = f"L'organisation correspondant au siren {siren} est introuvable"
        super().__init__(siren, msg)


class OrganisationNonUniqueError(GetOrganisationError):
    def __init__(self, combien: int, siren: str) -> None:
        self.combien = combien
        msg = f"{combien} organisations correspondent au siren {siren}"
        super().__init__(siren, msg)


class OrganisationUnexpectedApiStatusError(GetOrganisationError):
    def __init__(
        self,
        siren: str,
        http_status: Union[int, None],
    ) -> None:
        self.http_status = http_status
        msg = f"Status {http_status} inattendu."
        super().__init__(siren, msg, http_status)


def _wrap_get_organisation_errors(func):
    def inner(*args, **kwargs):
        try:
            siren = args[1]
            return func(*args, **kwargs)
        except GetOrganisationError as err:
            raise err
        except Exception as err:
            raise GetOrganisationError(
                siren, "Une erreur inconnue est survenue"
            ) from err

    return inner

from prometheus_client import Histogram

_buckets = (
    "0.005",
    "0.01",
    "0.025",
    "0.05",
    "0.075",
    "0.1",
    "0.25",
    "0.5",
    "0.75",
    "1.0",
    "2.5",
    "5.0",
    "7.5",
    "10.0",
    "25.0",
    "50.0",
    "75.0",
    "100.0",
    "+Inf",
)

LISTE_TOTEM_METADATA_HISTOGRAM = Histogram(
    "liste_totem_metadata_seconds",
    "Temps passé à calculer les liste totem metadata",
    buckets=_buckets,
)


READ_SCDL_AS_STR = Histogram(
    "read_scdl_as_str",
    "Temps passé à lire un SCDL",
    buckets=_buckets,
)


CONVERTIR_XML_TO_SCDL = Histogram(
    "convertir_xml_to_scdl",
    "Temps passé à convertir un XML pour le transformer en SCDL",
    buckets=_buckets,
)

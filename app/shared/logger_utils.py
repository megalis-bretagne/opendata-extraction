import os
import logging
from sys import stderr
from typing import Optional
from pygelf import GelfUdpHandler

from functools import cache

GELF_HOST_KEY = "GELF_HOST"
GELF_PORT_KEY = "GELF_PORT"
GELF_PROTO_KEY = "GELF_PROTO"

SERVICE_NAME = "opendata-extraction"

@cache
def create_or_get_gelf_loghandler() -> Optional[logging.Handler]:
    handler = None

    host = os.environ.get(GELF_HOST_KEY)
    port = os.environ.get(GELF_PORT_KEY)
    proto = os.environ.get(GELF_PROTO_KEY)

    if not all([host, port, proto]):
        if any([host,port, proto]):
            stderr.write(f"Vous devez spécifier {GELF_HOST_KEY}, {GELF_PORT_KEY} et {GELF_PROTO_KEY}\n")
        return None
    
    proto = proto.lower() # type: ignore
    host = host.lower() # type: ignore
    port = int(port) # type: ignore

    if proto != "udp":
        stderr.write(f"Seul UDP est supporté pour {GELF_PROTO_KEY}\n")
    
    additionnal_fields = {
        "service": SERVICE_NAME,
    }

    handler = GelfUdpHandler(host=host, port=port, compress = False, debug=True, **additionnal_fields)
    # handler = GelfUdpHandler(host=host, port=port, **additionnal_fields)
    
    return handler
        

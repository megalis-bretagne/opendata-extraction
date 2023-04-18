import csv
from datetime import datetime
import hashlib
import logging
from pathlib import Path
from urllib.parse import quote

import pysolr, re, os, errno, shutil
import requests
from bs4 import BeautifulSoup
import paramiko
from flask import current_app


def get_hash(filePath):
    BLOCK_SIZE = 65536  # The size of each read from the file
    file_hash = hashlib.sha256()
    with open(filePath, 'rb') as f:  # Open the file to read it's bytes
        fb = f.read(BLOCK_SIZE)  # Read from the file. Take in the amount declared above
        while len(fb) > 0:  # While there is still data being read from the file
            file_hash.update(fb)  # Update the hash
            fb = f.read(BLOCK_SIZE)  # Read the next block from the file
    return file_hash.hexdigest()


def solr_connexion():
    solr_address = current_app.config['URL_SOLR'] + "{}".format(current_app.config['INDEX_DELIB_SOLR'])
    solr = pysolr.Solr(solr_address, always_commit=True, timeout=120,
                       auth=(current_app.config['USER_SOLR'], current_app.config['PASSWORD_SOLR']))
    solr.log.setLevel('WARN')
    # # Do a health check.
    solr.ping()
    return solr


def index_file_in_solr(path, params):
    with open(path, 'rb') as file_obj:
        filename = quote(file_obj.name.encode("utf-8"))
        solr_address = current_app.config['URL_SOLR'] + "{}".format(current_app.config['INDEX_DELIB_SOLR'])
        handler = "/update/extract"
        requests.post(
            solr_address + handler,
            params=params,
            json={
                "extractOnly": "false",
                "lowernames": "true",
                "wt": "json"
            },
            files={"file": (filename, file_obj)}
        )



def solr_clear_all():
    solr_address = current_app.config['URL_SOLR'] + "{}".format(current_app.config['INDEX_DELIB_SOLR'])
    solr = pysolr.Solr(solr_address, always_commit=True, timeout=10,
                       auth=(current_app.config['USER_SOLR'], current_app.config['PASSWORD_SOLR']))
    # # Do a health check.
    solr.ping()
    solr.delete(q='*:*')
    return solr


def str_rep(in_str):
    in_str = in_str.replace("\n", '')
    out_str = re.sub('\s+', ' ', in_str)
    out_str = re.sub("[.]+", '', out_str)
    return out_str


def extract_content(solr_data, format):
    soup = BeautifulSoup(solr_data, format)
    out = [str_rep(x) for x in soup.stripped_strings]
    return " ".join(out)


def remove_file_sur_serveur(pathFile):
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=current_app.config['DEPOT_HOSTNAME'], username=current_app.config['DEPOT_USERNAME'],
                password=current_app.config['DEPOT_PASSWORD'])
    # creation du repertoire si il n'existe pas
    ssh.exec_command("rm -f " + pathFile)
    ssh.close()


# def scp_sur_serveur(path,remote_path):
#    ssh = paramiko.SSHClient()
#    ssh.load_system_host_keys()
#    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#    ssh.connect(hostname=current_app.config['DEPOT_HOSTNAME'],username=current_app.config['DEPOT_USERNAME'],password=current_app.config['DEPOT_PASSWORD'])
#    # creation du repertoire si il n'existe pas
#    ssh.exec_command("mkdir -p "+remote_path)
#    # SCPCLient takes a paramiko transport as an argument
#    scp = SCPClient(ssh.get_transport())
#    scp.put(path,remote_path=remote_path)
#    scp.close()
#
# def scp_sur_serveur_change_name(path, remote_path,nouveau_nom):
#    ssh = paramiko.SSHClient()
#    ssh.load_system_host_keys()
#    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#    ssh.connect(hostname=current_app.config['DEPOT_HOSTNAME'], username=current_app.config['DEPOT_USERNAME'],
#                password=current_app.config['DEPOT_PASSWORD'])
#    # creation du repertoire si il n'existe pas
#    ssh.exec_command("mkdir -p " + remote_path)
#    # SCPCLient takes a paramiko transport as an argument
#    scp = SCPClient(ssh.get_transport())
#    scp.put(path, remote_path=remote_path+'/'+nouveau_nom)
#    scp.close()

def move_file(path, new_path, filename):
    # Create the directory
    try:
        os.makedirs(new_path, exist_ok=True)
        logging.info("Directory '%s' created successfully" % new_path)
    except OSError:
        logging.info("Directory '%s' can not be created" % new_path)
    shutil.move(path, new_path + filename)


def copy_file(path, new_path, filename):
    # Create the directory
    try:
        os.makedirs(new_path, exist_ok=True)
        logging.info("Directory '%s' created successfully" % new_path)
    except OSError:
        logging.info("Directory '%s' can not be created" % new_path)
    shutil.copyfile(path, new_path + filename)


def symlink_file(path, new_path, filename):
    # Create the directory
    try:
        os.makedirs(new_path, exist_ok=True)
        logging.info("Directory '%s' created successfully" % new_path)
    except OSError:
        logging.info("Directory '%s' can not be created" % new_path)
    try:
        os.symlink(path, new_path + filename)
    except FileExistsError:
        logging.exception("le lien existe deja")

def unsymlink_file(dir, filename):
    try:
        p = Path(dir) / filename
        if not os.path.exists(p):
            logging.debug(f"Tentative de suppression d'un lien inexistant. On ignore.")
            return
        if not os.path.islink(p):
            logging.warning(f"Tentative de suppression d'un lien sur un objet qui n'est pas un lien: {p}")
            return
        os.unlink(p)
    except Exception as e:
        logging.exception(e)

nature_actes_dict = dict()
nature_actes_dict[1] = "Délibérations"
nature_actes_dict[2] = "Actes réglementaires"
nature_actes_dict[3] = "Actes individuels"
nature_actes_dict[4] = "Contrats,conventions et avenants"
nature_actes_dict[5] = "Documents budgétaires et financiers"
nature_actes_dict[6] = "Autres"

class PastellApiException(Exception):
    pass

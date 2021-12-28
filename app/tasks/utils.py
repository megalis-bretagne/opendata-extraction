import logging
import pysolr, re, os, errno, shutil
from bs4 import BeautifulSoup
import paramiko
from functools import lru_cache
from api_insee import ApiInsee
from flask import current_app

@lru_cache(maxsize=32)
def api_insee_call(siren):
    api = ApiInsee(
        key = current_app.config['API_SIREN_KEY'],
        secret = current_app.config['API_SIREN_SECRET'],
    )
    data = api.siret(q={
        'siren': siren,
        'etablissementSiege':True
    }).get()
    #todo Sirene    API    calls    limit    exceeded, must    wait    60    sec
    #} else if ($response != NULL & & isset($response->fault) & & $response->fault->code == 900804) {
    return data

def solr_connexion():
    solr_address = current_app.config['URL_SOLR']+"{}".format( current_app.config['INDEX_DELIB_SOLR'])
    solr = pysolr.Solr(solr_address, always_commit=True, timeout=120, auth=(current_app.config['USER_SOLR'], current_app.config['PASSWORD_SOLR']))
    # # Do a health check.
    solr.ping()
    return solr

def solr_clear_all():
    solr_address = current_app.config['URL_SOLR']+"{}".format( current_app.config['INDEX_DELIB_SOLR'])
    solr = pysolr.Solr(solr_address, always_commit=True, timeout=10, auth=(current_app.config['USER_SOLR'], current_app.config['PASSWORD_SOLR']))
    # # Do a health check.
    solr.ping()
    solr.delete(q='*:*')
    return solr

def str_rep(in_str):
    in_str = in_str.replace("\n", '')
    out_str = re.sub('\s+', ' ', in_str)
    out_str = re.sub("[.]+", '', out_str)
    return out_str

def extract_content(solr_data,format):
    soup = BeautifulSoup(solr_data, format)
    out = [str_rep(x) for x in soup.stripped_strings]
    return " ".join(out)

def remove_file_sur_serveur(pathFile):
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=current_app.config['DEPOT_HOSTNAME'],username=current_app.config['DEPOT_USERNAME'],password=current_app.config['DEPOT_PASSWORD'])
    # creation du repertoire si il n'existe pas
    ssh.exec_command("rm -f "+pathFile)
    ssh.close()


#def scp_sur_serveur(path,remote_path):
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
#def scp_sur_serveur_change_name(path, remote_path,nouveau_nom):
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

def clear_wordir():
    WORKDIR = get_or_create_workdir()
    filelist = [ f for f in os.listdir(WORKDIR) ]
    for f in filelist:
        os.remove(os.path.join(WORKDIR, f))


def get_or_create_workdir():
    WORKDIR = current_app.config['WORKDIR']
    # create workdir
    try:
        os.mkdir(WORKDIR)
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise
        pass
    return WORKDIR


def move_file(path,new_path,filename):
    # Create the directory
    try:
        os.makedirs(new_path, exist_ok=True)
        logging.info("Directory '%s' created successfully" % new_path)
    except OSError:
        logging.info("Directory '%s' can not be created" % new_path)
    shutil.move(path, new_path + filename)

def copy_file(path,new_path,filename):
    # Create the directory
    try:
        os.makedirs(new_path, exist_ok=True)
        logging.info("Directory '%s' created successfully" % new_path)
    except OSError:
        logging.info("Directory '%s' can not be created" % new_path)
    shutil.copyfile(path, new_path + filename)


def symlink_file(path,new_path,filename):
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

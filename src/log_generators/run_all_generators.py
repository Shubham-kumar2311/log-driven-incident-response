import threading
from auth_service import run as auth_run
from api_gateway import run as api_run
from db_monitor import run as db_run
from deployment_service import run as deploy_run
from k8s_runtime import run as k8s_run


threads = [
    threading.Thread(target=auth_run, args=("normal",)),
    threading.Thread(target=api_run, args=("normal",)),
    threading.Thread(target=db_run, args=("normal",)),
    threading.Thread(target=deploy_run, args=("normal",)),
    threading.Thread(target=k8s_run, args=("normal",)),
]

for t in threads:
    t.start()   

for t in threads:
    t.join()
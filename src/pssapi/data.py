from json import load as _json_load
import os as _os
from typing import Dict as _Dict



# ---------- Constants ----------

__ID_NAMES_FILEPATH: str = None
ID_NAMES_INFO: _Dict[str, str] = None

__PWD: str = None


# ---------- Initialization ----------

__PWD = _os.getcwd()
if '/src' in __PWD:
    __PWD = f'{__PWD}/pssapi/'
else:
    __PWD = f'{__PWD}/src/pssapi/'

__ID_NAMES_FILEPATH = f'{__PWD}id_names.json'

with open(__ID_NAMES_FILEPATH) as fp:
    ID_NAMES_INFO = _json_load(fp)
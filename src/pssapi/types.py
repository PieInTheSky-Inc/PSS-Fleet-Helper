from typing import Dict as _Dict
from typing import List as _List
from typing import Union as _Union



EntityInfo = _Dict[str, 'EntityInfo']
EntitiesData = _Dict[str, EntityInfo]
EntityDict = _Union[_List['EntityDict'], _Dict[str, 'EntityDict']]
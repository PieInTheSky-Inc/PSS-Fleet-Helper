from datetime import datetime as _datetime
from enum import Enum as _Enum
from typing import Dict as _Dict
from typing import Optional as _Optional
import pytz as _pytz
from xml.etree import ElementTree as _ElementTree
from xml.etree.ElementTree import ParseError as _XmlParseError
from errors import PssXmlError as _PssXmlError


from .data import ID_NAMES_INFO as _ID_NAMES_INFO

from .types import EntitiesData as _EntitiesData
from .types import EntityDict as _EntityDict



# ---------- Constants ----------

__BOOL_VALUE_LOOKUP: _Dict[str, bool] = {
    'true': True,
    'false': False,
}

__API_DATETIME_FORMAT_ISO: str = '%Y-%m-%dT%H:%M:%S'
__API_DATETIME_FORMAT_ISO_DETAILED: str = '%Y-%m-%dT%H:%M:%S.%f'





# ---------- Type conversions ----------

def str_to_boolean(raw_value: str) -> _Optional[bool]:
    if raw_value:
        return __BOOL_VALUE_LOOKUP[raw_value]
    else:
        return None


def str_to_datetime(raw_value: str) -> _Optional[_datetime]:
    result = None
    if raw_value:
        try:
            result = _datetime.strptime(raw_value, __API_DATETIME_FORMAT_ISO)
        except ValueError:
            result = _datetime.strptime(raw_value, __API_DATETIME_FORMAT_ISO_DETAILED)
        result = _pytz.utc.localize(result)
    return result



def str_to_int(raw_value: str, default: int = None) -> _Optional[int]:
    if raw_value:
        return int(raw_value)
    else:
        return default


def str_to_enum(raw_value: str, enum: _Enum) -> _Optional[_Enum]:
    if raw_value:
        return enum[raw_value]
    else:
        return None





# ---------- XML conversions ----------

def raw_xml_to_dict(raw_xml: str, include_root: bool = True, fix_attributes: bool = True, preserve_lists: bool = False) -> _EntityDict:
    try:
        root = _ElementTree.fromstring(raw_xml)
    except _XmlParseError as e:
        raise _PssXmlError(raw_xml, e)
    result = __convert_xml_to_dict(root, include_root=include_root, fix_attributes=fix_attributes, preserve_lists=preserve_lists)
    return result


def xmltree_to_dict2(raw_text: str) -> _EntitiesData:
    return __xmltree_to_dict(raw_text, 2)


def xmltree_to_dict3(raw_text: str) -> _EntitiesData:
    return __xmltree_to_dict(raw_text, 3)


def __convert_xml_to_dict(root: _ElementTree.Element, include_root: bool = True, fix_attributes: bool = True, preserve_lists: bool = False) -> _EntityDict:
    if root is None:
        return None

    result = {}
    if root.attrib:
        if include_root:
            if fix_attributes:
                result[root.tag] = __fix_attribute(root.attrib)
            else:
                result[root.tag] = root.attrib
        else:
            if fix_attributes:
                result = __fix_attribute(root.attrib)
            else:
                result = root.attrib
    elif include_root:
        result[root.tag] = {}

    # Retrieve all distinct names of sub tags
    tag_count_map = __get_child_tag_count(root)
    children_dict = {}

    for child in root:
        tag = child.tag
        key = None
        if tag_count_map[tag] > 1:
            id_attr_names = _ID_NAMES_INFO.get(tag)
            if id_attr_names:
                id_attr_values = [child.attrib[id_attr_name] for id_attr_name in id_attr_names]
                key = '.'.join(sorted(id_attr_values))
        if not key:
            key = tag

        child_dict = __convert_xml_to_dict(child, include_root=False, fix_attributes=fix_attributes, preserve_lists=preserve_lists)
        if key not in children_dict.keys():
            children_dict[key] = child_dict

    if children_dict:
        if preserve_lists:
            if len(children_dict) > 1:
                children_list = list(children_dict.values())
                if include_root:
                    result[root.tag] = children_list
                else:
                    if result:
                        result['Collection'] = children_list
                    else:
                        result = children_list
            else:
                result.setdefault(root.tag, {}).update(children_dict)
        else:
            if include_root:
                # keys get overwritten here
                result[root.tag] = children_dict
            else:
                result.update(children_dict)

    return result


def __fix_attribute(attribute: _Dict[str, str]) -> _Dict[str, str]:
    if not attribute:
        return None

    result = {}

    for key, value in attribute.items():
        if key.endswith('Xml') and value:
            raw_xml = value
            fixed_value = raw_xml_to_dict(raw_xml)
            result[key[:-3]] = fixed_value

        result[key] = value

    return result


def __get_child_tag_count(root: _ElementTree.Element) -> _Dict[str, int]:
    if root is None:
        return None

    child_tags = list(set([child_node.tag for child_node in root]))
    result = {}
    for child_tag in child_tags:
        result[child_tag] = sum(1 for child_node in root if child_node.tag == child_tag)

    return result


def __xmltree_to_dict(raw_text: str, depth: int) -> _EntitiesData:
    result = raw_xml_to_dict(raw_text)
    while depth > 0:
        found_new_root = False
        for value in result.values():
            if isinstance(value, dict):
                result = value
                depth -= 1
                found_new_root = True
                break
        if not found_new_root:
            return {}
    return result
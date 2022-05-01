from typing import Tuple as _Tuple
from xml.etree.ElementTree import ParseError as _XmlParseError



class PssApiError(Exception):
    def __str__(self) -> str:
        msg = [
            type(self).__name__,
            self.message
        ]

    def __repr__(self) -> str:
        return self.__str__()


class ServerMaintenanceError(PssApiError):
    pass


class PssXmlError(PssApiError, _XmlParseError):
    def __init__(self, raw_xml: str, parse_error: _XmlParseError):
        self.__raw_xml: str = raw_xml
        self.__parse_error: _XmlParseError = parse_error

    @property
    def raw_xml(self) -> str:
        return self.__raw_xml

    @property
    def position(self) -> _Tuple[int, int]:
        return self.__parse_error.position

import re


class PlaylistTag:
    def __init__(self, name: str, data: list[str] | dict[str, str] | None = None):
        self.name = name
        self.data = data

    def toString(self) -> str:
        if isinstance(self.data, dict):
            return f"#{self.name}:{','.join(f'{key}={value}' for key, value in self.data.items())}"
        elif isinstance(self.data, list):
            return f"#{self.name}:{','.join(self.data)}"
        else:
            return f"#{self.name}"

    def __eq__(self, other):
        if isinstance(other, PlaylistTag):
            return (self.name, self.data) == (other.name, other.data)
        else:
            return NotImplemented

    def __ne__(self, other):
        if isinstance(other, PlaylistTag):
            return (self.name, self.data) != (other.name, other.data)
        else:
            return NotImplemented



class PlaylistTagReader:
    TAG_WITH_DATA = re.compile("#(.*?):(.*)")
    TAG_WITHOUT_DATA = re.compile("#(.*)")

    @classmethod
    def getTag(self, string: str) -> PlaylistTag | None:
        tag = re.match(self.TAG_WITH_DATA, string)
        if tag == None:
            tag = re.match(self.TAG_WITHOUT_DATA, string)
            if tag == None:
                return None
            else:
                return PlaylistTag(tag.group(1))
        else:
            return PlaylistTag(tag.group(1), self._getTagData(tag.group(2)))

    @classmethod
    def _getTagData(self, line: str) -> list[str] | dict[str, str]:
        if "=" in line and not self._startsWithQuotation(line):
            tagData = self._parseDictString(line)
        else:
            tagData = self._parseListString(line)
        return tagData

    @classmethod
    def _startsWithQuotation(self, string: str) -> bool:
        return string.startswith("\'") or string.startswith("\"")

    @classmethod
    def _parseListString(self, line: str) -> list[str]:
        parsedLine = line.split(",")
        quotation = None
        data = []
        for string in parsedLine:
            if quotation == None:
                quotation = string[0] if self._startsWithQuotation(string) else None
                data.append(string)
                if quotation == None:
                    continue
            else:
                data[-1] = ",".join((data[-1], string))
            if string.endswith(quotation):
                data[-1] = data[-1].strip("\'\"").replace(f"\\{quotation}", quotation)
                quotation = None
        return data

    @classmethod
    def _parseDictString(self, line: str) -> dict[str, str]:
        parsedLine = line.split(",")
        quotation = None
        data = {}
        for string in parsedLine:
            if quotation == None:
                key, value = string.split("=", 1)
                quotation = value[0] if self._startsWithQuotation(value) else None
                data[key] = value
                if quotation == None:
                    continue
            else:
                value = string
                data[key] = ",".join((data[key], value))
            if value.endswith(quotation):
                data[key] = data[key].strip("\'\"")
                quotation = None
        return data
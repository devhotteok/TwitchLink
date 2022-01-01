import re


class PlaylistTag:
    def __init__(self, name, data):
        self.name = name
        self.data = data

class PlaylistReader:
    TAG_WITH_DATA = re.compile("#(.*?):(.*)")
    TAG_WITHOUT_DATA = re.compile("#(.*)")

    def getTag(self, string):
        tag = re.match(self.TAG_WITH_DATA, string)
        if tag == None:
            tag = re.match(self.TAG_WITHOUT_DATA, string)
            if tag == None:
                return None
            else:
                return PlaylistTag(tag.group(1), None)
        else:
            return PlaylistTag(tag.group(1), self.getTagData(tag.group(2)))

    def getTagData(self, line):
        if "=" in line:
            tagData = {}
            for data in line.split(","):
                try:
                    data = data.split("=")
                    tagData[data[0]] = data[1].strip("\"")
                except:
                    pass
        else:
            tagData = []
            for data in line.split(","):
                tagData.append(data)
        return tagData
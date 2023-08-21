import typing
import heapq


class PriorityQueue:
    def __init__(self):
        self._data = []
        self._index = 0

    def push(self, item: typing.Any, priority: int = 0) -> None:
        if len(self._data) == 0:
            self._index = 0
        heapq.heappush(self._data, (-priority, self._index, item))
        self._index += 1

    def pop(self) -> typing.Any:
        return heapq.heappop(self._data)[2]

    def removeItem(self, item: typing.Any) -> None:
        self._data.remove(next(queueData for queueData in self._data if queueData[2] == item))
        heapq.heapify(self._data)

    def removeItems(self, items: typing.Iterable[typing.Any]) -> None:
        for item in items:
            self._data.remove(next(queueData for queueData in self._data if queueData[2] == item))
        heapq.heapify(self._data)

    def __len__(self):
        return len(self._data)

    def __contains__(self, item):
        return any(queueData[2] == item for queueData in self._data)
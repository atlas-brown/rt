from dataclasses import dataclass
from collections.abc import Mapping
from typing import Self

from rt.regular_types.stream_transform import Constant, StreamTransform
from rt.regular_types.stream_type import StreamType


@dataclass(frozen=True)
class CommandType:
    accepted_input: StreamType | None
    transform: StreamTransform

    def apply(
        self, input: StreamType, holes: Mapping[str, StreamType]
    ) -> StreamType:
        return self.transform.apply(input, holes)

    @classmethod
    def simple(cls, accepted_input: StreamType | None, output: StreamType) -> Self:
        return cls(accepted_input, Constant(output))

    def is_simple(self) -> bool:
        return isinstance(self.transform, Constant)

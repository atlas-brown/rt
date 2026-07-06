from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from rt.constants import ALPHABET_SIZE
from rt.regex import ast
from rt.regular_types.stream_type import StreamType, StreamTypeTemplate
from rt.utils import char_set_complement


@dataclass(frozen=True)
class StreamTransform(ABC):
    @abstractmethod
    def apply(self, input: StreamType, holes: Mapping[str, StreamType]) -> StreamType:
        pass


@dataclass(frozen=True)
class Constant(StreamTransform):
    output: StreamType

    def apply(self, input: StreamType, holes: Mapping[str, StreamType]) -> StreamType:
        return self.output


@dataclass(frozen=True)
class Input(StreamTransform):
    def apply(self, input: StreamType, holes: Mapping[str, StreamType]) -> StreamType:
        return input


@dataclass(frozen=True)
class Regex(StreamTransform):
    regex_ast: ast.Regex

    def apply(self, input: StreamType, holes: Mapping[str, StreamType]) -> StreamType:
        if self.regex_ast.has_child_of_type(ast.Hole):
            return StreamTypeTemplate.from_regex(self.regex_ast).instantiate(holes)
        return StreamType.from_regex(self.regex_ast)


@dataclass(frozen=True)
class Union(StreamTransform):
    left: StreamTransform
    right: StreamTransform

    def apply(self, input: StreamType, holes: Mapping[str, StreamType]) -> StreamType:
        return self.left.apply(input, holes).union(self.right.apply(input, holes))


@dataclass(frozen=True)
class Intersection(StreamTransform):
    left: StreamTransform
    right: StreamTransform

    def apply(self, input: StreamType, holes: Mapping[str, StreamType]) -> StreamType:
        return self.left.apply(input, holes).intersect(self.right.apply(input, holes))


@dataclass(frozen=True)
class Concatenation(StreamTransform):
    left: StreamTransform
    right: StreamTransform

    def apply(self, input: StreamType, holes: Mapping[str, StreamType]) -> StreamType:
        return self.left.apply(input, holes).concatenate(self.right.apply(input, holes))


@dataclass(frozen=True)
class Subtraction(StreamTransform):
    left: StreamTransform
    right: StreamTransform

    def apply(self, input: StreamType, holes: Mapping[str, StreamType]) -> StreamType:
        return self.left.apply(input, holes).subtract(self.right.apply(input, holes))


@dataclass(frozen=True)
class Complement(StreamTransform):
    transform: StreamTransform

    def apply(self, input: StreamType, holes: Mapping[str, StreamType]) -> StreamType:
        return self.transform.apply(input, holes).complement()


@dataclass(frozen=True)
class Repetition(StreamTransform):
    transform: StreamTransform
    min: int
    max: int | None

    def apply(self, input: StreamType, holes: Mapping[str, StreamType]) -> StreamType:
        return self.transform.apply(input, holes).repeat(self.min, self.max)


@dataclass(frozen=True)
class Reversal(StreamTransform):
    transform: StreamTransform

    def apply(self, input: StreamType, holes: Mapping[str, StreamType]) -> StreamType:
        return self.transform.apply(input, holes).reverse()


# translate-match
@dataclass(frozen=True)
class Replacement(StreamTransform):
    transform: StreamTransform
    pattern: str | StreamType | StreamTransform
    replacement: str
    first_occurence_only: bool

    def apply(self, input: StreamType, holes: Mapping[str, StreamType]) -> StreamType:
        if isinstance(self.pattern, StreamTransform):
            pattern = self.pattern.apply(input, holes)
        else:
            pattern = self.pattern
        return self.transform.apply(input, holes).replace(
            pattern, self.replacement, self.first_occurence_only
        )


# line-extract
@dataclass(frozen=True)
class Match(StreamTransform):
    transform: StreamTransform
    pattern: str | StreamType | StreamTransform

    def apply(self, input: StreamType, holes: Mapping[str, StreamType]) -> StreamType:
        if isinstance(self.pattern, StreamTransform):
            pattern = self.pattern.apply(input, holes)
        else:
            pattern = self.pattern
        return self.transform.apply(input, holes).match(pattern)


# translate-chars
@dataclass(frozen=True)
class CharTranslation(StreamTransform):
    transform: StreamTransform
    chars: str
    replacements: str
    use_complement_of_chars: bool
    squeeze_repetitions: bool

    def apply(self, input: StreamType, holes: Mapping[str, StreamType]) -> StreamType:
        return self.transform.apply(input, holes).translate_chars(
            self.chars,
            self.replacements,
            self.use_complement_of_chars,
            self.squeeze_repetitions,
        )


# field-select
@dataclass(frozen=True)
class FieldExtraction(StreamTransform):
    transform: StreamTransform
    separator: str
    indices: Sequence[int]
    use_complement_of_indices: bool

    def apply(self, input: StreamType, holes: Mapping[str, StreamType]) -> StreamType:
        return self.transform.apply(input, holes).extract_fields(
            self.separator, self.indices, self.use_complement_of_indices
        )


@dataclass(frozen=True)
class DefaultIfEmpty(StreamTransform):
    transform: StreamTransform
    default: StreamTransform

    def apply(self, input: StreamType, holes: Mapping[str, StreamType]) -> StreamType:
        st = self.transform.apply(input, holes)
        if st.is_empty():
            return self.default.apply(input, holes)
        return st


@dataclass(frozen=True)
class Compose(StreamTransform):
    left: StreamTransform
    right: StreamTransform

    def apply(self, input: StreamType, holes: Mapping[str, StreamType]) -> StreamType:
        return self.right.apply(self.left.apply(input, holes), holes)


@dataclass(frozen=True)
class DeleteChars(StreamTransform):
    transform: StreamTransform
    chars: str
    use_complement_of_chars: bool
    preprocessed: bool = True

    def apply(self, input: StreamType, holes: Mapping[str, StreamType]) -> StreamType:
        c = self.chars
        if self.use_complement_of_chars:
            c = char_set_complement(c, 0, ALPHABET_SIZE)
        return self.transform.apply(input, holes).translate_chars(c, "", False, False)

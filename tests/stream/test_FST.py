"""
Test suite for Finite State Transducer (FST) operations.

This module contains comprehensive tests for various FST operations including
translation, compression, deletion, replacement, and regex-based transformations.
"""

import random
import string
from typing import Set, List
import pytest

from stream.transducer import (
    add_newline_if_not_end_with_newline_FST,
    correct_cut_field_FST,
    cut_char_FST,
    filter_FST,
    first_regex_replacement_FST, 
    first_replacement_FST,
    full_stream_to_line_based_FST, 
    global_replacement_FST,
    head_FST,
    line_based_functional_to_stream_FST,
    start_regex_replacement_FST,
    stream_based_filter_FST,
    tail_FST, 
    translate_to_line_delimited_FST, 
    translation_FST, 
    compression_FST, 
    deletion_FST, 
    cut_field_FST, 
    global_regex_replacement_FST
)
from stream.regex_parser import ast_to_automaton, RegexParser


@pytest.fixture
def random_seed() -> None:
    random.seed(42)


def generate_random_string(length: int = 10, letters: str = string.ascii_lowercase) -> str:
    return ''.join(random.choice(letters) for _ in range(length))


def generate_random_string_unique_chars(length: int = 10) -> str:
    letters = list(string.ascii_lowercase)
    random.shuffle(letters)
    if length > len(letters):
        length = len(letters)
    return ''.join(letters[:length])


class TestTranslationFST:
    
    def test_basic_translation(self) -> None:
        fst = translation_FST("abc", "def")
        
        assert fst.transform_all("abc") == {"def"}
        assert fst.transform_all("ab") == {"de"}
        assert fst.transform_all("a") == {"d"}
        assert fst.transform_all("") == {""}
        assert fst.transform_all("acbbba") == {"dfeeed"}
    
    @pytest.mark.parametrize("test_iteration", range(10))
    def test_random_translation(self, random_seed: None, test_iteration: int) -> None:
        set1 = generate_random_string_unique_chars()
        set2 = generate_random_string_unique_chars()
        fst = translation_FST(set1, set2)
        
        test_string = generate_random_string_unique_chars(random.randint(1, 20))
        expected_output = ""
        
        for char in test_string:
            if char in set1:
                index = set1.index(char)
                if index < len(set2):
                    expected_output += set2[index]
                else:
                    expected_output += char
            else:
                expected_output += char
        
        assert fst.transform_all(test_string) == {expected_output}


class TestCompressionFST:
    
    def test_basic_compression(self) -> None:
        fst = compression_FST("ab")
        
        assert fst.transform_all("aaa") == {"a"}
        assert fst.transform_all("aaabbc") == {"abc"}
        assert fst.transform_all("abcde") == {"abcde"}
        assert fst.transform_all("") == {""}
    
    @pytest.mark.parametrize("test_iteration", range(10))
    def test_random_compression(self, random_seed: None, test_iteration: int) -> None:
        """Test compression with random strings."""
        fst = compression_FST(string.ascii_lowercase)
        original = generate_random_string(random.randint(1, 50))
        
        # Calculate expected compression result
        compressed = ""
        prev_char = None
        for char in original:
            if char != prev_char:
                compressed += char
                prev_char = char
        
        assert fst.transform_all(original) == {compressed}


class TestDeletionFST:
    """Test suite for deletion FST operations."""
    
    def test_basic_deletion(self) -> None:
        """Test basic character deletion functionality."""
        fst = deletion_FST("aeiou")
        
        assert fst.transform_all("hello") == {"hll"}
        assert fst.transform_all("python") == {"pythn"}
        assert fst.transform_all("aeiou") == {""}
        assert fst.transform_all("") == {""}

        # Test whole stream
        fst = deletion_FST("abc\n")
        assert fst.transform_all("\n") == {""}
        assert fst.transform_all("abc\n") == {""}
        assert fst.transform_all("axbycz\nb\nc\ndag\n") == {"xyzdg"}
    
    @pytest.mark.parametrize("test_iteration", range(10))
    def test_random_deletion(self, random_seed: None, test_iteration: int) -> None:
        """Test deletion with random character sets."""
        chars_to_delete = generate_random_string_unique_chars(random.randint(1, 10))
        fst = deletion_FST(chars_to_delete)
        test_string = generate_random_string(random.randint(1, 50))
        
        expected = ''.join([c for c in test_string if c not in chars_to_delete])
        assert fst.transform_all(test_string) == {expected}

class TestCutCharFST:
    """Test suite for character cutting FST operations."""
    
    def test_basic_cut_char(self) -> None:
        """Test basic character cutting functionality."""
        fst = cut_char_FST([3])
        assert fst.transform_all("h e l l o") == {"e"}
        assert fst.transform_all("hi") == {""}


        # Test no upperbound
        fst = cut_char_FST([3], has_upperbound=False)
        assert fst.transform_all("h e l l o") == {"e l l o"}
        assert fst.transform_all("hi") == {""}
        assert fst.transform_all("1 2 3") == {"2 3"}
        assert fst.transform_all("1 2 3 ") == {"2 3 "}

        # Test whole stream
        fst = line_based_functional_to_stream_FST(cut_char_FST([3], has_upperbound=False))
        assert fst.transform_all("\n") == {"\n"}
        assert fst.transform_all("abc\n") == {"c\n"}
        assert fst.transform_all("axbycz\nb\nc\ndag\n") == {"bycz\n\n\ng\n"}


class TestCutFieldFST:
    """Test suite for field cutting FST operations."""
    
    def test_basic_cut_field(self) -> None:
        """Test basic field cutting functionality."""
        # Test single field extraction
        fst = correct_cut_field_FST(" ", [3])
        assert fst.transform_all("h e l l o") == {"l"}
        assert fst.transform_all("hi") == {"hi"}
        assert fst.transform_all("1 2 3") == {"3"}
        
        # Test multiple field extraction
        fst = correct_cut_field_FST(" ", [1, 3])
        assert fst.transform_all("h e l l o") == {"h l"}
        assert fst.transform_all("hi") == {"hi"}
        assert fst.transform_all("1 2 3") == {"1 3"}

        # Test no upperbound
        fst = correct_cut_field_FST(" ", [1, 3], has_upperbound=False)
        assert fst.transform_all("h e l l o") == {"h l l o"}
        assert fst.transform_all("hi") == {"hi"}
        assert fst.transform_all("1 2 3") == {"1 3"}
        assert fst.transform_all("1 2 3 ") == {"1 3 "}

        # Test whole stream
        fst = line_based_functional_to_stream_FST(correct_cut_field_FST(" ", [1, 3], has_upperbound=False))
        assert fst.transform_all("h e l l o") == {"h l l o"}
        assert fst.transform_all("hi") == {"hi"}
        assert fst.transform_all("1 2 3") == {"1 3"}
        assert fst.transform_all("1 2 3 ") == {"1 3 "}
        assert fst.transform_all("1 2 3\n4 5 6") == {"1 3\n4 6"}
        assert fst.transform_all("1 2 3\n4 5 6\n") == {"1 3\n4 6\n"}
        assert fst.transform_all("1 2 3\n1\n1 2 3 ") == {"1 3\n1\n1 3 "}

        fst = line_based_functional_to_stream_FST(correct_cut_field_FST(" ", [3], has_upperbound=True))
        assert fst.transform_all("total 80\ndrwxrwxr-x  2 user user  4096 Jun  10 12:34  bin\n") == {"\n2\n"}
    
    @pytest.mark.parametrize("test_iteration", range(5))
    def test_random_cut_field(self, random_seed: None, test_iteration: int) -> None:
        """Test field cutting with random delimiters and fields."""
        delimiter = random.choice(string.punctuation)
        num_fields = random.randint(1, 3)
        fields_to_extract = sorted(random.sample(range(1, 6), num_fields))
        
        fst = cut_field_FST(delimiter, fields_to_extract)
        
        total_fields = random.randint(max(fields_to_extract) + 1, max(fields_to_extract) + 3)
        test_parts = [generate_random_string(random.randint(1, 8)) for _ in range(total_fields)]
        test_string = delimiter.join(test_parts)
        
        expected_parts = [test_parts[field - 1] for field in fields_to_extract if field <= len(test_parts)]
        expected = delimiter.join(expected_parts)
        
        assert fst.transform_all(test_string) == {expected}


class TestWholeStreamToLineBasedFST:
    """Test suite for whole stream to line-based FST operations."""
    
    def test_basic_whole_stream_to_line_based(self) -> None:
        """Test basic whole stream to line-based functionality."""
        fst = full_stream_to_line_based_FST()
        assert fst.transform_all("\n") == {""}
        assert fst.transform_all("abc\n") == {"abc"}
        assert fst.transform_all("abc\n\n") == {"abc", ""}
        assert fst.transform_all("\nabc\n") == {"abc", ""}
        assert fst.transform_all("abc") == {"abc"}
        assert fst.transform_all("abc\n\n\n") == {"abc", ""}
        assert fst.transform_all("abc\nxyzzzzzzzzzzzz\nz") == {"abc", "xyzzzzzzzzzzzz", "z"}
        assert fst.transform_all("abc\nxyzzzzzzzzzzzz\nz\n") == {"abc", "xyzzzzzzzzzzzz", "z"}
        assert fst.transform_all("abc\nxyzzzzzzzzzzzz\nz\n\n") == {"abc", "xyzzzzzzzzzzzz", "z", ""}
        assert fst.transform_all("abc\nxyzzzzzzzzzzzz\n\nz\n") == {"abc", "xyzzzzzzzzzzzz", "z", ""}
        
        
class TestReplacementFST:
    """Test suite for replacement FST operations."""
    
    def test_global_replacement_basic(self) -> None:
        """Test basic global replacement functionality."""
        fst = global_replacement_FST("a", "b")
        
        assert fst.transform_all("aaa") == {"bbb"}
        assert fst.transform_all("abc") == {"bbc"}
        assert fst.transform_all("def") == {"def"}
        assert fst.transform_all("") == {""}
    
    def test_global_replacement_complex(self) -> None:
        """Test complex global replacement patterns."""
        fst = global_replacement_FST("abaa", "x")
        
        assert fst.transform_all("abaa") == {"x"}
        assert fst.transform_all("aabaa") == {"ax"}
        assert fst.transform_all("abaabaa") == {"xbaa"}
        assert fst.transform_all("abaaabaa") == {"xx"}
        assert fst.transform_all("ab") == {"ab"}
        assert fst.transform_all("ababaa") == {"abx"}
        assert fst.transform_all("abaaababaa") == {"xabx"}
        assert fst.transform_all("abacabaacabaa") == {"abacxcx"}
        assert fst.transform_all('abaaabaaabaa') == {"xxx"}
    
    @pytest.mark.parametrize("test_iteration", range(5))
    def test_random_global_replacement(self, random_seed: None, test_iteration: int) -> None:
        """Test global replacement with random patterns."""
        alphabet = "abc"
        s1 = generate_random_string(random.randint(3, 8), alphabet)
        s2 = generate_random_string(random.randint(50, 200), alphabet)
        
        # Insert pattern randomly into string
        s2_list = list(s2)
        for _ in range(random.randint(0, 5)):
            index = random.randint(0, len(s2_list))
            s2_list[index:index] = list(s1)
        s2 = ''.join(s2_list)
        
        fst = global_replacement_FST(s1, "x")
        expected = s2.replace(s1, "x")
        assert fst.transform_all(s2) == {expected}
    
    def test_first_replacement_basic(self) -> None:
        """Test basic first replacement functionality."""
        fst = first_replacement_FST("a", "b")
        
        assert fst.transform_all("aaa") == {"baa"}
        assert fst.transform_all("abc") == {"bbc"}
        assert fst.transform_all("def") == {"def"}
        assert fst.transform_all("") == {""}
    
    def test_first_replacement_complex(self) -> None:
        """Test complex first replacement patterns."""
        fst = first_replacement_FST("abaa", "x")
        
        assert fst.transform_all("abaa") == {"x"}
        assert fst.transform_all("aabaa") == {"ax"}
        assert fst.transform_all("abaabaa") == {"xbaa"}
        assert fst.transform_all("abaaabaa") == {"xabaa"}
        assert fst.transform_all("ab") == {"ab"}
        assert fst.transform_all("ababaa") == {"abx"}
        assert fst.transform_all("abaaababaa") == {"xababaa"}
        assert fst.transform_all("abacabaacabaa") == {"abacxcabaa"}
    
    @pytest.mark.parametrize("test_iteration", range(5))
    def test_random_first_replacement(self, random_seed: None, test_iteration: int) -> None:
        """Test first replacement with random patterns."""
        alphabet = "abc"
        s1 = generate_random_string(random.randint(3, 8), alphabet)
        s2 = generate_random_string(random.randint(50, 200), alphabet)
        
        # Insert pattern randomly into string
        s2_list = list(s2)
        for _ in range(random.randint(0, 5)):
            index = random.randint(0, len(s2_list))
            s2_list[index:index] = list(s1)
        s2 = ''.join(s2_list)
        
        fst = first_replacement_FST(s1, "x")
        expected = s2.replace(s1, "x", 1)
        assert fst.transform_all(s2) == {expected}


class TestRegexReplacementFST:
    """Test suite for regex-based replacement FST operations."""
    
    def test_global_regex_replacement_basic(self) -> None:
        """Test basic global regex replacement functionality."""
        pattern = "a*"
        automata = ast_to_automaton(RegexParser(pattern).parse())
        fst = global_regex_replacement_FST(automata, "b")
        
        assert fst.transform_all("aaa") == {"b"}
        assert fst.transform_all("a") == {"b"}
        assert fst.transform_all("ac") == {"bcb"}
        assert fst.transform_all("abc") == {"bbbcb"}
        assert fst.transform_all("def") == {"dbebfb"}  # Note: Known behavior
    
    def test_global_regex_replacement_complex(self) -> None:
        """Test complex global regex replacement patterns."""
        # Test a.*b pattern
        pattern = r"a.*b"
        automata = ast_to_automaton(RegexParser(pattern).parse())
        fst = global_regex_replacement_FST(automata, "x")
        
        assert fst.transform_all("aaa") == {"aaa"}
        assert fst.transform_all("acb") == {"x"}
        assert fst.transform_all("aaabbb") == {"x"}
        assert fst.transform_all("aaabbbab") == {"xx", "x"}  # ambiguous
        assert fst.transform_all("bbbaaacbbbaaa") == {"bbbxaaa"}
        
        # Test digit pattern
        pattern = "abc[0-9]+"
        automata = ast_to_automaton(RegexParser(pattern).parse())
        fst = global_regex_replacement_FST(automata, "x")
        
        assert fst.transform_all("aaa") == {"aaa"}
        assert fst.transform_all("abc2131231231") == {"x"}
        assert fst.transform_all("abc2a") == {"xa"}
    
    def test_global_regex_replacement_named_pattern(self) -> None:
        """Test named pattern replacement."""
        pattern = "fred[0-9]+"
        automata = ast_to_automaton(RegexParser(pattern).parse())
        fst = global_regex_replacement_FST(automata, "george")
        
        assert fst.transform_all("fred123") == {"george"}
        assert fst.transform_all("fred") == {"fred"}
        assert fst.transform_all("fred123fred123") == {"georgegeorge"}
        assert fst.transform_all("fred123afred123") == {"georgeageorge"}
        assert fst.transform_all("fred123ffred123") == {"georgefgeorge"}
        assert fst.transform_all("fred123fredfred123") == {"georgefredgeorge"}
        assert fst.transform_all("fredfred123fredfred123fred") == {"fredgeorgefredgeorgefred"}
        assert fst.transform_all("fred1f") == {"georgef"}
    
    def test_global_regex_replacement_ambiguous(self) -> None:
        """Test ambiguous pattern replacement."""
        pattern = "a.a"
        automata = ast_to_automaton(RegexParser(pattern).parse())
        fst = global_regex_replacement_FST(automata, "x")
        
        assert "x" in fst.transform_all("aaa")
        assert "ax" in fst.transform_all("aaba")
        assert "xxx" in fst.transform_all("aaaaaaaaa")
        assert "axa" in fst.transform_all("aabaa")
    
    def test_first_regex_replacement(self) -> None:
        """Test first regex replacement functionality."""
        pattern = r"a.*b"
        automata = ast_to_automaton(RegexParser(pattern).parse())
        fst = first_regex_replacement_FST(automata, "x")
        
        assert fst.transform_all("aaa") == {"aaa"}
        assert fst.transform_all("acb") == {"x"}
        assert fst.transform_all("aaabbb") == {"x"}
        assert fst.transform_all("bbbaaacbbbaaa") == {"bbbxaaa"}
        assert fst.transform_all("aaabbbab") == {"x"}
        
        # Test with group pattern
        pattern = "a(aa)+"
        automata = ast_to_automaton(RegexParser(pattern).parse())
        fst = first_regex_replacement_FST(automata, "x")
        
        assert fst.transform_all("aaa") == {"x"}
        assert fst.transform_all("aa") == {"aa"}
        assert fst.transform_all("aaaaa") == {"x"}
        assert fst.transform_all("aaaa") == {"xa"}
        assert fst.transform_all("aaaaaaaa") == {"xa"}
    
    def test_start_regex_replacement(self) -> None:
        """Test start-anchored regex replacement functionality."""
        pattern = r"a.*b"
        automata = ast_to_automaton(RegexParser(pattern).parse())
        fst = start_regex_replacement_FST(automata, "x")
        
        assert fst.transform_all("aaa") == {"aaa"}
        assert fst.transform_all("acb") == {"x"}
        assert fst.transform_all("aaabbb") == {"x"}
        assert fst.transform_all("bbbaaacbbbaaa") == {"bbbaaacbbbaaa"}
        
        # Test with specific patterns
        pattern = "abc[0-9]+"
        automata = ast_to_automaton(RegexParser(pattern).parse())
        fst = start_regex_replacement_FST(automata, "x")
        
        assert fst.transform_all("aaa") == {"aaa"}
        assert fst.transform_all("abc2131231231") == {"x"}
        assert fst.transform_all("abc2a") == {"xa"}
        assert fst.transform_all("aabc2a") == {"aabc2a"}
        
        # Test with dot pattern
        pattern = "..."
        automata = ast_to_automaton(RegexParser(pattern).parse())
        fst = start_regex_replacement_FST(automata, "x")
        
        assert fst.transform_all("aaa") == {"x"}
        assert fst.transform_all("aa") == {"aa"}
        assert fst.transform_all("aaaaa") == {"xaa"}
        assert fst.transform_all("123456789") == {"x456789"}


class TestTranslateToLineDelimitedFST:
    """Test suite for line-delimited translation FST operations."""
    
    def test_translate_to_line_delimited(self) -> None:
        """Test translation to line-delimited format."""
        fst = translate_to_line_delimited_FST(" ")
        input_text = "  most imPressive\n     me tO you!\n do letteRs middle\n= interneT's glue!"
        expected = {
            'letteRs', '', 'imPressive\n', 'most', 'glue!', 'you!\n', 
            "interneT's", 'do', 'tO', 'middle\n=', 'me'
        }
        
        assert fst.transform_all(input_text) == expected

class TestFilterFST:
    """Test suite for filter FST operations."""
    
    def test_filter(self) -> None:
        """Test filter functionality."""
        fst = filter_FST(ast_to_automaton(RegexParser(".*a.*").parse()))
        assert fst.transform_all("aaa") == {"aaa"}
        assert fst.transform_all("bbb") == set()
        assert fst.transform_all("bbbbbbba") == {"bbbbbbba"}
        assert fst.transform_all("bbbbbbbbbabbbbbb") == {"bbbbbbbbbabbbbbb"}

        fst = filter_FST(ast_to_automaton(RegexParser(".*[0-9]+|A[a-z].*").parse()))
        assert fst.transform_all("aaa") == set()
        assert fst.transform_all("Aa") == {"Aa"}
        assert fst.transform_all("Aa123") == {"Aa123"}
        assert fst.transform_all("XXX123") == {"XXX123"}
        assert fst.transform_all("XXX123XXX") == set()

    def test_stream_based_filter(self) -> None:
        fst = stream_based_filter_FST(ast_to_automaton(RegexParser(".*a.*").parse()))
        assert fst.transform_all("") == {""}
        assert fst.transform_all("\n") == {""}
        assert fst.transform_all("\n2\n\n") == {""}
        assert fst.transform_all("aaa") == {"aaa"}
        assert fst.transform_all("bbb") == {""}
        assert fst.transform_all("bbbbbbba") == {"bbbbbbba"}
        assert fst.transform_all("bbbbbbbbbabbbbbb") == {"bbbbbbbbbabbbbbb"}
        assert fst.transform_all("aaa\nbba\ncc\ndag\n") == {"aaa\nbba\ndag\n"}

        fst = stream_based_filter_FST(ast_to_automaton(RegexParser(".*[0-9]+|A[a-z].*").parse()))
        assert fst.transform_all("aaa\nAa\nAa123\nXXX123\nXXX123XXX\n") == {"Aa\nAa123\nXXX123\n"}

class TestTailFST:
    def test_tail_fst(self) -> None:
        fst = tail_FST("\n", 1)
        assert fst.transform_all("\n") == {"\n"}
        assert fst.transform_all("a\n") == {"a\n"}
        assert fst.transform_all("aaaaa\n") == {"aaaaa\n"}
        assert fst.transform_all("\n\n") == {"\n"}
        assert fst.transform_all("\na\n") == {"a\n"}
        assert fst.transform_all("a\n\n") == {"\n"}

        fst = tail_FST("\n", 2)
        assert fst.transform_all("\n") == {"\n"}
        assert fst.transform_all("a\n") == {"a\n"}
        assert fst.transform_all("aaaaa\n") == {"aaaaa\n"}
        assert fst.transform_all("\n\n") == {"\n\n"}
        assert fst.transform_all("\na\n") == {"\na\n"}
        assert fst.transform_all("a\n\n") == {"a\n\n"}
        assert fst.transform_all("\n\n\n") == {"\n\n"}
        assert fst.transform_all("a\n\n\n") == {"\n\n"}
        assert fst.transform_all("\n\n\n\n") == {"\n\n"}
        assert fst.transform_all("\na\n\n") == {"a\n\n"}


class TestHeadFST:
    def test_head_fst(self) -> None:
        fst = head_FST("\n", 1)
        assert fst.transform_all("\n") == {"\n"}
        assert fst.transform_all("a\n") == {"a\n"}
        assert fst.transform_all("aaaaa\n") == {"aaaaa\n"}
        assert fst.transform_all("\n\n") == {"\n"}
        assert fst.transform_all("a\n\n") == {"a\n"}
        assert fst.transform_all("a\n\n\n") == {"a\n"}
        
        fst = head_FST("\n", 2)
        assert fst.transform_all("\n") == {"\n"}
        assert fst.transform_all("a\n") == {"a\n"}
        assert fst.transform_all("aaaaa\n") == {"aaaaa\n"}
        assert fst.transform_all("\n\n") == {"\n\n"}
        assert fst.transform_all("a\n\n") == {"a\n\n"}
        assert fst.transform_all("a\n\n\n") == {"a\n\n"}

class TestAddNewlineIfNotEndWithNewlineFST:
    def test_add_newline_if_not_end_with_newline_fst(self) -> None:
        fst = add_newline_if_not_end_with_newline_FST()
        assert fst.transform_all("\n") == {"\n"}
        assert fst.transform_all("a\n") == {"a\n"}
        assert fst.transform_all("a\n\n") == {"a\n\n"}
        assert fst.transform_all("a") == {"a\n"}
        assert fst.transform_all("a\nb") == {"a\nb\n"}

# Test runner for pytest compatibility
if __name__ == "__main__":
    pytest.main([__file__])

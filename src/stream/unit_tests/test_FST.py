import random
import string
from stream.transducer import first_regex_replacement_FST, first_replacement_FST, global_replacement_FST, start_regex_replacement_FST, translate_to_line_delimited_FST, translation_FST, compression_FST, deletion_FST, cut_field_FST, global_regex_replacement_FST
from stream.regex_parser import ast_to_automaton, RegexParser


def random_string(length=10, letters=string.ascii_lowercase):
    return ''.join(random.choice(letters) for i in range(length))

def random_string_uniq_chars(length=10):
    letters = list(string.ascii_lowercase)
    random.shuffle(letters)
    if length > len(letters):
        length = len(letters)
    return ''.join(letters[:length])


def test_translation_FST():
    fst = translation_FST("abc", "def")
    assert fst.transform_all("abc") == {"def"}
    assert fst.transform_all("ab") == {"de"}
    assert fst.transform_all("a") == {"d"}
    assert fst.transform_all("") == {""}
    assert fst.transform_all("acbbba") == {"dfeeed"}

def test_random_translation_FST():
    set1 = random_string_uniq_chars()
    set2 = random_string_uniq_chars()
    fst = translation_FST(set1, set2)
    for i in range(100):
        random_string = random_string_uniq_chars(random.randint(1, 100))
        expected_output = ""
        for char in random_string:
            if char in set1:
                index = set1.index(char)
                if index < len(set2):
                    expected_output += set2[index]
                else:
                    expected_output += char
            else:
                expected_output += char
            
        assert fst.transform_all(random_string) == {expected_output}

def test_compression_FST():
    fst = compression_FST("ab")
    assert fst.transform_all("aaa") == {"a"}
    assert fst.transform_all("aaabbc") == {"abc"}
    assert fst.transform_all("abcde") == {"abcde"}
    assert fst.transform_all("") == {""}

def test_random_compression_FST():
    fst = compression_FST(string.ascii_lowercase)
    for i in range(100):
        original = random_string(random.randint(1, 100))
        compressed = ""
        prev_char = None
        for char in original:
            if char != prev_char:
                compressed += char
                prev_char = char
        assert fst.transform_all(original) == {compressed}

def test_deletion_FST():
    fst = deletion_FST("aeiou")
    assert fst.transform_all("hello") == {"hll"}
    assert fst.transform_all("python") == {"pythn"}
    assert fst.transform_all("aeiou") == {""}
    assert fst.transform_all("") == {""}

def test_random_deletion_FST():
    for i in range(100):
        chars_to_delete = random_string_uniq_chars(random.randint(1, 10))
        fst = deletion_FST(chars_to_delete)
        test_string = random_string(random.randint(1, 100))
        expected = ''.join([c for c in test_string if c not in chars_to_delete])
        assert fst.transform_all(test_string) == {expected}

def test_cut_FST():
    fst = cut_field_FST(" ", [3])
    assert fst.transform_all("h e l l o") == {"l"}
    assert fst.transform_all("hi") == {""}
    assert fst.transform_all("1 2 3") == {"3"}
    fst = cut_field_FST(" ", [1, 3])
    assert fst.transform_all("h e l l o") == {"h l"}
    assert fst.transform_all("hi") == {"hi"}
    assert fst.transform_all("1 2 3") == {"1 3"}


def test_random_cut_FST():
    for i in range(100):
        delimiter = random.choice(string.punctuation)
        
        num_fields = random.randint(1, 5)
        fields_to_extract = sorted(random.sample(range(1, 10), num_fields))
        print(f"delimiter: {delimiter}, fields_to_extract: {fields_to_extract}")
        fst = cut_field_FST(delimiter, fields_to_extract)
        
        total_fields = random.randint(max(fields_to_extract) + 1, max(fields_to_extract) + 5)
        test_parts = [random_string(random.randint(1, 10)) for _ in range(total_fields)]
        test_string = delimiter.join(test_parts)
        print(f"test_string: {test_string}")
        expected_parts = [test_parts[field - 1] for field in fields_to_extract if field <= len(test_parts)]
        expected = delimiter.join(expected_parts)
        
        assert fst.transform_all(test_string) == {expected}

def test_global_replacement_FST():
    fst = global_replacement_FST("a", "b")
    assert fst.transform_all("aaa") == {"bbb"}
    assert fst.transform_all("abc") == {"bbc"}
    assert fst.transform_all("def") == {"def"}
    assert fst.transform_all("") == {""}

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

    fst = global_replacement_FST("bcbcbacb", "x")
    assert fst.transform_all("bbb") == {"bbb"}
    assert fst.transform_all("bbbcbcbcbacb") == {"bbbcx"}
    assert fst.transform_all("ccacaaaabbbcbcbcbacb") == {"ccacaaaabbbcx"}


def test_random_global_replacement_FST():
    alphabet = "abc"
    for i in range(500):
        s1 = random_string(random.randint(6, 40), alphabet)
        s2 = random_string(random.randint(200, 1000), alphabet)
        # insert some s1 in s2 randomly
        s2 = list(s2)
        for j in range(random.randint(0, 20)):
            index = random.randint(0, len(s2))
            s2[index:index] = list(s1)
        s2 = ''.join(s2)
        print(f"s1: {s1}")
        print(f"s2: {s2}")
        fst = global_replacement_FST(s1, "x")
        expected = s2.replace(s1, "x")
        assert fst.transform_all(s2) == {expected}


def test_first_replacement_FST():
    fst = first_replacement_FST("a", "b")
    assert fst.transform_all("aaa") == {"baa"}
    assert fst.transform_all("abc") == {"bbc"}
    assert fst.transform_all("def") == {"def"}
    assert fst.transform_all("") == {""}

    fst = first_replacement_FST("abaa", "x")
    assert fst.transform_all("abaa") == {"x"}
    assert fst.transform_all("aabaa") == {"ax"}
    assert fst.transform_all("abaabaa") == {"xbaa"}
    assert fst.transform_all("abaaabaa") == {"xabaa"}
    assert fst.transform_all("ab") == {"ab"}
    assert fst.transform_all("ababaa") == {"abx"}
    assert fst.transform_all("abaaababaa") == {"xababaa"}
    assert fst.transform_all("abacabaacabaa") == {"abacxcabaa"}

    fst = first_replacement_FST("bcbcbacb", "x")
    assert fst.transform_all("bbb") == {"bbb"}
    assert fst.transform_all("bbbcbcbcbacb") == {"bbbcx"}
    assert fst.transform_all("ccacaaaabbbcbcbcbacb") == {"ccacaaaabbbcx"}


def test_random_first_replacement_FST():
    alphabet = "abc"
    for i in range(500):
        s1 = random_string(random.randint(6, 40), alphabet)
        s2 = random_string(random.randint(200, 1000), alphabet)
        # insert some s1 in s2 randomly
        s2 = list(s2)
        for j in range(random.randint(0, 20)):
            index = random.randint(0, len(s2))
            s2[index:index] = list(s1)
        s2 = ''.join(s2)
        print(f"s1: {s1}")
        print(f"s2: {s2}")
        fst = first_replacement_FST(s1, "x")
        expected = s2.replace(s1, "x", 1)
        assert fst.transform_all(s2) == {expected}


def test_global_regex_replacement_FST():
    pattern = "a*"
    automata = ast_to_automaton(RegexParser(pattern).parse())
    fst = global_regex_replacement_FST(automata, "b")
    assert fst.transform_all("aaa") == {"b"}
    assert fst.transform_all("a") == {"b"}
    assert fst.transform_all("ac") == {"bcb"}
    assert fst.transform_all("abc") == {"bbbcb"}
    assert fst.transform_all("def") == {"dbebfb"} # FIXME: should be bdbebfb

    pattern = r"a.*b"
    automata = ast_to_automaton(RegexParser(pattern).parse())
    fst = global_regex_replacement_FST(automata, "x")
    assert fst.transform_all("aaa") == {"aaa"}
    assert fst.transform_all("acb") == {"x"}
    assert fst.transform_all("aaabbb") == {"x"}
    assert fst.transform_all("aaabbbab") == {"xx", "x"} # ambiguous
    assert fst.transform_all("bbbaaacbbbaaa") == {"bbbxaaa"}

    pattern = "abc[0-9]+"
    automata = ast_to_automaton(RegexParser(pattern).parse())
    fst = global_regex_replacement_FST(automata, "x")
    assert fst.transform_all("aaa") == {"aaa"}
    assert fst.transform_all("abc2131231231") == {"x"}
    assert fst.transform_all("abc2a") == {"xa"}

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

    pattern = "a.a"
    automata = ast_to_automaton(RegexParser(pattern).parse())
    fst = global_regex_replacement_FST(automata, "x")
    print(fst)
    assert "x" in fst.transform_all("aaa")
    assert "ax" in fst.transform_all("aaba")
    assert "xxx" in fst.transform_all("aaaaaaaaa")
    assert "axa" in fst.transform_all("aabaa")


def test_first_regex_replacement_FST():
    pattern = r"a.*b"
    automata = ast_to_automaton(RegexParser(pattern).parse())
    fst = first_regex_replacement_FST(automata, "x")
    print(fst)
    assert fst.transform_all("aaa") == {"aaa"}
    assert fst.transform_all("acb") == {"x"}
    assert fst.transform_all("aaabbb") == {"x"}
    assert fst.transform_all("bbbaaacbbbaaa") == {"bbbxaaa"}
    assert fst.transform_all("aaabbbab") == {"x"}

    pattern = "abc[0-9]+"
    automata = ast_to_automaton(RegexParser(pattern).parse())
    fst = first_regex_replacement_FST(automata, "x")
    assert fst.transform_all("aaa") == {"aaa"}
    assert fst.transform_all("abc2131231231") == {"x"}
    assert fst.transform_all("abc2a") == {"xa"}

    pattern = "fred[0-9]+"
    automata = ast_to_automaton(RegexParser(pattern).parse())
    fst = first_regex_replacement_FST(automata, "george")
    assert fst.transform_all("fred123") == {"george"}
    assert fst.transform_all("fred") == {"fred"}
    assert fst.transform_all("fred123fred123") == {"georgefred123"}
    assert fst.transform_all("fred123afred123") == {"georgeafred123"}
    assert fst.transform_all("fred123ffred123") == {"georgeffred123"}
    assert fst.transform_all("fred123fredfred123") == {"georgefredfred123"}
    assert fst.transform_all("fredfred123fredfred123fred") == {"fredgeorgefredfred123fred"}
    assert fst.transform_all("fred1f") == {"georgef"}

    pattern = "a(aa)+"
    automata = ast_to_automaton(RegexParser(pattern).parse())
    fst = first_regex_replacement_FST(automata, "x")
    assert fst.transform_all("aaa") == {"x"}
    assert fst.transform_all("aa") == {"aa"}
    assert fst.transform_all("aaaaa") == {"x"}
    assert fst.transform_all("aaaa") == {"xa"}
    assert fst.transform_all("aaaaaaaa") == {"xa"}



def test_start_regex_replacement_FST():
    pattern = r"a.*b"
    automata = ast_to_automaton(RegexParser(pattern).parse())
    fst = start_regex_replacement_FST(automata, "x")
    assert fst.transform_all("aaa") == {"aaa"}
    assert fst.transform_all("acb") == {"x"}
    assert fst.transform_all("aaabbb") == {"x"}
    assert fst.transform_all("bbbaaacbbbaaa") == {"bbbaaacbbbaaa"}

    pattern = "abc[0-9]+"
    automata = ast_to_automaton(RegexParser(pattern).parse())
    fst = start_regex_replacement_FST(automata, "x")
    assert fst.transform_all("aaa") == {"aaa"}
    assert fst.transform_all("abc2131231231") == {"x"}
    assert fst.transform_all("abc2a") == {"xa"}
    assert fst.transform_all("aabc2a") == {"aabc2a"}

    pattern = "fred[0-9]+"
    automata = ast_to_automaton(RegexParser(pattern).parse())
    fst = start_regex_replacement_FST(automata, "george")
    assert fst.transform_all("fred123") == {"george"}
    assert fst.transform_all("fred") == {"fred"}
    assert fst.transform_all("fred123fred123") == {"georgefred123"}
    assert fst.transform_all("fred123afred123") == {"georgeafred123"}
    assert fst.transform_all("fred123ffred123") == {"georgeffred123"}
    assert fst.transform_all("fred123fredfred123") == {"georgefredfred123"}
    assert fst.transform_all("fredfred123fredfred123fred") == {"fredfred123fredfred123fred"}
    assert fst.transform_all("fred1f") == {"georgef"}

    pattern = "a(aa)+"
    automata = ast_to_automaton(RegexParser(pattern).parse())
    fst = start_regex_replacement_FST(automata, "x")
    assert fst.transform_all("aaa") == {"x"}
    assert fst.transform_all("aa") == {"aa"}
    assert fst.transform_all("aaaaa") == {"x"}
    assert fst.transform_all("aaaa") == {"xa"}
    assert fst.transform_all("aaaaaaaa") == {"xa"}

    pattern = "..."
    automata = ast_to_automaton(RegexParser(pattern).parse())
    fst = start_regex_replacement_FST(automata, "x")
    assert fst.transform_all("aaa") == {"x"}
    assert fst.transform_all("aa") == {"aa"}
    assert fst.transform_all("aaaaa") == {"xaa"}
    assert fst.transform_all("123456789") == {"x456789"}

def test_translate_to_line_delimited_FST():
    set1 = " "
    fst = translate_to_line_delimited_FST(set1)
    assert fst.transform_all("  most imPressive\n     me tO you!\n do letteRs middle\n= interneT's glue!") == {'letteRs', '', 'imPressive\n', 'most', 'glue!', 'you!\n', "interneT's", 'do', 'tO', 'middle\n=', 'me'}

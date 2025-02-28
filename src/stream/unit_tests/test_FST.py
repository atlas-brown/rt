import random
import string
from stream.transducer import translation_FST, compression_FST, deletion_FST, cut_FST


def random_string(length=10):
    letters = string.ascii_lowercase
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

def test_cut_FST_1():
    fst = cut_FST(" ", [3])
    assert fst.transform_all("h e l l o") == {"l"}
    assert fst.transform_all("hi") == {""}
    assert fst.transform_all("1 2 3") == {"3"}

def test_cut_FST_2():
    fst = cut_FST(" ", [1, 3])
    assert fst.transform_all("h e l l o") == {"h l"}
    assert fst.transform_all("hi") == {"hi"}
    assert fst.transform_all("1 2 3") == {"1 3"}

def test_random_cut_FST():
    for i in range(100):
        delimiter = random.choice(string.punctuation)
        
        num_fields = random.randint(1, 5)
        fields_to_extract = sorted(random.sample(range(1, 10), num_fields))
        print(f"delimiter: {delimiter}, fields_to_extract: {fields_to_extract}")
        fst = cut_FST(delimiter, fields_to_extract)
        
        total_fields = random.randint(max(fields_to_extract) + 1, max(fields_to_extract) + 5)
        test_parts = [random_string(random.randint(1, 10)) for _ in range(total_fields)]
        test_string = delimiter.join(test_parts)
        print(f"test_string: {test_string}")
        expected_parts = [test_parts[field - 1] for field in fields_to_extract if field <= len(test_parts)]
        expected = delimiter.join(expected_parts)
        
        assert fst.transform_all(test_string) == {expected}

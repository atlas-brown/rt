from stream.regular_type import RegularType


def get_result(expected_input: str, actual_input: str) -> bool:
    expected_type = RegularType(expected_input)
    actual_type = RegularType(actual_input)
    return actual_type.is_subtype(expected_type)

def test_subtyping():
    assert get_result("[0-9]+", "[0-9]+") == True
    assert get_result("[0-9]+", "[0-9]") == True
    assert get_result("[0-9]", "[0-9]+") == False
    assert get_result("[0-9]*", "[0-9]+") == True
    assert get_result(".*", "[0-9]") == True
    assert get_result(".*", "[0-9]+") == True
    assert get_result(".+", "[0-9]+") == True
    assert get_result(".+", "[0-9]*") == False
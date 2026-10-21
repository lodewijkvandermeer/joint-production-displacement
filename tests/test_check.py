from jpdm import check


def test_identical_documents_do_not_differ():
    d = {"a": [1.0, {"b": 2}], "c": "x"}
    assert check.diff_json(d, {"a": [1.0, {"b": 2}], "c": "x"}) == []


def test_float_noise_is_tolerated_but_a_real_change_is_not():
    assert check.diff_json({"x": 0.1234567890}, {"x": 0.1234567891}) == []
    assert check.diff_json({"x": 0.1234}, {"x": 0.1235}) == [("/x", 0.1234, 0.1235)]


def test_structure_changes_are_reported():
    assert check.diff_json({"a": 1}, {"b": 1})
    assert check.diff_json([1, 2], [1])
    assert check.diff_json({"a": "x"}, {"a": "y"})
    assert check.diff_json({"a": True}, {"a": 1.0})

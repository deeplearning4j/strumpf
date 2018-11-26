import pytest
import strumpf as st

_STRUMPF = None

LARGE_A = 'large_a.txt'
LARGE_B = 'large_b.txt'
SMALL = 'small.txt'


def _get_strumpf_instance():
    # Note: running tests requires a valid local config stored
    # at ~/.deeplearning4j/strumpf/config.json with valid azure credentials
    if _STRUMPF is None:
        _STRUMPF = st.Strumpf()
    return _STRUMPF


def _create_large_test_file(file_name, size_mb)
    with open(file_name, "wb") as test_file:
        test_file.truncate(size_mb * 1024 * 1024)


def test_workflow():
    strumpf = 


if __name__ == '__main__':
    pytest.main([__file__])
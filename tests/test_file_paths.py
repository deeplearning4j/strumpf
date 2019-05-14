import pytest
from strumpf.cli import CLI
from strumpf.core import join

cli = CLI()
strumpf = cli.strumpf


def test_join():

    base = 'C:\\foo\\bar'
    ext = 'baz'
    assert join(base, ext) == 'C:/foo/bar/baz'


if __name__ == '__main__':
    pytest.main([__file__])

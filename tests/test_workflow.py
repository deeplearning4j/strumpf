import pytest
import os
import mock
from strumpf.cli import CLI
from strumpf.core import ZIP, REF
from strumpf.client import get_url

_STRUMPF = None

LARGE_A = 'large_a.txt'
LARGE_B = 'large_b.txt'
SMALL = 'small.txt'


def _get_cli_instance():
    global _STRUMPF
    # Note: running tests requires a valid local config stored
    # at ~/.deeplearning4j/strumpf/config.json with valid azure credentials
    if _STRUMPF is None:
        _STRUMPF = CLI()
    return _STRUMPF


def _create_large_test_file(file_name, byte_size):
    with open(file_name, "wb") as test_file:
        test_file.truncate(byte_size)


def test_workflow():
    # create CLI
    cli = _get_cli_instance()

    # each CLI creates a strumpf instance
    strumpf = cli.strumpf

    # query status
    cli.status()

    # create two large and one small resource in resp. local folder
    local_dir = strumpf.get_local_resource_dir()
    limit = strumpf.get_limit_in_bytes()
    large_a = 'large_a.txt'
    large_b = 'large_b.txt'
    small = 'small.txt'
    large_a_path = os.path.join(local_dir, large_a)
    large_b_path = os.path.join(local_dir, large_b)
    small_path = os.path.join(local_dir, small)

    _create_large_test_file(os.path.join(local_dir, large_a_path), 2 * limit)
    _create_large_test_file(os.path.join(local_dir, large_b_path), 2 * limit)
    _create_large_test_file(os.path.join(
        local_dir, small_path), 0)  # empty file

    # Adding the small file has no effect,
    # the large file will be added to "staged" files.

    # The user has to provide the full local file path
    # to avoid misunderstandings.
    cli.add(large_a_path)
    cli.add(small_path)

    cli.status()
    staged_files = strumpf.get_staged_files()
    assert len(staged_files) == 1
    assert large_a_path in staged_files

    # Adding the base path also works and will add all files
    cli.add(local_dir)

    # Now all large files are staged.
    staged_files = strumpf.get_staged_files()
    assert len(staged_files) == 2
    assert large_b_path in staged_files

    # Trigger upload of all files (confirm "yes" for upload)
    with mock.patch('strumpf.core.input', return_value='y'):
        cli.upload()
    # staged files are cleared again
    staged_files = strumpf.get_staged_files()
    assert len(staged_files) == 0

    # Confirm that files are not available locally anymore
    assert not os.path.isfile(large_a_path)
    assert not os.path.isfile(large_b_path)

    # Instead, files have been replaced by references.
    assert os.path.isfile(large_a_path + REF)
    assert os.path.isfile(large_b_path + REF)

    # Connect to azure to check for remote files
    azure = strumpf.service_from_config()
    blobs = azure.get_all_blob_names()

    # Confirm that zipped files and references are available on azure
    # The file comes as version "v1", reference files get updated.
    assert large_a + ZIP + '.v1' in blobs
    assert large_a + REF in blobs

    # Confirm that original (not zipped) files and references
    # have been cached as well
    cache = strumpf.get_cache_dir()
    assert os.path.isfile(os.path.join(cache, large_a))
    assert not os.path.isfile(os.path.join(cache, large_a + ZIP))
    assert os.path.isfile(os.path.join(cache, large_a + REF))

    # Try to download file. Since it's in cache AND hashes equal,
    # no need to download again
    was_downloaded, _ = cli.download(large_a)
    assert not was_downloaded

    # Now, clear cache and attempt download again.
    # This time it will download and unzip the file
    strumpf._clear_cache()
    assert not os.path.isfile(os.path.join(cache, large_a))

    # Version 1 gets downloaded
    # (we validate internally that it's the right hash as well)
    was_downloaded, version = cli.download(large_a)
    assert was_downloaded
    assert version == 1
    assert os.path.isfile(os.path.join(cache, large_a))

    # Finally, create an updated version of "large_a" and upload it again.
    _create_large_test_file(os.path.join(local_dir, large_a_path), 2 * limit)
    cli.add(large_a_path)
    with mock.patch('strumpf.core.input', return_value='y'):
        cli.upload()

    # Now we have two versioned, remote files and one reference
    blobs = azure.get_all_blob_names()
    assert large_a + ZIP + '.v1' in blobs
    assert large_a + ZIP + '.v2' in blobs
    assert large_a + REF in blobs

    # This time version 2 gets downloaded
    strumpf._clear_cache()
    was_downloaded, version = cli.download(large_a)
    assert was_downloaded
    assert version == 2

    # Lastly, if a user wants to use a test resources, we need to provide a
    # test resource URL, given the original file name
    url = get_url(large_a)

    # Test the url by opening the file
    with open(url, 'r') as f:
        f.read

    # Cleaning up
    os.remove(large_a_path + REF)
    os.remove(large_b_path + REF)
    os.remove(small_path)
    strumpf._clear_cache()

if __name__ == '__main__':
    pytest.main([__file__])

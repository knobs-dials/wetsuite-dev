import os
import pytest
from wetsuite.helpers.net import download


def test_download():
    ''' Test some basic assumptions around strip_namespace() and strip_namespace_inplace()  '''

    # checking that these don't raise any errors
    download('http://www.example.com')

    download('https://www.example.com')

    download('https://www.example.com', show_progress=True)

    with pytest.raises(ValueError, match=r'.*404.*'):
        download('https://www.example.com/noexist')


def test_download_to_file( tmp_path ): # note: pytest fixture will create a temporary directory
    tofile_path = tmp_path / "testfile"  # this syntax works because tmp_path is a pathlib.Path object
    download('https://www.example.com', tofile_path=tofile_path)
    assert os.path.exists( tofile_path )

    # check that we don't create a file if we failed to start fetching
    with pytest.raises(ValueError, match=r'.*404.*'):
        download('https://www.example.com/noexist', tofile_path=tofile_path)
        assert not os.path.exists( tofile_path )




import pytest

import wetsuite.datasets


def test_fetch_index():
    index = wetsuite.datasets.fetch_index()


def test_dataset_class_basics( tmp_path ):
    ' test Some Dataset basics '
    ds = wetsuite.datasets.Dataset(
        description = 'descr',
        data  = {'a':b'b', 'c':b'd'}, 
        name  = 'name')
    assert ds.description == 'descr'
    assert ds.data == {'a':b'b', 'c':b'd'}
    assert ds.name == 'name'
    assert ds.num_items == 2

    str(ds)


def test_dataset_class_save( tmp_path ):
    ds = wetsuite.datasets.Dataset(
        description = 'descr',
        data  = {'a':'b', 'c':'d'}, 
        name  = 'name')
    ds.save_files( tmp_path )

    ds = wetsuite.datasets.Dataset(
        description = 'descr',
        data  = {'a':b'b', 'c':b'd'}, 
        name  = 'name')
    ds.save_files( tmp_path )

    ds = wetsuite.datasets.Dataset(
        description = 'descr',
        data  = {'a':{1:2}, 'c':{3:4}}, 
        name  = 'name')
    ds.save_files( tmp_path )


# TODO: more        
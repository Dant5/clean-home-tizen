"""Release archives must not carry private native recovery/signing data."""
import importlib.util
from pathlib import Path
import sys
import zipfile
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('release_companion',ROOT/'scripts/prepare-release.py')
release=importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


def test_generic_companion_with_licence_is_accepted(tmp_path):
    path=tmp_path/'helper.zip'
    with zipfile.ZipFile(path,'w') as archive:
        archive.writestr('LICENSE','MIT')
        archive.writestr('payload/payload.json','{"schema":1}')
    release.validate_companion(path)


@pytest.mark.parametrize('name',['../escape','/absolute','folder\\escape','OriginalHome.json','device.original.json','device.status.json','author.p12','profiles.xml','owner.wgt'])
def test_private_or_unsafe_companion_archive_is_refused(tmp_path,name):
    path=tmp_path/'helper.zip'
    with zipfile.ZipFile(path,'w') as archive:
        archive.writestr('LICENSE','MIT')
        archive.writestr(name,'test fixture')
    with pytest.raises(ValueError): release.validate_companion(path)

import os
import pwd
from unittest.mock import MagicMock, patch

import pytest
from rocker.core import DockerImageGenerator

from ghrocker.ghrocker import generate_dockerfile, main


def _make_passwd(name, uid, gid):
    return pwd.struct_passwd((
        name,
        'x',
        uid,
        gid,
        '',
        f'/home/{name}',
        '/bin/bash',
    ))


def test_generate_dockerfile_excludes_user(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ret = generate_dockerfile([])
    assert ret == 0

    dockerfile_content = (tmp_path / 'Dockerfile.ghrocker').read_text()
    assert 'FROM ruby:3.1-bookworm' in dockerfile_content
    assert 'RUN gem install jekyll' in dockerfile_content
    assert 'Snippet from extension [user]' not in dockerfile_content
    assert 'useradd' not in dockerfile_content


def test_prebuilt_image_with_two_different_user_ids():
    captured_digs = []
    orig_init = DockerImageGenerator.__init__

    def spy_init(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)
        captured_digs.append(self)

    users = [
        _make_passwd('user_one', 1001, 1001),
        _make_passwd('user_two', 2002, 2002),
    ]

    for user_entry in users:
        with patch('pwd.getpwuid', return_value=user_entry), \
             patch.object(DockerImageGenerator, '__init__', spy_init), \
             patch.object(DockerImageGenerator, 'build', return_value=0) as mock_build, \
             patch.object(DockerImageGenerator, 'run', return_value=0) as mock_run:
            ret = main(['test/test_site', '--build-only'])
            assert ret == 0
            assert mock_build.called
            assert mock_run.called

    assert len(captured_digs) == 2

    dig_user_one, dig_user_two = captured_digs

    # Both use the prebuilt image as base and do not reinstall gems
    for dig in (dig_user_one, dig_user_two):
        assert 'FROM ghcr.io/tfoote/ghrocker/ghrocker:latest' in dig.dockerfile
        assert 'RUN gem install jekyll' not in dig.dockerfile
        docker_cmd = dig.generate_docker_cmd(command='jekyll build -V --trace')
        assert '-w /tmp/jekyll' in docker_cmd
        assert ':/tmp/jekyll' in docker_cmd

    # First invocation layers UID 1001 (user_one) onto the prebuilt image
    assert '--uid "1001"' in dig_user_one.dockerfile
    assert '-g "1001"' in dig_user_one.dockerfile
    assert 'USER user_one' in dig_user_one.dockerfile
    assert 'user_two' not in dig_user_one.dockerfile

    # Second invocation layers UID 2002 (user_two) onto the prebuilt image
    assert '--uid "2002"' in dig_user_two.dockerfile
    assert '-g "2002"' in dig_user_two.dockerfile
    assert 'USER user_two' in dig_user_two.dockerfile
    assert 'user_one' not in dig_user_two.dockerfile


def test_develop_mode_includes_ghpages_and_user():
    captured_digs = []
    orig_init = DockerImageGenerator.__init__

    def spy_init(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)
        captured_digs.append(self)

    user_entry = _make_passwd('dev_user', 1000, 1000)
    with patch('pwd.getpwuid', return_value=user_entry), \
         patch.object(DockerImageGenerator, '__init__', spy_init), \
         patch.object(DockerImageGenerator, 'build', return_value=0) as mock_build, \
         patch.object(DockerImageGenerator, 'run', return_value=0) as mock_run:
        ret = main(['test/test_site', '--develop', '--build-only'])
        assert ret == 0
        assert mock_build.called
        assert mock_run.called

    assert len(captured_digs) == 1
    dig = captured_digs[0]
    assert 'FROM ruby:3.1-bookworm' in dig.dockerfile
    assert 'RUN gem install jekyll' in dig.dockerfile
    assert '--uid "1000"' in dig.dockerfile
    assert 'USER dev_user' in dig.dockerfile


@pytest.fixture
def mock_dig():
    with patch('ghrocker.ghrocker.DockerImageGenerator') as mock_class:
        instance = MagicMock()
        instance.build.return_value = 0
        instance.run.return_value = 0
        mock_class.return_value = instance
        yield instance


def test_default_mode(mock_dig):
    ret = main(['test/test_site'])
    assert ret == 0
    assert mock_dig.run.called
    kwargs = mock_dig.run.call_args[1]
    assert kwargs['command'] == 'jekyll serve -w'
    assert kwargs.get('network') == 'host'
    assert kwargs['build_only'] is False
    assert kwargs['serve_only'] is False


def test_default_mode_with_baseurl(mock_dig):
    ret = main(['test/test_site', '--baseurl', '/blog'])
    assert ret == 0
    assert mock_dig.run.called
    kwargs = mock_dig.run.call_args[1]
    assert kwargs['command'] == "jekyll serve -w --baseurl='/blog' -d /tmp/aliased_site"


def test_build_only_mode(mock_dig):
    ret = main(['test/test_site', '--build-only'])
    assert ret == 0
    assert mock_dig.run.called
    kwargs = mock_dig.run.call_args[1]
    assert kwargs['command'] == 'jekyll build -V --trace'
    assert 'network' not in kwargs
    assert kwargs['build_only'] is True
    assert kwargs['serve_only'] is False


def test_build_alias_mode(mock_dig):
    ret = main(['test/test_site', '--build'])
    assert ret == 0
    assert mock_dig.run.called
    kwargs = mock_dig.run.call_args[1]
    assert kwargs['command'] == 'jekyll build -V --trace'
    assert 'network' not in kwargs
    assert kwargs['build_only'] is True


def test_serve_only_mode(mock_dig):
    ret = main(['test/test_site', '--serve-only'])
    assert ret == 0
    assert mock_dig.run.called
    kwargs = mock_dig.run.call_args[1]
    assert kwargs['command'] == 'jekyll serve --skip-initial-build --no-watch'
    assert kwargs.get('network') == 'host'
    assert kwargs['serve_only'] is True
    assert kwargs['build_only'] is False


def test_serve_only_mode_with_baseurl(mock_dig):
    ret = main(['test/test_site', '--serve-only', '--baseurl', '/blog'])
    assert ret == 0
    assert mock_dig.run.called
    kwargs = mock_dig.run.call_args[1]
    assert kwargs['command'] == "jekyll serve --skip-initial-build --no-watch --baseurl='/blog' -d /tmp/aliased_site"


def test_config_option(mock_dig):
    ret = main(['test/test_site', '--serve-only', '--config', '_config.yml,_config_dev.yml'])
    assert ret == 0
    assert mock_dig.run.called
    kwargs = mock_dig.run.call_args[1]
    assert kwargs['command'] == 'jekyll serve --skip-initial-build --no-watch --config=_config.yml,_config_dev.yml'


def test_incompatible_build_and_serve_only(mock_dig):
    with pytest.raises(SystemExit):
        main(['test/test_site', '--build-only', '--serve-only'])


def test_incompatible_build_and_baseurl(mock_dig):
    with pytest.raises(SystemExit):
        main(['test/test_site', '--build-only', '--baseurl', '/blog'])

import pwd
from unittest.mock import patch

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

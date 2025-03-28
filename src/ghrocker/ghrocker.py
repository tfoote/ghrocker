import argparse
import os
import shlex

from rocker.core import DockerImageGenerator
from rocker.core import get_rocker_version
from rocker.core import RockerExtensionManager


def main():

    parser = argparse.ArgumentParser(
        description='A tool for building and testing gh-pages locally',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('directory')
    #parser.add_argument('command', nargs='*', default='')
    parser.add_argument('--nocache', action='store_true',
        help='Force a rebuild of the image')
    parser.add_argument('--develop', action='store_true',
       help='Build the image locally not using the prebuilt image.')
    parser.add_argument('--config', type=str, nargs="+", action='append', default=None)
    parser.add_argument('--baseurl', type=str, action='store', default=None)
    parser.add_argument('--prebuilt-image', type=str, action='store', default='ghcr.io/tfoote/ghrocker/ghrocker:latest')
    parser.add_argument('-v', '--version', action='version',
        version='%(prog)s ' + get_rocker_version())
    parser.add_argument('--build-only', action='store_true')
    parser.add_argument('--debug-inside', action='store_true')
    # TODO(tfoote) add verbose parser.add_argument('--verbose', action='store_true')


    extension_manager = RockerExtensionManager()
    default_args = {'ghpages': True, 'user': True, 'network': 'host'}
    extension_manager.extend_cli_parser(parser, default_args)

    args = parser.parse_args()
    args_dict = vars(args)
    args_dict['directory'] = os.path.abspath(args_dict['directory'])

    if args.build_only and args.baseurl:
        parser.error("build and baseurl options are incompatible")

    if args.build_only:
        args_dict['command'] = 'jekyll build -V --trace'
        del args_dict['network']
    else:
        args_dict['command'] = 'jekyll serve -w'
        if args.baseurl is not None:
            # Don't output to the default location if generating using a modified baseurl
            args_dict['command'] += ' --baseurl=\'{baseurl}\' -d /tmp/aliased_site'.format(**args_dict)

    if args.config:
        config_args = ','.join(args.config[0])
        args_dict['command'] += ' --config={config_args}'.format(**locals())

    active_extensions = extension_manager.get_active_extensions(args_dict)
    print("Active extensions %s" % [e.get_name() for e in active_extensions])

    dig = DockerImageGenerator(active_extensions, args_dict, 'ruby:3.1-bookworm')

    #Initialize exit_code
    exit_code = 0
    if args.develop:
        exit_code = dig.build(**vars(args))
    else:
        print(f"Skipping build for prebuilt image {args.prebuilt_image}")
        dig.image_id = args.prebuilt_image
        dig.built = True
    if exit_code != 0:
        print("Build failed exiting")
        return exit_code

    if args.debug_inside:
        args_dict['command'] = 'bash'

    return dig.run(**args_dict)

def generate_dockerfile():

    parser = argparse.ArgumentParser(
        description='Generate the dockerfile for the prebuilt image',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-v', '--version', action='version',
        version='%(prog)s ' + get_rocker_version())

    extension_manager = RockerExtensionManager()
    default_args = {'ghpages': True, 'user': True, 'network': 'host'}
    extension_manager.extend_cli_parser(parser, default_args)

    args = parser.parse_args()
    args_dict = vars(args)

    active_extensions = extension_manager.get_active_extensions(args_dict)
    print("Active extensions %s" % [e.get_name() for e in active_extensions])

    dig = DockerImageGenerator(active_extensions, args_dict, 'ruby:3.1-bookworm')
    with open('Dockerfile.ghrocker', 'w') as fh:
        fh.write(dig.dockerfile)
    return 0

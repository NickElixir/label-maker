"""Create machine learning training data from satellite imagery and OpenStreetMap"""

import sys
import argparse
import logging
import json
from os import makedirs, path as op

from cerberus import Validator
from shapely.geometry import MultiPolygon, Polygon

from label_maker.version import __version__
from label_maker.download import download_mbtiles
from label_maker.label import make_labels
from label_maker.preview import preview
from label_maker.images import download_images
from label_maker.package import package_directory
from label_maker.validate import schema

logger = logging.getLogger(__name__)

def get_bounds(feature_collection):
    """Get a bounding box for a FeatureCollection of Polygon Features"""
    features = [f for f in feature_collection['features'] if f['geometry']['type'] in ['Polygon']]
    return MultiPolygon(list(map(lambda x: Polygon(x['geometry']['coordinates'][0]), features))).bounds


def parse_args(args):
    """Create an argument parser with subcommands"""
    desc = 'label_maker (v%s)' % __version__
    dhf = argparse.ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(description=desc)

    pparser = argparse.ArgumentParser(add_help=False)
    pparser.add_argument('--version', help='Print version and exit',
                         action='version', version=__version__)
    pparser.add_argument('--log', default=2, type=int,
                         help='0:all, 1:debug, 2:info, 3:warning, 4:error, 5:critical')
    pparser.add_argument('-c', '--config', default='config.json', type=str,
                         help='location of config.json file')
    pparser.add_argument('-d', '--dest', default='data', type=str,
                         help='directory for storing output files')
    pparser.add_argument('-mb', '--mbtiles', default='', type=str,
                         help='directory with QA tiles')
    # add subcommands
    subparsers = parser.add_subparsers(dest='command')

    subparsers.add_parser('download', parents=[pparser], help='', formatter_class=dhf)
    l = subparsers.add_parser('labels', parents=[pparser], help='', formatter_class=dhf)
    p = subparsers.add_parser('preview', parents=[pparser], help='', formatter_class=dhf)
    subparsers.add_parser('images', parents=[pparser], help='', formatter_class=dhf)
    subparsers.add_parser('package', parents=[pparser], help='', formatter_class=dhf)

    # labels has an optional parameter
    l.add_argument('-s', '--sparse', action='store_true')

    # preview has an optional parameter
    p.add_argument('-n', '--number', default=5, type=int,
                   help='number of examples images to create per class')

    # turn namespace into dictinary
    parsed_args = vars(parser.parse_args(args))

    return parsed_args


def cli():
    """Validate input data and call the appropriate subcommand with necessary arguments"""
    args = parse_args(sys.argv[1:])
    logger.setLevel(args.pop('log') * 10)
    cmd = args.pop('command')

    # read in configuration file and destination folder
    config = json.load(open(args.get('config')))
    dest_folder = args.get('dest')
    mbtiles_folder = args.get('mbtiles')

    # create destination folder if necessary
    if not op.isdir(dest_folder):
        makedirs(dest_folder)
    # validate configuration file
    v = Validator(schema)
    valid = v.validate(config)
    if not valid:
        raise Exception(v.errors)

    # custom validation for top level keys
    # require either: country & bounding_box or geojson
    if 'geojson' not in config.keys() and not ('country' in config.keys() and 'bounding_box' in config.keys()):
        raise Exception('either "geojson" or "country" and "bounding_box" must be present in the configuration JSON')

    # for geojson, overwrite other config keys to correct labeling
    if 'geojson' in config.keys():
        config['country'] = op.splitext(op.basename(config.get('geojson')))[0]
        config['bounding_box'] = get_bounds(json.load(open(config.get('geojson'), 'r')))

    if cmd == 'download':
        download_mbtiles(dest_folder=dest_folder, **config)
    elif cmd == 'labels':
        sparse = args.get('sparse', False)
        make_labels(dest_folder=dest_folder, mbtiles_folder=mbtiles_folder, sparse=sparse, **config)
    elif cmd == 'preview':
        number = args.get('number')
        preview(dest_folder=dest_folder, number=number, **config)
    elif cmd == 'images':
        download_images(dest_folder=dest_folder, **config)
    elif cmd == 'package':
        package_directory(dest_folder=dest_folder, **config)

if __name__ == "__main__":
    cli()

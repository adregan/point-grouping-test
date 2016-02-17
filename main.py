import argparse
import json
import numpy as np
from scipy.cluster.vq import vq, kmeans, whiten

def JSONFile(file_path):
    ''' JSONFile : Str -> List
        Implements a custom argument type that takes a filepath,
        reads the file's data and returns it as loaded JSON.
    '''
    try:
        with open(file_path, 'r') as file:
            points = json.loads(file.read())
    except FileNotFoundError as err:
        raise argparse.ArgumentTypeError(
            'The file {0} couldn\'t be found'.format(file_path))
    except json.decoder.JSONDecodeError as err:
        raise argparse.ArgumentTypeError(
            'Couldn\'t parse JSON: {0}'.format(err))
    else:
        return points

def get_args():
    ''' get_args: None -> argparse.Namespace
        Builds the command line argument parser and parses the args.
    '''
    parser = argparse.ArgumentParser(
        description='Groups the location of jobs \
        based on the number of vans available.')

    # Using custom type to handle the JSON loading
    parser.add_argument(
        '-i',
        '--infile',
        type=JSONFile,
        dest='infile',
        required=True,
        help='The path to the input file.')

    parser.add_argument(
        '-n',
        '--number',
        type=int,
        dest='number_of_vans',
        required=True,
        help='The number of vans running today.')

    parser.add_argument(
        '-o',
        '--outfile',
        type=str,
        dest='outfile',
        default='groups.json',
        help='The name of the outfile. Defaults to `groups.json`.')

    return parser.parse_args()

def create_output(file_path, vans_data):
    with open(file_path, 'w') as file:
        file.write(json.dumps(vans_data, indent=2))

def main():
    args = get_args()
    data = args.infile
    points = np.array([
        [point.get('lon'), point.get('lat')]
        for point in args.infile
    ])
    whitened = whiten(points)
    centroids, distortion = kmeans(whitened, args.number_of_vans)
    index, distortion = vq(whitened, centroids)

    vans = [[] for _ in range(args.number_of_vans)]

    for i, point in enumerate(data):
        point_id = point.get('id')
        vans[index[i]].append(point_id)

    create_output(args.outfile, vans)

if __name__ == '__main__':
    main()
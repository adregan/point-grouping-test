import argparse
import json
import math
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

def distance(point_1, point_2):
    ''' distance: Point Point -> Int
        computes the distance between two points
    '''

    return math.sqrt(
        math.pow((point_2[1]-point_1[1]), 2) + 
        math.pow((point_2[0]-point_1[0]), 2))

def distribute(vans, number_of_points, centroids):
    ideal_avg_points = math.floor(number_of_points / len(vans))

    vans_less = []
    vans_more = []

    for i, van in enumerate(vans):
        stops = len(van)
        if stops < ideal_avg_points:
            vans_less.append(
                {'index': i, 'centroid': centroids[i], 'count': stops})
        if stops > ideal_avg_points:
            vans_more.append(
                {'index': i, 'centroid': centroids[i], 'count': stops})

    # What I want to do is check that the distance to a point is less 
    # than the distance between the two centroids

    while len(vans_less) > 0:
        try: 
            more = vans_more.pop()
        except IndexError:
            print(more)
            pass

        less = vans_less.pop()

        available_points = list(vans[more.get('index')])
        more_center = more.get('centroid')
        less_center = less.get('centroid')

        distance_btw_centers = distance(more_center, less_center)

        while len(vans[less.get('index')]) < ideal_avg_points:
            farthest_distance = 0
            farthest = {}

            for i, point in enumerate(available_points):
                dist = distance(
                    more_center, [point.get('lon'), point.get('lat')])

                if dist > farthest_distance:
                    farthest_distance = dist
                    farthest['index'] = i
                    farthest['point'] = point

            farthest_point = farthest.get('point')
            distance_to_less_center = distance(
                less_center,
                [farthest_point.get('lon'), farthest_point.get('lat')])

            if distance_to_less_center < distance_btw_centers:
                vans[less.get('index')].append(farthest_point)
                vans[more.get('index')].pop(farthest.get('index'))
            else:
                available_points.pop(farthest.get('index'))

    return vans

def main():
    args = get_args()
    data = args.infile
    points = np.array([
        [point.get('lon'), point.get('lat')]
        for point in args.infile
    ])

    centroids, distortion = kmeans(points, args.number_of_vans)
    index, distortion = vq(points, centroids)

    vans = [[] for _ in range(args.number_of_vans)]

    for i, point in enumerate(data):
        point_id = point.get('id')
        vans[index[i]].append(point_id)

    create_output(args.outfile, vans)

if __name__ == '__main__':
    main()
import argparse
import json
import math
import numpy as np
from scipy.cluster.vq import vq, kmeans
import sys
from io import TextIOWrapper

def JSONFile(file_input, stdin=False):
    ''' JSONFile : Str -> List
        Implements a custom argument type that takes a filepath,
        reads the file's data and returns it as loaded JSON.
    '''
    try:
        if not stdin:
            with open(file_input, 'r') as file:
                points = json.loads(file.read())
        else:
            data = file_input.read()
            points = json.loads(data)
    except FileNotFoundError as err:
        raise argparse.ArgumentTypeError(
            'The file {0} couldn\'t be found'.format(file_input))
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
    # Number of vans is a positional argument and doesn't need a flag
    # (but is required)
    parser.add_argument(
        'number_of_vans',
        type=int,
        help='The number of vans running today.'
    )

    # Using custom type to handle the JSON loading
    parser.add_argument(
        '-i',
        '--infile',
        type=JSONFile,
        dest='infile',
        default=sys.stdin,
        help='The path to the input file. Default is stdin.')


    parser.add_argument(
        '-o',
        '--outfile',
        type=str,
        dest='outfile',
        default=sys.stdout,
        help='The name of the outfile. Default is stdout.')

    return parser.parse_args()

def create_output(outfile, vans_data):
    ''' create_output : (Str | IO) List -> IO
        Can take either a Stdout object or a file name and write
        the data.
    '''
    output = []
    for van in vans_data:
        output.append([p.get('id') for p in van])
    if isinstance(outfile, TextIOWrapper):
        outfile.write(json.dumps(output, indent=2))
    else:
        with open(outfile, 'w') as file:
            file.write(json.dumps(output, indent=2))

def distance(point_1, point_2):
    ''' distance: Point Point -> Int
        computes the distance between two points
    '''

    return math.sqrt(
        math.pow((point_2[1]-point_1[1]), 2) + 
        math.pow((point_2[0]-point_1[0]), 2))

def find_closest_with_more(less, vans_more):
    ''' find_closest_with_more: Dict List -> Tuple
        Will find the closest grouping with more points than it needs
        to the grouping with too few. Returns the closest grouping and an
        updated list of groupings with more.
    '''
    vans_more_copy = list(vans_more)
    closest_distance = float('inf')
    more = None
    more_index = None
    for i, van in enumerate(vans_more):
        dist = distance(less.get('centroid'), van.get('centroid'))
        if dist < closest_distance:
            closest_distance = dist
            more_index = i

    if more_index != None:
        more = vans_more_copy.pop(more_index)

    return more, vans_more_copy

def distribute(vans, number_of_points, centroids):
    ''' distribute : List Int List -> List
        Will try to balance the number of points in a grouping by finding
        groupings with more points than is ideal and moving them to nearby
        groupings with too few points.
    '''
    ideal_avg_points = math.floor(number_of_points / len(vans))

    vans_less = []
    vans_more = []

    for i, van in enumerate(vans):
        stops = len(van)
        if stops < ideal_avg_points and stops != 0:
            vans_less.append(
                {'index': i, 'centroid': centroids[i], 'count': stops})
        if stops > ideal_avg_points:
            vans_more.append(
                {'index': i, 'centroid': centroids[i], 'count': stops})

    if not vans_less:
        return vans

    vans_less = sorted(vans_less, key=lambda van: van.get('count'))
    vans_more = sorted(vans_more, key=lambda van: van.get('count'), reverse=True)

    less = vans_less.pop()
    more, vans_more = find_closest_with_more(less, vans_more)

    while less and more:
        available_points = list(vans[more.get('index')])
        more_center = more.get('centroid')
        less_center = less.get('centroid')

        distance_btw_centers = distance(more_center, less_center)

        while (len(vans[less.get('index')]) < ideal_avg_points 
            and len(vans[more.get('index')]) > ideal_avg_points
            and len(available_points) > 0):

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
                available_points.pop(farthest.get('index'))
            else:
                available_points.pop(farthest.get('index'))

        try:
            less = vans_less.pop()
        except IndexError:
            less = None

        if len(vans[more.get('index')]) <= ideal_avg_points:
            try:
                more, vans_more = find_closest_with_more(less, vans_more)
            except:
                more = None

    return vans

def main():
    args = get_args()
    # This catches files sent in with stdin
    if isinstance(args.infile, TextIOWrapper):
        data = JSONFile(args.infile, True)
    else:
        data = args.infile

    points = np.array([
        [point.get('lon'), point.get('lat')]
        for point in data
    ])

    # In testing, found that a higher number of iterations led to less
    # errors due to missing centroids (Note: whitening led to worse results)
    centroids, distortion = kmeans(points, args.number_of_vans, 2000)
    index, distortion = vq(points, centroids)

    vans = [[] for _ in range(args.number_of_vans)]

    for i, point in enumerate(data):
        vans[index[i]].append(point)

    vans = distribute(vans, len(data), centroids)


    create_output(args.outfile, vans)

if __name__ == '__main__':
    main()
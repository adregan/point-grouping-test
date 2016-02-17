## Requirements

- Python 3
- pip
- pyvenv

## To install

1) `git clone https://github.com/adregan/point-grouping-test.git`
2) `cd point-grouping-test`
3) `pyvenv env`
4) `source env/bin/activate`
5) `pip install -r requirements.txt`
6) `python main.py 3 -i points.json -o groups.json`

## Usage

`python main.py -h` to see all the available options and required arguments. By default, this program accepts input from `stdin` and outputs by default to `stdout`:

`cat points.json | python main.py 3 > groups.json`

You can pass in a file using the `-i` flag and specify your output file with the `-o` flag:

`python main.py 3 -i points.json -o groups.json`

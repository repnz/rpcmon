import json
import sys


def main():
    input_file = sys.argv[1]
    cmd = sys.argv[2]
    exp = eval(sys.argv[3])

    with open(input_file, 'r') as f:
        objects = json.load(f)

    if not isinstance(objects, list):
        raise Exception("jsonfilter can work only with lists")

    if cmd == 'map':
        objects = list(map(exp, objects))

    elif cmd == 'filter':
        objects = list(filter(exp, objects))

    elif cmd == 'set':
        objects = list(set(map(exp, objects)))

    elif cmd == 'count':
        objects = sum(1 for x in objects if exp(x))

    elif cmd == 'group_count':
        group_count = {}

        for obj in objects:
            key = exp(obj)
            group_count[key] = group_count.get(key, 0) + 1

        objects = group_count

    json.dump(objects, sys.stdout, indent=4)


if __name__ == '__main__':
    main()

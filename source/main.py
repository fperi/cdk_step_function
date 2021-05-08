import argparse
import sys


def main():

    """
    The entrypoint of the package. Does nothing if not printing the parameters
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--parameter", type=str, help="parameter", required=True)
    args = parser.parse_args()
    parameter = str(args.parameter)

    print(f"Entrypoint running with parameter {parameter}")

    sys.exit(0)


if __name__ == "__main__":

    main()

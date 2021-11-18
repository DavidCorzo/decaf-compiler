import argparse

def decaf_cli() -> dict:
    parser = argparse.ArgumentParser()
    parser.add_argument('--o', help="rename file with -o")
    parser.add_argument('--target', help="-target <stage>", choices=["scanner", "parser", "semantic", "codegen"])
    parser.add_argument('--debug', help="-debug <stage>", action='store_true')
    args = parser.parse_args()
    return args.__dict__

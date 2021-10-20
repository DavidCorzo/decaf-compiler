import argparse

def command_line_interpreter() -> dict:
    parser = argparse.ArgumentParser()
    parser.add_argument('--o', help="rename file with -o")
    parser.add_argument('--target', help="-target <stage>", choices=["scan", "parse", "ast", "irt", "codegen"])
    parser.add_argument('--debug', help="-debug <stage>")
    args = parser.parse_args()
    return args.__dict__


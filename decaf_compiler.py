from decaf_cli import decaf_cli
from decaf_scanner import scanner

TOKEN_FILENAME = './tokens.yaml'
RENAME_EXECUTABLE, TARGET_STAGE, DEBUG = 'o', 'target', 'debug'
if __name__ == '__main__':
    cla = decaf_cli()
    # code = scanner("./src_code.decaf", "./tokens.yaml")

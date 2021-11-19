from decaf_cli import decaf_cli
from decaf_scanner import scanner
from decaf_parser import lr_0, lr_0_t, parser
from decaf_semantic import semantic
from decaf_codegen import codegen

RENAME_EXECUTABLE, TARGET_STAGE, DEBUG, SOURCE_CODE = 'o', 'target', 'debug', 'source_code'
STAGES = {'scanner':1, 'parser':2, 'semantic':3, 'codegen':4, None: 4}

SCANNER_TOKEN_FILENAME_WO_EXT = 'tokens'

PARSER_STARTING_PRODUCTION = '<program>'
PARSER_PRODUCTIONS_FILENAME = './productions.yaml'

if __name__ == '__main__':
    cla = {'source_code': 'src_code.decaf', 'o': 'decaf_program.executable', 'target': 'scanner', 'debug': False} # decaf_cli()
    target, target_index = cla[TARGET_STAGE], 0
    debug = cla[DEBUG]
    executable_name = None
    if cla[RENAME_EXECUTABLE]:
        executable_name = cla[RENAME_EXECUTABLE]
    else:
        executable_name = cla[SOURCE_CODE].replace('.decaf', '.executable')
    source_code = cla[SOURCE_CODE]
    scanner_instance = parser_instance = semantic_instance = codegen_instance = None
    if target_index != target:
        scanner_instance = scanner(source_code, SCANNER_TOKEN_FILENAME_WO_EXT, build=1, save=1)
        if debug:
            scanner_instance.debug()
        target_index += 1
    if target_index != target:
        lr_0_dfa = lr_0(PARSER_STARTING_PRODUCTION, PARSER_PRODUCTIONS_FILENAME, build=1, save=1)
        lr_0_table = lr_0_t(lr_0_dfa)
        parser_instance = parser(lr_0_table, scanner_instance)
        print(parser_instance)
        if debug:
            parser_instance.debug()
        target_index += 1
    if target_index != target:
        semantic_instance = semantic(parser_instance)
        if debug:
            semantic_instance.debug()
        target_index += 1
    if target_index != target:
        codegen_instance = codegen(semantic_instance, executable_name)
        # if debug:
        #     codegen_instance.debug()

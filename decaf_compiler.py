from decaf_cli import decaf_cli
from decaf_scanner import scanner
from decaf_parser import lr_0, lr_0_t, parser
from decaf_semantic import semantic
from decaf_codegen import codegen

intended_print = print

RENAME_EXECUTABLE, TARGET_STAGE, DEBUG, SOURCE_CODE = 'o', 'target', 'debug', 'source_code'
STAGES = {'scanner':1, 'parser':2, 'semantic':3, 'codegen':4, None: 4}

SCANNER_TOKEN_FILENAME_WO_EXT = './decaf_scanner/tokens'

PARSER_STARTING_PRODUCTION = '<program>'
PARSER_PRODUCTIONS_FILENAME = './decaf_parser/productions'

if __name__ == '__main__':
    cla = decaf_cli()# {'source_code': 'src_code.decaf', 'o': 'decaf_program', 'target': None, 'debug': True}
    target, target_index = STAGES[cla[TARGET_STAGE]], 0
    debug = cla[DEBUG]
    executable_name = 'a'
    if cla[RENAME_EXECUTABLE]:
        executable_name = cla[RENAME_EXECUTABLE]
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
        if debug:
            parser_instance.debug()
        target_index += 1
    if target_index != target:
        semantic_instance = semantic(parser_instance)
        if debug:
            semantic_instance.debug()
        target_index += 1
    if target_index != target:
        codegen_instance = codegen(semantic_instance, executable_filename=executable_name)
        if debug:
            codegen_instance.debug()
        intended_print(f"\nCompiled Successfully to ./{executable_name}.asm consult decaf_debug/codegen_debug.asm for commented and formated file.")

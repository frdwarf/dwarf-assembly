/** Entry point */

#include <iostream>
#include <cstdlib>

#include "SimpleDwarf.hpp"
#include "DwarfReader.hpp"
#include "CodeGenerator.hpp"

using namespace std;


int main(int argc, char** argv) {
    if(argc < 2) {
        cerr << "Error: missing input file. Usage:" << endl
             << argv[0] << " path/to/binary.elf" << endl;
        exit(1);
    }

    SimpleDwarf parsed_dwarf = DwarfReader(argv[1]).read();

    cerr << parsed_dwarf;

    cerr << "=====================" << endl << endl;

    CodeGenerator code_gen(parsed_dwarf, cout);
    code_gen.generate();

    return 0;
}

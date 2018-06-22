/** Entry point */

#include <iostream>
#include <sstream>
#include <cstdlib>

#include "SimpleDwarf.hpp"
#include "DwarfReader.hpp"
#include "CodeGenerator.hpp"
#include "PcHoleFiller.hpp"
#include "ConseqEquivFilter.hpp"

#include "settings.hpp"

using namespace std;

struct MainOptions {
    std::string elf_path;
};

MainOptions options_parse(int argc, char** argv) {
    MainOptions out;

    bool seen_switch_gen_policy = false;
    bool print_helptext = false;
    int exit_status = -1;

    for(int option_pos = 1; option_pos < argc; ++option_pos) {
        std::string option(argv[option_pos]);

        if(option.find("-") != 0) { // This is not an option argument
            out.elf_path = option;
        }

        else if(option == "--help") {
            print_helptext = true;
            exit_status = 0;
        }

        else if(option == "--switch-per-func") {
            seen_switch_gen_policy = true;
            settings::switch_generation_policy =
                settings::SGP_SwitchPerFunc;
        }
        else if(option == "--global-switch") {
            seen_switch_gen_policy = true;
            settings::switch_generation_policy =
                settings::SGP_GlobalSwitch;
        }

        else if(option == "--pc-list") {
            if(option_pos + 1 == argc) { // missing parameter
                exit_status = 1;
                print_helptext = true;
            }
            else {
                ++option_pos;
                settings::pc_list = argv[option_pos];
            }
        }

        else if(option == "--enable-deref-arg") {
            settings::enable_deref_arg = true;
        }
    }

    if(!seen_switch_gen_policy) {
        cerr << "Error: please use either --switch-per-func or "
             << "--global-switch." << endl;
        print_helptext = true;
        exit_status = 1;
    }
    if(out.elf_path.empty()) {
        cerr << "Error: missing input file." << endl;
        print_helptext = true;
        exit_status = 1;
    }

    if(print_helptext) {
        cerr << "Usage: "
             << argv[0]
             << " [--switch-per-func | --global-switch]"
             << " [--enable-deref-arg]"
             << " [--pc-list PC_LIST_FILE] elf_path"
             << endl;
    }
    if(exit_status >= 0)
        exit(exit_status);

    return out;
}

int main(int argc, char** argv) {
    MainOptions opts = options_parse(argc, argv);
    SimpleDwarf parsed_dwarf = DwarfReader(opts.elf_path).read();

    SimpleDwarf filtered_dwarf =
        PcHoleFiller()(
        ConseqEquivFilter()(
            parsed_dwarf));

    CodeGenerator code_gen(
            filtered_dwarf,
            cout,
            [](const SimpleDwarf::Fde& fde) {
                std::ostringstream ss;
                ss << "_fde_" << fde.beg_ip;
                return ss.str();
            });
    code_gen.generate();

    return 0;
}

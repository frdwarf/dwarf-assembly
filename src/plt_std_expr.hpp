#pragma once

#include <dwarfpp/expr.hpp>

static const dwarf::encap::loc_expr REFERENCE_PLT_EXPR(
        std::vector<dwarf::encap::expr_instr> {
            {
               {
                   .lr_atom  = 0x77,
                   .lr_number = 8,
                   .lr_number2 = 0,
                   .lr_offset = 0
               },
               {
                   .lr_atom  = 0x80,
                   .lr_number = 0,
                   .lr_number2 = 0,
                   .lr_offset = 2
               },
               {
                   .lr_atom  = 0x3f,
                   .lr_number = 15,
                   .lr_number2 = 0,
                   .lr_offset = 4
               },
               {
                   .lr_atom  = 0x1a,
                   .lr_number = 0,
                   .lr_number2 = 0,
                   .lr_offset = 5
               },
               {
                   .lr_atom  = 0x3b,
                   .lr_number = 11,
                   .lr_number2 = 0,
                   .lr_offset = 6
               },
               {
                   .lr_atom  = 0x2a,
                   .lr_number = 0,
                   .lr_number2 = 0,
                   .lr_offset = 7
               },
               {
                   .lr_atom  = 0x33,
                   .lr_number = 3,
                   .lr_number2 = 0,
                   .lr_offset = 8
               },
               {
                   .lr_atom  = 0x24,
                   .lr_number = 0,
                   .lr_number2 = 0,
                   .lr_offset = 9
               },
               {
                   .lr_atom  = 0x22,
                   .lr_number = 0,
                   .lr_number2 = 0,
                   .lr_offset = 10
               }
            }
            });

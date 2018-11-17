Disclaimer of Warranty:
-----------------------
This software code and all associated documentation, comments or other 
information (collectively "Software") is provided "AS IS" without 
warranty of any kind. MICRON TECHNOLOGY, INC. ("MTI") EXPRESSLY 
DISCLAIMS ALL WARRANTIES EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED 
TO, NONINFRINGEMENT OF THIRD PARTY RIGHTS, AND ANY IMPLIED WARRANTIES 
OF MERCHANTABILITY OR FITNESS FOR ANY PARTICULAR PURPOSE. MTI DOES NOT 
WARRANT THAT THE SOFTWARE WILL MEET YOUR REQUIREMENTS, OR THAT THE 
OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE. 
FURTHERMORE, MTI DOES NOT MAKE ANY REPRESENTATIONS REGARDING THE USE OR 
THE RESULTS OF THE USE OF THE SOFTWARE IN TERMS OF ITS CORRECTNESS, 
ACCURACY, RELIABILITY, OR OTHERWISE. THE ENTIRE RISK ARISING OUT OF USE 
OR PERFORMANCE OF THE SOFTWARE REMAINS WITH YOU. IN NO EVENT SHALL MTI, 
ITS AFFILIATED COMPANIES OR THEIR SUPPLIERS BE LIABLE FOR ANY DIRECT, 
INDIRECT, CONSEQUENTIAL, INCIDENTAL, OR SPECIAL DAMAGES (INCLUDING, 
WITHOUT LIMITATION, DAMAGES FOR LOSS OF PROFITS, BUSINESS INTERRUPTION, 
OR LOSS OF INFORMATION) ARISING OUT OF YOUR USE OF OR INABILITY TO USE 
THE SOFTWARE, EVEN IF MTI HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH 
DAMAGES. Because some jurisdictions prohibit the exclusion or 
limitation of liability for consequential or incidental damages, the 
above limitation may not apply to you.

Copyright 2003 Micron Technology, Inc. All rights reserved.

Getting Started:
----------------
Unzip the included files to a folder.
Compile ddr3.v and tb.v in a verilog simulator.
Simulate the top level test bench tb.
Or, if you are using the ModelSim simulator, type "do tb.do" at the prompt.

File Descriptions:
------------------
ddr3.v                      -ddr3 model
ddr3_mcp.v                  -structural wrapper for ddr3 - multi-chip package model
ddr3_module.v               -structural wrapper for ddr3 - module model
1024Mb_ddr3_parameters.vh   -file that contains all 1Gb parameters used by the model
2048Mb_ddr3_parameters.vh   -file that contains all 2Gb parameters used by the model
4096Mb_ddr3_parameters.vh   -file that contains all 4Gb parameters used by the model
8192Mb_ddr3_parameters.vh   -file that contains all 8Gb parameters used by the model
readme.txt                  -this file
tb.v                        -ddr3 model test bench
subtest.vh                  -example test included by the test bench.

Defining the Speed Grade:
-------------------------
The verilog compiler directive "`define" may be used to choose between 
multiple speed grades supported by the ddr3 model.  Allowable speed 
grades are listed in the ddr3_parameters.vh file and begin with the 
letters "sg".  The speed grade is used to select a set of timing 
parameters for the ddr3 model.  The following are examples of defining 
the speed grade.

    simulator   command line
    ---------   ------------
    ModelSim    vlog +define+sg25 ddr3.v
    VCS         vcs +define+sg25 ddr3.v
    NC-Verilog  ncverilog +define+sg25 ddr3.v

Defining the Organization:
--------------------------
The verilog compiler directive "`define" may be used to choose between 
multiple organizations supported by the ddr3 model.  Valid 
organizations include "x4", "x8", and x16, and are listed in the 
ddr3_parameters.vh file.  The organization is used to select the amount 
of memory and the port sizes of the ddr3 model.  The following are
examples of defining the organization.

    simulator   command line
    ---------   ------------
    ModelSim    vlog +define+x8 ddr3.v
    NC-Verilog  ncverilog +define+x8 ddr3.v
    VCS         vcs +define+x8 ddr3.v

All combinations of speed grade and organization are considered valid 
by the ddr3 model even though a Micron part may not exist for every 
combination.

Allocating Memory:
------------------
An associative array has been implemented to reduce the amount of 
static memory allocated by the ddr3 model.  Each entry in the 
associative array is a burst length of eight in size.  The number of 
entries in the associative array is controlled by the MEM_BITS 
parameter, and is equal to 2^MEM_BITS.  For example, if the MEM_BITS 
parameter is equal to 10, the associative array will be large enough 
to store 1024 writes of burst length 8 to unique addresses.  The 
following are examples of setting the MEM_BITS parameter to 8.

    simulator   command line
    ---------   ------------
    ModelSim    vsim -GMEM_BITS=8 ddr3
    NC-Verilog  ncverilog +defparam+ddr3.MEM_BITS=8 ddr3.v
    VCS         vcs -pvalue+MEM_BITS=8 ddr3.v

It is possible to allocate memory for every address supported by the 
ddr3 model by using the verilog compiler directive "`define MAX_MEM".
This procedure will improve simulation performance at the expense of 
system memory.  The following are examples of allocating memory for
every address.

    Simulator   command line
    ---------   ------------
    ModelSim    vlog +define+MAX_MEM ddr3.v
    NC-Verilog  ncverilog +define+MAX_MEM ddr3.v
    VCS         vcs +define+MAX_MEM ddr3.v

**********************************************************************
The following information is provided to assist the modeling engineer 
in creating multi-chip package (mcp) models.  ddr3_mcp.v is a 
structural wrapper that instantiates ddr3 models.  This wrapper can be 
used to create single, dual, or quad rank mcp models.  From the 
perspective of the model, the only item that needs to be defined is the 
number of ranks.
**********************************************************************

Defining the Number of Ranks in a multi-chip package:
----------------------------------------------------
The verilog compiler directive "`define" may be used to choose between 
single, dual, and quad rank mcp configurations.  The default is single 
rank if nothing is defined.  Dual rank configuration can be selected by 
defining "DUAL_RANK" when the ddr3_mcp is compiled.  Quad rank 
configuration can be selected by defining "QUAD_RANK" when the ddr3_mcp 
is compiled.  The following are examples of defining a dual rank mcp 
configuration.

    simulator   command line
    ---------   ------------
    ModelSim    vlog +define+DUAL_RANK ddr3.v ddr3_mcp.v
    NC-Verilog  ncverilog +define+DUAL_RANK ddr3.v ddr3_mcp.v
    VCS         vcs +define+DUAL_RANK ddr3.v ddr3_mcp.v

**********************************************************************
The following information is provided to assist the modeling engineer 
in creating DIMM models.  ddr3_module.v is a structural wrapper that 
instantiates ddr3 models.  This wrapper can be used to create UDIMM, 
RDIMM or SODIMM models.  Other form factors are not supported 
(MiniDIMM, VLP DIMM, etc.).  From the perspective of the model, the 
items that need to be defined are the number of ranks, the module 
type, and the presence of ECC.  All combinations of ranks, module 
type, and ECC are considered valid by the ddr3_module model even 
though a Micron part may not exist for every combination.
**********************************************************************

Defining the Number of Ranks on a module:
----------------------------------------
The verilog compiler directive "`define" may be used to choose between 
single, dual, and quad rank module configurations.  The default is single 
rank if nothing is defined.  Dual rank configuration can be selected by 
defining "DUAL_RANK" when the ddr3_module is compiled.  Quad rank 
configuration can be selected by defining "QUAD_RANK" when the ddr3_module 
is compiled.  The following are examples of defining a dual rank module 
configuration.

    simulator   command line
    ---------   ------------
    ModelSim    vlog +define+DUAL_RANK ddr3.v ddr3_module.v
    NC-Verilog  ncverilog +define+DUAL_RANK ddr3.v ddr3_module.v
    VCS         vcs +define+DUAL_RANK ddr3.v ddr3_module.v

Defining the Module Type:
-----------------------------------
The verilog compiler directive "`define" may be used to choose between 
UDIMM, RDIMM, and SODIMM module configurations.  The default is 
unregistered (UDIMM) if nothing is defined.  SODIMM configuration can be 
selected by defining "SODIMM" when the ddr3_module is compiled.  Registered 
configuration can be selected by defining "RDIMM" when the ddr3_module is 
compiled.  The following are examples of defining a registered module 
configuration.

    simulator   command line
    ---------   ------------
    ModelSim    vlog +define+RDIMM ddr3.v ddr3_module.v
    NC-Verilog  ncverilog +define+RDIMM ddr3.v ddr3_module.v
    VCS         vcs +define+RDIMM ddr3.v ddr3_module.v

Defining the ECC for a module:
-----------------------------
The verilog compiler directive "`define" may be used to choose between 
ECC and nonECC module configurations.  The default is nonECC if nothing 
is defined.  ECC configuration can be selected by defining "ECC" when 
the ddr3_module is compiled.  The following are examples of defining an
ECC module configuration.

    simulator   command line
    ---------   ------------
    ModelSim    vlog +define+ECC ddr3.v ddr3_module.v
    NC-Verilog  ncverilog +define+ECC ddr3.v ddr3_module.v
    VCS         vcs +define+ECC ddr3.v ddr3_module.v

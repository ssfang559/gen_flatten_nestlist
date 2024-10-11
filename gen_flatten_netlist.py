#! /apps/local/bin/python3.7

import sys
import os
from optparse import OptionParser
import re

def help():
    print('''
***********************
 - gen_flatten_netlist -
***********************
 => Usage:
 gen_flatten_netlist --netlist <input spice netlist>
                      --top <netlist top cell name>
                      --process <imc19n_TX imc19n_RW imc19n_LP_RW cxmt10G3 cxmt10G3_LP>
                      --metal <1p3m1x1y1z/1p4m1x2y1z>
                      --hcell <hcell file>
                      help <Usage>
 => Example:
 % gen_flatten_netlist --netlist Top_Cell.cdl --top Top_Cell --process imc19n_RW --metal 1p3m1x1y1z (--hcell hcell)

----------------------
-> Version : 1.0
   Author: Shanshan Fang
    ''')
    sys.exit()

parse = OptionParser()
parse.add_option('--netlist',dest='netlist')
parse.add_option('--top',dest='top')
parse.add_option('--hcell',dest='hcell')
parse.add_option('--process',dest='process')
parse.add_option('--metal',dest='metal')
options = parse.parse_args()[0]
opt_netlist=options.netlist
opt_top=options.top
opt_hcell=options.hcell
opt_process=options.process
opt_metal=options.metal
if (opt_netlist is None) | (opt_top is None) | (opt_process is None) | (opt_metal is None) :
    help()  

work_dir=os.getcwd()
hcell=work_dir+"/gen_flatten_netlist.hcell"
calibre_qs_exec=work_dir+"/calibre_qs_exec.tcl"
calibre_cmd=work_dir+"/gen_flatten_netlist.csh"
new_rule=work_dir+'/'+opt_process+'_'+opt_metal+'.rule'

def gen_hcell(write_file,str1):
    with open(write_file,mode='w') as f:
        f.write(str1+'\t'+str1)

#Generate gen_flatten_netlist.hcell
if opt_hcell is None:
    gen_hcell(hcell,opt_top)
else:
    hcell=opt_hcell

#Read the input calibreLVS.rule and generate a new rule file
def gen_lvsrule(str0,str1,write_file,str3):
    with open(write_file,'w') as f:
        for line in open("/apps/imctf/runset/calibre/"+opt_process+"/current/"+opt_metal+"/calibreLVS.rule",'r'):
            if re.findall(r'LAYOUT PATH',line):
                f.write('LAYOUT PATH '+'"'+str0+'"'+'\n')
            elif re.findall(r'LAYOUT PRIMARY',line):
                f.write('LAYOUT PRIMARY '+'"'+str1+'"'+'\n')
            elif re.findall(r'LAYOUT SYSTEM',line):
                f.write('LAYOUT SYSTEM '+str3+'\n')
            elif re.findall(r'SOURCE PATH',line):
                f.write('SOURCE PATH '+'"'+str0+'"'+'\n')
            elif re.findall('SOURCE PRIMARY',line):
                f.write('SOURCE PRIMARY '+'"'+str1+'"'+'\n')
            else:
                f.write(line)             

#Generate calibre_qs_exec.tcl file 
def gen_calibre_qs_exec(str0,str1,str2):
    with open(calibre_qs_exec,'w') as f:
        f.write('#!/bin.csh\n\n')
        f.write('set ns [dfm::read_netlist -source -rules '+str0+' -hcell '+str2+' -netlist_transforms { trivial_pins deep_shorts high_shorts reduced } ]\n')
        f.write('dfm::write_spice_netlist '+str1+'_flatten.spi'+' -netlist_handle $ns\n')
        f.write('dfm::close_netlist\n\n')
        f.write('quit\n')

#Generate gen_flatten_netlist.csh file
def gen_run_csh(write_file,str1,str2,str3):
    with open(write_file,'w') as f:
        f.write('#!/bin/csh\n')
        f.write('calibre -qs -exec '+str2+'\n')

gen_lvsrule(opt_netlist,opt_top,new_rule,'SPICE')
gen_calibre_qs_exec(new_rule,opt_top,hcell)
gen_run_csh(calibre_cmd,opt_top,calibre_qs_exec,new_rule)

os.system('chmod 755 '+calibre_qs_exec)
os.system('chmod 755 '+calibre_cmd)

print('Running '+calibre_cmd+'...\n')
os.system(calibre_cmd+' | tee gen_flatten_netlist.log')

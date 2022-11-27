import tac
import cfg
import ssagen
import sys
import json
from cfg import CFG
from cfg import recompute_liveness

def DSE(cfg):
    # DSE (Global Dead Store Elimination)
    modified = True
    while modified:
        modified = False
        #live-in and live-out sets as dictionaries that map tac.Instr objects to sets of temporaries
        livein, liveout = dict(), dict()
        #livein,liveout are emptied out & replaced with the corresponding live sets
        recompute_liveness(cfg, livein, liveout)
        for instr in cfg.instrs():
            #instructions without side-effects
            if instr.opcode not in ('div', 'mod', 'call') and (instr.dest != None) and (instr.dest not in liveout[instr]):
                modified = True
                # delete dead store instr
                for block in cfg._blockmap.values():
                    if instr in block.body:
                        block.body.remove(instr)
                        break
            elif instr.opcode in ('div', 'mod', 'call'):
                continue
    return cfg

def GCP(decl, cfg):
    #updates the cfg.CFG instance with its SSA form (crude).
    #arguments : tac.Proc instance & its cfg.CFG instance 
    ssagen.crude_ssagen(procs[decl], cfg[decl])
    # GCP (Copy Propagation)
    # no need to rerun it.
    for instr in cfg.instrs():
        #for every copy instruction of the form %u = copy %v
        if instr.opcode == "copy":
            replace = instr.dest
            #globally replace every occurrence of %u by %v 
            replaced = instr.arg1
            removed = False
            for block in cfg._blockmap.values():
                if instr in block.body:
                    if not removed:
                        removed = True
                        block.body.remove(instr)
                for temp_instr in block.body:
                    if (temp_instr.dest in gvars.keys()):
                        continue
                    if temp_instr.opcode == "phi":
                        # replace temp in phi functions
                        for (label, temp) in temp_instr.arg1.items():
                            if temp in gvars.keys():
                                continue
                            elif temp == replace:
                                temp_instr.arg1[label] = replace
                    else:
                        #for each arg
                        if (temp_instr.arg1 == replace) and (temp_instr.arg1 not in gvars.keys()):
                            temp_instr.arg1 = replaced
                        if (temp_instr.arg2 == replace) and (temp_instr.arg2 not in gvars.keys()):
                            temp_instr.arg2 = replaced
    return cfg     

if __name__ == '__main__':
    optimized = []
    fname = sys.argv[-1]
    print('fname: ' + fname)

    gvars, procs = dict(), dict()
    tac_program = tac.load_tac(fname)
    #execute tac program
    for decl in tac_program:
        if isinstance(decl, tac.Gvar):
            gvars[decl.name] = decl
        else:
            procs[decl.name] = decl
    tac.execute(gvars, procs, '@main', [])
    print('after 1st execute')

    cfg_dict = dict()

    for name, CFG in cfg_dict.items():
        # to create CFG from TAC procedure
        cfg_dict[name] = cfg.infer(name)
        cfg_dict = DSE(CFG)        
    for name, CFG in cfg_dict.items():
        cfg_dict = GCP(name, CFG)
    # linearize CFG back into the body of TAC procedure
    for name, CFG in cfg_dict.items():
        cfg.linearize(procs[name], CFG)        
        
    # execution of TAC
    for decl in gvars.values():
        optimized.append(decl)
    for decl in procs.values():
        optimized.append(decl)
    #if only 1 filename
    if len(sys.argv) == 2:
        #output the optimized TAC (with SSA phi instructions) to standard output
        for instr in optimized:
            print(instr)
    #if input and output filenames
    else:
        #output the optimized TAC (with SSA phi instructions)to a file specified using the -o option
        with open(sys.argv[2], 'w') as tac_file:
            json.dump(optimized, tac_file)
    print('before 2nd execute')
    tac.execute(gvars, procs, '@main', [])
        
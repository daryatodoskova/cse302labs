"""
Compiler pass that performs the control flow optimization using CFG representation.
"""

import sys
import argparse
import json
from ast2tac import Instruction, Prog
from AST import VarDecl

_cond_jumps = {'jz', 'jnz', 'jl', 'jle', 'jnl', 'jnle'}

class Basicblock:
    def __init__(self, instrs):
        self.label = instrs[0].args[0]
        self.instrs = instrs
        self.child = set()
        self.parent = set()

    def add_parent(self, p_label):
        self.parent.add(p_label)

    def add_child(self, c_label):
        self.child.add(c_label)

    def __str__(self):
        return f'Label: {self.label} ; Instructions: {self.instrs}'

    def merge(self, block):
        self.instrs += block.instrs
        for child_label in block.child:
            self.child.add(child_label)

class CFG:
    def __init__(self, tac_file, proc_name):
        self.name = proc_name[1:]
        self.block_inference(tac_file)

    # construct the basic blocks from the instructions
    def block_inference(self, tac_file):
        self.block = dict()
        self.instructions = dict()

        # Add an entry label before first instruction if needed
        if (tac_file[0].opcode != 'label'):
            lentry = ".Lentry_" + self.name
            tac_file.insert(0, Instruction('label', lentry, None, None))
            self.entry_label = lentry
        else:
            self.entry_label = tac_file[0].args[0]

        count_label = 0
        tac_add = []
        i = 0

        while (i < len(tac_file)):
            if (i < len(tac_file) - 1):
                next = tac_file[i + 1]

            # For jumps, add a label after the instruction if one doesn’t already exist
            if (tac_file[i].opcode == 'jmp') and (i < len(tac_file) - 1) and (next.opcode != 'label'):
                new = Instruction('label', f'.Ljmp_{self.name}_{count_label}', None, None)
                count_label += 1
                tac_file.insert(i + 1, new)

            #Add explicit jmps for fall-throughs.
            elif (i >= 1) and (tac_file[i].opcode == 'label') and (tac_file[i - 1].opcode != 'jmp'):
                if (tac_file[i - 1].opcode == 'ret'):
                    tac_file.insert(i, Instruction('jmp', tac_file[i].args[0], None, 'tmp'))
                else:
                    tac_file.insert(i, Instruction('jmp', tac_file[i].args[0], None, None))

            self.instructions[Instr(tac_file[i])] = Instr(tac_file[i])
            tac_add.append(Instr(tac_file[i]))
            i += 1

        self.block[tac_file[0].args[0]] = Basicblock([self.instructions[self.tac_id[0]]])
        prev = tac_file[0].args[0]
        edges = []
        b_instr = []

        # Start a new block at each label

        for i in range(1, len(tac_file)):
            #accumulate instructions in the block until...
            b_instr.append(tac_file[i])
            #...encountering a jump
            if tac_file[i].opcode == 'jmp':
                # block until jmp instruction built
                self.blocks[new_block.label] = BasicBlock(b_instr)
                destination_label = tac_file[i].args[0]
                edges.append((new_block.label, destination_label))
                b_instr = []
            #...a ret
            elif tac_file[i].opcode == 'ret':
                self.blocks[new_block.label] = BasicBlock(b_instr)
                b_instr = []
            #...or another label
            elif tac_file[i].opcode in cond_jumps:
                source = block_instr[0].args[0]
                destination = tac_file[i].args[1]
                edges.append((source, destination))

        for (parent, child) in edges:
            self.block[parent].add_child(child)
            self.block[child].add_parent(parent)

        print("block inference done")


    def serialize(self, f=True):
        """
        Turns CFG back into an ordinary TAC sequence
        """
        entry_b = self.block[self.entry_label]
        serialized_instrs = entry_b.instrs
        serialized_labels = set([self.entry_label])

        def UCE(block):
            """
            Unreachable Code Elimination
            - runs after every simplification, particularly jump threading
            - all unreachable blocks are safely removed from the CFG
            """
            for child_label in block.successor:
                if child_label not in serialized_labels:
                    # Add current block to schedule
                    serialized_instrs.extend(self.block[child_label].instrs)
                    serialized_labels.add(child_label)
                    UCE(self.block[child_label])

        # Start with the block with the entry label
        UCE(entry_b)

        if f:
            jmps_to_simplify = []   ## Fall-Through
            for i in range(len(serialized_instrs) - 1):
                current_instr = serialized_instrs[i]
                if current_instr.opcode == 'jmp':
                    next_instr = serialized_instrs[i + 1]
                    if next_instr.opcode == 'label' and next_instr.args[0] == current_instr.args[0]:
                        jmps_to_simplify.append(index)

            if len(useless_jmps) > 0:
                #put them in right order before deleting
                jmps_to_simplify.reverse()
                for i in useless_jmps:
                    serialized_instrs.pop(i)

        return serialized_instrs

    def perform_UCE(self):
        serialized = self.serialize(False)
        self.block_inference(serialized)

    def jump_thread(self):

        def linear_seq_of_blocks(block, current_lin_seq):
            if len(block.child) == 1:
                child_label = list(block.child)[0]
                block = self.block[child_label]
                if (len(block.parent) == 1):
                    current_lin_seq += [child_label]
                    return linear_seq_of_blocks(block, current_lin_seq)
            return current_lin_seq

        old_labels = set()

        for label, block in self.block.items():

            # Jump Threading: Sequencing Unconditional Jumps

            lin_seq_of_block_labels = linear_seq_of_blocks(block, [label])[:-1]

            if len(lin_seq_of_block_labels) > 1:
                modified = True

                for i in range(1, len(lin_seq_of_block_labels) - 1):
                    # Only continue if each of B_2,...,B_{n-2} have empty bodies
                    blockseq = self.block[linear_seq_of_block_labels[i]].instrs[1:-1]
                    if len(lin_seq_of_block_labels[i]) > 2:
                        modified = False
                        break

                # Change the jmp instruction in B1 to point to Bn instead, so that next(B1) = {Bn}
                if modified:
                    first_block = self.block[lin_seq_of_block_labels[0]]
                    first_block.instrs[-1].instr.args[0] = lin_seq_of_block_labels[-1]
                    # Merge blocks into first_block
                    for i in lin_seq_of_block_labels[1:-1]:
                        first_block.merge(self.block[i])
                        old_labels.add(i)

            # Jump Threading: Turning Conditional into Unconditional Jumps

            for child_label in block.child:
                cond_temp = None
                # If there is a conditional jump from block to the child block
                for i in block.instrs:
                    if (i.opcode in _cond_jumps) and (i.args[1] == child_label):
                        cond_temp = i.args[0]
                        cond_jump = i.opcode

                if not cond_temp:
                    continue

                # Verify that cond_temp isn't modified in the child block
                modified = False
                for i in self.block[child_label].instrs:
                    if i.result == cond_temp:
                        modified = True
                        break
                if modified:
                    continue

                # Verify that a same cond_jump with the same cond_temp is in child block
                for i in range(len(child.instrs) - 1):
                    if (child.instrs[i].opcode == cond_jump) and (child.instrs[i].args[0] == cond_temp):
                        next = child.instrs[i].args[1]
                        child.instrs[i].opcode = 'nop'
                        if child.instrs[i + 1].opcode == 'jmp':
                            child.instrs[i + 1].args[0] = next

        # Delete blocks after merge
        for i in old_labels:
            self.block.pop(i, None)

    def coaleasce(self):
        """
        Coalescing of linear chains of blocks
        Done after every other CFG simplification phase
        """
        old_label = None
        for block in list(self.block.values()):
            # only 1 child
            if len(block.child) == 1:
                child_label = list(block.child)[0]
                child_block = self.block[child_label]
                # if the child block has only 1 parent and if it's not the entry block
                if (len(child_block.parent) == 1) and (child_label != self.entry_label):
                    # if the end of the parent block is 'jmp'
                    if block.instrs[-1].opcode == 'jmp':
                        # delete that last jmp
                        block.instrs[-1].opcode = 'nop'
                        # Merge both blocks
                        block.merge(child_block)
                        # child label will be deleted
                        old_label = child_label
                        break

        if old_label:
            self.block.pop(old_label)
            for block in self.block.values():
                # delete old labels from the child blocks
                if old_label in block.child:
                    block.child.remove(old_label)
                # delete old labels from the parent blocks
                if old_label in block.parent:
                    block.parent.remove(old_label)
            return (block.label, old_label)
        else:
            return False

    def coalescing(self):
        coalesced = set()
        while True:
            now_coalescing = self.coalesce()
            self.perform_UCE()
            #dead code cleaned
            if now_coalescing and now_coalescing not in coalesced_blocks:
                coalesced.add(now_coalescing)
            else:
                break

    def control_flow_optimization(self):
        """
        1. Jump threading (conditional & unconditional)
        2. UCE
        3. Coalescing
        """
        self.jump_thread()
        self.perform_UCE()
        self.coalescing()


#-------------------------------------------------------------------------------
#COMPLETE LOADING FILE

def load_tac(js_obj):
    res = []
    for decl in js_obj:
        if "proc" in decl.keys():
            tac = []
            for line in decl["body"]:
                op = line["opcode"]
                arg1 = None
                arg2 = None
                dest = line["result"]
                # 1 arg
                if (len(line["args"]) == 1):
                    arg1 = line["args"][0]
                # 2 args
                elif (len(line["args"]) == 2):
                    arg1 = line["args"][0]
                    arg2 = line["args"][1]
                tac.append(Instruction.__repr__(op, [arg1, arg2], dest))
            #...

def optimize_tac(filename):
    gvars = []
    procs = []
    with open(filename, 'r') as fp:
        js_obj = json.load(fp)
        tac = load_tac(js_obj)
    for decl in tac:
        #...


if __name__ == "__main__":
    opts, args = getopt.getopt(sys.argv[1:], '', [])
    optimize_tac(args[0])

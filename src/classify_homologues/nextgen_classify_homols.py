print('Starting up...')
from time import time
start = time()

import os
import argparse
#import sys
import rdkit.Chem as Chem
from utils import *
from rdkit.Chem import AllChem
from pathlib import Path
import rdkit.Chem.rdchem as rdchem
import rdkit.Chem.Draw as Draw
import rdkit.Chem.Descriptors
from rdkit.Chem import PandasTools
from rdkit.Chem.Draw import MolsToGridImage
import pandas as pd
import numpy as np
import datamol as dm



print("Homologue classification started...")

#parse inputs
parser = argparse.ArgumentParser()
parser.add_argument("-s", "--smiles", help="List of SMILES as input.")
parser.add_argument("-l", "--labels", help="List of labels as input.")
parser.add_argument("-ru", "--repeatingunits", help="Repeating unit as SMARTS string enclosed by speech marks. Default is CH2 i.e., '[#6&H2]'.")
parser.add_argument("-min", "--min_RU_in", help="Minimum length of RU chain, default = 3 units.", type=int)
parser.add_argument("-max", "--max_RU_in", help="Maximum length of RU chain, default = 30 units.", type=int)
parser.add_argument("-f", "--frag_in", help="No. of fragmentation steps separating RU from core(s).", type=int)
args = parser.parse_args()

print('all args parsed OK')

#read in smiles and labels
smiles, mols, smiles_torem, idxtorem = read_smiles_csv(args.smiles)
print('readsmilesOK')

labels = read_labels_csv(args.labels, idxtorem)
print('readlabelsOK')
df = pd.DataFrame({ "SMILES":smiles, "Mols":mols, "Labels":labels})
print('df OK')
#prepare repeating units
if args.repeatingunits:
    ru_in = args.repeatingunits + '-'
else:
    ru_in = '[#6&H2]-' #set CH2 as default RU

if args.min_RU_in:
    min_length = args.min_RU_in
else:
    min_length = 3

if args.max_RU_in:
    max_length = args.max_RU_in
else:
    max_length = 30

if args.frag_in:
    frag_steps = args.frag_in
else:
    frag_steps = 2 #set fragmentation_steps default as 2

ru = setup_repeating_unit(ru_in, min_length, max_length)
#tested '[#8]-[#6&H2]-[#6&H2]-', '[#6](-[#9])(-[#9])-', '[#8]-[#6](-[#9])(-[#9])-[#6](-[#9])(-[#9])', '[#8]-[#6&H](-[#9])','[#8]-[#6](-[#9])(-[#9])'
print("ru setup OK")

Path("output").mkdir(parents=True, exist_ok=True)
print("output folder setup OK")
write_removed_smiles(smiles_torem)
#detect RUs in mols
mols_no_ru_matches, labels_mols_no_ru_matches, mols_with_ru, labels_mols_with_ru = detect_repeating_units(mols, labels, ru)

print('detect_repeating_units OK')
#fragmentation into patts and cores, done n times (n = frag_steps)
lists_patts, lists_cores, empty_cores_idx = fragment_into_cores(mols_with_ru, ru, frag_steps)

print("Done fragment_into_cores.")

#detect and output molecules made solely of RUs
mols_made_of_ru, labels_made_of_ru, mols_to_classify, labels_to_classify = detect_mols_made_of_ru(mols_with_ru, labels_mols_with_ru, empty_cores_idx)
print("Done detect_mols_made_of_ru")


lists_patts, lists_cores = process_patts_cores(lists_patts, lists_cores, empty_cores_idx)
print("Done filtering out empty patts and cores")

classified_series, result_df = generate_df(lists_patts, lists_cores, mols_to_classify, labels_to_classify, df, mols_made_of_ru)
print("Done generate_df")


mols_nonseries, labs_nonseries, nonseries = detect_mols_nonseries(result_df)
print("Done detect_mols_nonseries")

grpdmols = detect_cores_classified_series(classified_series)
print('Done detect_cores_classified_series')

final_cores, leg_final_cores = depict_cores_summary(grpdmols)
print("Done depict_cores_summary")

generate_classified_series_summary(result_df)
print("Done generate_classified_series_summary")

#depict_classified_series(grpdmols, classified_series)
#print("Done depict_classified_series")

num_series, mols_classified = print_output_summary(result_df, nonseries, mols_no_ru_matches, mols_made_of_ru)
end = time()
print("Homologue classification complete! " + str(mols_classified) + " molecules have been classified into " +str(num_series) + " series." )
runtime = end - start
print('It took ' + str(runtime) + ' seconds.')
#output summary file
generate_output_summary(args.smiles, mols_classified, num_series, ru_in, mols_no_ru_matches, nonseries, mols_made_of_ru, min_length, max_length, frag_steps, runtime)
print("Classification summary generated.")

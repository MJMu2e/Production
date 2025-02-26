#!/usr/bin/env python

#Script to create and/or submit multiple campaign using Project-py
#Create ini files: ./ProjPy/gen_Campaigns.py --ini_file ProjPy/mdc2020_mixing.in --comb_json data/mix.json
#Create ini files: ./ProjPy/gen_Campaigns.py --ini_file ProjPy/mdc2020_primary.ini --comb_json data/primary.json --comb_type list --cutoff_key primary_name
#Create, upload and submit all campaign: ./ProjPy/gen_Campaigns.py --ini_file ProjPy/mdc2020_mixing.ini --cfg_file CampaignConfig/mdc2020_digireco.cfg --comb_json data/mix.json --upload --submit

#To upload setup poms-client first, delete voms-proxy (NOT as mu2epro!!!), get kx509:
#source /cvmfs/fermilab.opensciencegrid.org/packages/common/setup-env.sh
#spack load poms-client/hplsffi

import os
from itertools import product
import argparse
import json
import sys

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Script to submit multiple POMS campaigns through project_py")
requiredNamed = parser.add_argument_group('required arguments')
requiredNamed.add_argument("--ini_file", type=str, help="INI file", required=True)
requiredNamed.add_argument("--comb_json", type=str, help="JSON file that contains combinations to run over", required=True)
requiredNamed.add_argument("--comb_type", type=str, help="JSON file type: list or product", required=True)

parser.add_argument("--cutoff_key", type=str, help="Ignore keys in the campaign name after the cutoff_key", default=None)
parser.add_argument("--upload", action="store_true", help="Create campaigns")
parser.add_argument("--submit", action="store_true", help="Submit campaigns")
parser.add_argument("--test_run", action="store_true", help="Run in test run mode")
parser.add_argument("--ini_version", default="", type=str, help="Append version to the end of campaign name, i.e. _v1")

args = parser.parse_args()
ini_file = args.ini_file
comb_json = args.comb_json
comb_type = args.comb_type
cutoff_key = args.cutoff_key
ini_version = args.ini_version

upload = args.upload
submit = args.submit
test_run = args.test_run
ini_version = args.ini_version

# Load combo_dict from file
with open(comb_json, "r") as file:
    combo_dict = json.load(file)

print(os.path.basename(comb_json))

if comb_type == "product":
    list_values = list(product(*combo_dict.values()))
    list_keys = list(combo_dict.keys())
elif comb_type == "list":
    list_values = combo_dict
    list_keys = None        
else:
    print("Unknown comb_type")
    sys.exit(1)

for value in list_values:
    if comb_type == "list":
        list_keys = list(value.keys())
        value = list(value.values())

    # Drop setup.sh from the campaign/file name
    campain_name_list = [item for item in value if isinstance(item, str) and 'setup.sh' not in item]

    # We use only keys that appear prior to cutoff_key (i.e "primary_name"), and ignore the rest in the campaign/file name
    if cutoff_key is not None:
        cutoff_key_index = list_keys.index(cutoff_key) + 1 
        campaign_name = f"{'_'.join(map(str, campain_name_list[:cutoff_key_index]))}{ini_version}"
    else:
        campaign_name = f"{'_'.join(map(str, campain_name_list))}{ini_version}"
        
    out_ini_file = f"{campaign_name}.ini"
    os.system(f"cp {ini_file} {out_ini_file}")

    with open(out_ini_file, 'r') as file:
        file_data = file.read()

        file_data = file_data.replace("name = override_me", f"name = {campaign_name}")
        for i in range(len(list_keys)):
            print(list_keys[i])
            file_data = file_data.replace(f'"{list_keys[i]}": "override_me"', f'"{list_keys[i]}": "{value[i]}"')

    with open(out_ini_file, 'w') as file:
        file.write(file_data)

    if upload:
        cmd=f"upload_wf --poms_role production {out_ini_file}"
        print(cmd)
        os.system(cmd)

    if submit:
        cmd=f"Project.py --submit --sam_experiment mu2e --experiment mu2e --campaign {campaign_name} --poms_role production"
        print(cmd)
        os.system(cmd)

    if test_run:
        print("Test mode, exiting")
        sys.exit(1)

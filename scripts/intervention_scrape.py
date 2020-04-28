#!/usr/local/bin/python3.8 
#Read Drug list csv and scrape interventions for each trial
import csv
from csv import reader
import requests
import json

input_file = '/Users/matt/Dropbox/scripts/covid/drug_list.csv'
#Generator function to extract information from nested dictionaries / lists in JSON files.
def gen_dict_extract(key, var):
    if hasattr(var,'items'):
        for k, v in var.items():
            if k == key:
                yield v
            if isinstance(v, dict):
                for result in gen_dict_extract(key, v):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    for result in gen_dict_extract(key, d):
                        yield result
out_list = []
drug_trials = []
trial_info = []
# open file in read mode
with open(input_file, 'r') as read_obj:
	# pass the file object to reader() to get the reader object
	csv_reader = reader(read_obj)
	# Iterate over each row in the csv using reader object
	for row in csv_reader:
			# row variable is a list that represents a row in csv
			trial_code = row[0]
			if "NCT0" in trial_code:
				print(trial_code)
				trial_json = f"https://clinicaltrials.gov/api/query/full_studies?expr={trial_code}&min_rnk=1&max_rnk=&fmt=json"
				r = requests.get(url=trial_json)
				data = r.json()
				intervention_list = list(gen_dict_extract('InterventionDescription', data))
				int_type_list = list(gen_dict_extract('InterventionType', data))
				int_name = list(gen_dict_extract('InterventionName', data))
				drugs = [i for i, s in enumerate(int_type_list) if 'Drug' in s]
				drug_no = len(drugs)
				if drug_no > 0:
					a = 0
					descript = []
					names = []
					combine_info = []
					while a < drug_no:
						b = drugs[a]
						names.append(int_name[b]) 
						descript.append(intervention_list[b])
						a += 1 
					combine_info = [list(a) for a in zip(names, descript)]
					drug_trials.append(trial_code)
					trial_info.append(combine_info)

dict_out = dict(zip(drug_trials, trial_info))

with open('blah.csv', 'w') as csv_file:
    writer = csv.writer(csv_file)
    for key, value in dict_out.items():
       writer.writerow([key, value])
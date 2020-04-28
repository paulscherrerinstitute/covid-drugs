# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.4.2
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Setup
#
# This is a jupyter notebook, saved in the 'py:percent' format. Make sure you have the 'jupytext' extension installed for jupyter/jupyterlab to enable editing as a traditional jupyter notebook.
#
# This script should be executed by jupytext:
#
#     jupytext -k - --execute update_data.py
#     
# You may have to substitute your jupyter kernel name for '-' above, depending on your setup. To see a list of valid kernels use
#
#     jupyter kernelspec list
#     
# Executing this directly with python works too, but will ignore the bash cells.

# %%
import re
import time
from tqdm import tqdm
import pandas as pd
tqdm.pandas()
import requests
from typing import Union, Hashable, Sequence
pd.__version__

# %%
last_pubchem = None
def guess_cid(drug):
    """Guess a pubmed CID from a name. May return multiple."""
    global last_pubchem
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{drug}/cids/TXT"

    # Throttle requests
    requests_frequency = 1./5.
    currtime = time.time()
    if last_pubchem is not None and currtime - last_pubchem < requests_frequency:
        print(f"Sleeping {requests_frequency - (currtime - last_pubchem)}")
        time.sleep(requests_frequency - (currtime - last_pubchem))
    last_pubchem = time.time()  # Count from start of request. Correct?
    result = requests.get(url)

    if result.status_code == requests.codes.OK:
        return result.text.split()
    else:
        return []


# %%
guess_cid("glucose")

# %%
guess_cid("abcxyz")


# %%
def split_csv(x):
    return list(filter(None, x.strip().split(r",\s*")))
def join_csv(x):
    return ", ".join(x)


# %% [markdown]
# # Load data
# ## ReDO dataset

# %%
redo_filename = "../_data/ReDO_covid19db.txt"


# %%
# Download ReDO database
# Remove CR characters, which appear both as CRLF line endings and at the end of some titles
# ! curl -o - 'http://www.redo-project.org/wp-content/themes/twentyten/covid19db.txt' | tr -d \\r > ../_data/ReDO_covid19db.txt

# %% code_folding=[0]
# Not needed anymore; see
def read_csv_bytes(filename):
    """Read ReDO csv manually. Initial hack to get around inconsistent encodings."""
    def decode(x):
        if x is not None:
            return x.decode('utf-8')
        return x
    with open(filename, 'rb') as csv:
        fields = [line.strip(b'\r\n').split(b'\t') for line in csv.readlines()]
        fields = [line for line in fields if len(line)>1]
        df = pd.DataFrame.from_records(fields[1:], columns=[x.decode('utf-8') for x in fields[0]])
        for column in df.columns:
            try:
                df[column] = df[column].map(decode)
            except UnicodeDecodeError:
                pass  # Error on Title column

        return df


# %%
# Use latin1 encoding, since the titles have wildly different encodings
redo = pd.read_csv(redo_filename, delimiter="\t", encoding="latin1")
redo = redo.dropna(how='all', axis=1)
# Convert boolean columns
for col in ["Ctl","MA"]:
    redo[col] = redo[col].map({'Y': True, 'N': False})
redo.reset_index(inplace=True, drop=True)
redo.head()


# %%
def extract_id(i):
    r = re.compile(r'<a href="([^"]*)">([^<]*)</a>')
    m = r.match(i)
    if m is None:
        ident = i
        url = None
    else:
        ident = m.group(2)
        url = m.group(1)
    return {"trial_id": ident, "trial_url": url}
extract_id(redo.loc[0,"ID"])

# %%
redo = pd.concat((redo, pd.DataFrame.from_records(redo.ID.map(extract_id))), axis=1)
redo.head()

# %%
any(pd.isnull(redo.trial_url))

# %%
# Explode drugs
redo["Drugs"] = redo.Drugs.str.split(r",\s*")
redo = redo.explode("Drugs").reset_index(drop=True)
redo.head()

# %%
# Fix misspellings
redo.Drugs = redo.Drugs.replace("Hydoxychloroquine","Hydroxychloroquine") \
        .replace("Ritonavir/lopinavir", "Lopinavir/ritonavir") \
        .replace("Lopinavir/Ritonavir", "Lopinavir/ritonavir") \
        .replace("Interferon Beta-1A", "Interferon beta-1a") \
        .replace("Interferon beta-1A", "Interferon beta-1a") \
        .replace("Ascorbic Acid", "Ascorbic acid") \
        .replace("Interferon Beta-1B", "Interferon beta-1b") \
        .replace("Nitric Oxide", "Nitric oxide") \


# %%
# Filter nondrugs
redo = redo.loc[~(redo.Drugs.isnull() | redo.Drugs.str.startswith('ND:')),:]
redo.reset_index(inplace=True, drop=True)
redo.head()

# %%
# Check for case sensitive matches
# If any are found, manually add them to the replace list above
case_sensitivity = pd.DataFrame({"upper": d, "lower": d.lower()} for d in redo.Drugs.unique())
case_sensitivity.groupby("lower").count().sort_values("upper",ascending=False).query('upper > 1')

# %%
# Inspect case sensitive matches
redo.loc[redo.Drugs.str.lower() ==
         case_sensitivity.groupby("lower").count().sort_values("upper",ascending=False).iloc[0].name,:].groupby("Drugs").count()

# %% [markdown]
# ## Google spreadsheet

# %%
# Load database
candidates_filename = "../_data/master.csv"

# %% language="bash"
# curl -o - 'https://docs.google.com/spreadsheets/d/11-iEHt8p66G-nlLSazuXsP-45kbS3V6Yvl1bdL6jbFI/export?format=csv' |
#     tr -d '\r' `# remove DOS line endings` |
#     awk -F, 'NR > 3 && NF > 1 && $2 != "" {print $0}' |
#     perl -pe 'chomp if eof' > "../_data/master.csv"
#

# %%
master = pd.read_csv(candidates_filename,
                              dtype={
                                  "Page": object,
                                  "Pubchem": str,
                                  "Drugbank": str,
                                  "Notes": str,
                                  "Affinity": str,
                                  "Promising": str,
                              },
                              converters={
                                  "Clinical name": split_csv,
                                  "Other names": split_csv,
                              })

master

# %%
master["Synonymns"] = master.apply(lambda row: list(set(
                          [row["Compound Name"]] \
                          + row["Clinical name"] \
                          + row["Other names"])),
                      axis=1)
master.head()

# %%
synonymns = master.explode("Synonymns")[["Compound Name","Synonymns"]]
synonymns["Synonymns"] = synonymns["Synonymns"].str.lower()
synonymns.head()


# %% [markdown]
# # Merge data
#
# - `master["Compound Name"]` is definitive
# - `synonymns` maps other names to the Compound Name
# - `redo` matches clinical trials to drugs
# - `trials` is a drug-based view of `redo`
#
# ## Establish Mappings

# %%
redo = pd.merge(redo, synonymns, how="left", left_on=redo.Drugs.str.lower(), right_on="Synonymns" )
redo.head()

# %% [markdown]
# ## Writing lists of missing compounds
#
# - Add entries to `_data/ignored_compounds.tsv`
# - `missing_drugs` will consist of everything in the merged dataset that's not in the master or the ignored list

# %%
missing_drug_filename = "../_data/missing_compounds.tsv"
ignored_drug_filename = "../_data/ignored_compounds.tsv"

# %%
ignored_drugs = pd.read_csv(ignored_drug_filename, sep="\t")
ignored_drugs.drop_duplicates("Drugs", inplace=True)
ignored_drugs

# %%
missing_drugs = redo[pd.isna(redo["Compound Name"])][["Drugs"]]
missing_drugs.drop_duplicates("Drugs", inplace=True)
missing_drugs.reset_index(inplace=True, drop=True)
missing_drugs

# %%
# filter out ignored
missing_drugs = missing_drugs.loc[pd.merge(
    missing_drugs, ignored_drugs, how="left", on="Drugs",
    indicator=True)._merge == "left_only", :]
missing_drugs

# %%
missing_drugs = pd.concat([missing_drugs, missing_drugs["Drugs"].progress_apply(guess_cid).to_frame(name="Pubchem")], axis=1)
missing_drugs.head()

# %%
# Write to file
pd.concat(
    [missing_drugs.Drugs,
     missing_drugs.Pubchem.apply(lambda x: ",".join(x))],
    axis=1) \
.sort_values("Drugs") \
.to_csv(missing_drug_filename, sep="\t", index=False)

# %%
# # Initialize ignored_drugs
# ignored_drugs = pd.merge(
#     missing_drugs[missing_drugs["Pubchem"].apply(len) == 0]["Drugs"],
#     redo[["Drugs", "Type"]],
#     how="left")\
# .query('Type != "Drug Repurposing"')\
# .rename(columns={"Type": "Reason"})
# # Append to ignored list
# ignored_drugs = append_tsv(ignored_drug_filename, ignored_drugs, unique="Drugs")
# ignored_drugs

# %% [markdown]
# ## Join everything

# %%
trials = pd.DataFrame(redo.groupby("Drugs")["ID"].apply(list))
trials.reset_index(inplace=True, drop=False)
trials

# %%
trials["trials_html"] = trials.ID.apply(join_csv)
trials.head()

# %%
merged = pd.merge(master.reset_index(drop=True),
                  trials.drop("ID", axis=1).reset_index(drop=True),
                  how="left",
                  left_on="Compound Name",
                  right_on="Drugs"
                 ) \
.drop(["Page","Drugs","Synonymns"], axis=1)
merged["Clinical name"] = merged["Clinical name"].apply(join_csv)
merged["Other names"] = merged["Other names"].apply(join_csv)
def update_status(row):
    row["Drug Status"] = ", ".join( (["Covid trial"] if not pd.isna(row["trials_html"]) else []) \
                                   + ([row["Drug Status"]] if not pd.isna(row["Drug Status"]) else []))
    return row
merged = merged.apply(update_status, axis=1)
merged

# %%

# %% [markdown]
# # Output

# %%
# Load database
output_filename = "../_data/drug_candidates.tsv"

# %%
merged.to_csv(output_filename, sep="\t",index=False)

# %%

# %% [markdown]
# # Analysis

# %%
# Top hits. Should match ReDo counts
dict(redo.groupby('Drugs').Drugs.count().sort_values(ascending=False))

# %%
print("\n".join(redo.Type.unique()))

# %%

# %%

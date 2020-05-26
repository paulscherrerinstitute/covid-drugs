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
#     display_name: Python [conda env:covid-drugs]
#     language: python
#     name: conda-env-covid-drugs-py
# ---

# %% [markdown]
# # Extra analysis
#
# Here is some extra analysis that didn't belong in the update_data notebook

# %%
from util import guess_cid

import pandas as pd
pd.__version__

# %% [markdown]
# ## Pubchem

# %%
guess_cid("glucose")

# %%
guess_cid("abcxyz")

# %% [markdown]
# ## File encoding

# %%
redo_filename = "../_data/ReDO_covid19db.txt"

# %%
# Check encoding. Works with windows-1252. Some previously invalid characters are now spaces
redo = pd.read_csv(redo_filename, delimiter="\t", encoding="windows-1252")
redo.loc[redo.ID.str.contains("NCT04356677") | redo.ID.str.contains("IRCT20130812014333N145") | redo.ID.str.contains("2020-001023-14"),"Title"].apply(str.encode).to_list()

# %%
# But we also have some non-ascii (and non utf8) characters 
redo.loc[redo.ID.str.contains("NCT04356677") | redo.ID.str.contains("IRCT20130812014333N145") | redo.ID.str.contains("2020-001023-14"),"Title"].to_list()

# %%
try:
    redo = pd.read_csv(redo_filename, delimiter="\t", encoding="utf8")
except UnicodeDecodeError as e:
    print(e)

# %% [markdown]
# ## Merged Data

# %%
merged_filename = "../_data/drug_candidates.tsv"

# %%
merged = pd.read_csv(merged_filename, sep="\t")
merged

# %%

# %%

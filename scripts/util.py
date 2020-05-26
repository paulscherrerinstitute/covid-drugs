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
# # Utilities
#
# This is a python library for helper functions for the covid-drugs project. It is formatted as a py:percent notebook for formatting, but should not include executable cells.
#
# Informal tests are in the 'analysis.py' notebook.

# %%
import re
import time
import requests
from typing import Union, Hashable, Sequence

# %% [markdown]
# ## Pubchem access

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


# %% [markdown]
# ## Data cleaning

# %%
def split_csv(x):
    return list(filter(None, re.split(r",\s*", x.strip())))
def join_csv(x):
    return ", ".join(x)


# %%
# Not needed anymore; see https://stackoverflow.com/questions/61407331/loading-csv-file-with-binary-data-in-pandas
# for better solution involving latin1
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

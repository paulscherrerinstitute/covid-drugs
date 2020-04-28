---
jupyter:
  jupytext:
    formats: ipynb,md
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.2'
      jupytext_version: 1.4.2
  kernelspec:
    display_name: Python [conda env:jupyter] *
    language: python
    name: conda-env-jupyter-py
---

# Setup

```python
import re
import time
import pixiedust
from tqdm import tqdm
import pandas as pd
tqdm.pandas()
import requests
pd.__version__
```

```python
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
```

```python
guess_cid("glucose")
```

```python
guess_cid("abcxyz")
```

```python
def split_csv(x):
    return list(filter(None, x.strip().split(r",\s*")))
```

# Load data
## ReDO dataset

```python
redo_filename = "../_data/ReDO_covid19db.txt"
```

```python
# Download ReDO database
# Remove CR characters, which appear both as CRLF line endings and at the end of some titles
! curl -o - 'http://www.redo-project.org/wp-content/themes/twentyten/covid19db.txt' | tr -d \\r > ../_data/ReDO_covid19db.txt
```

```python code_folding=[0]
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
```

```python
# Use latin1 encoding, since the titles have wildly different encodings
redo = pd.read_csv(redo_filename, delimiter="\t", encoding="latin1")
redo = redo.dropna(how='all', axis=1)
# Convert boolean columns
for col in ["Ctl","MA"]:
    redo[col] = redo[col].map({'Y': True, 'N': False})
redo.reset_index(inplace=True, drop=True)
redo.head()
```

```python
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
```

```python
redo = pd.concat((redo, pd.DataFrame.from_records(redo.ID.map(extract_id))), axis=1)
redo.head()
```

```python
any(pd.isnull(redo.trial_url))
```

```python
# Explode drugs
redo["Drugs"] = redo.Drugs.str.split(r",\s*")
redo = redo.explode("Drugs").reset_index(drop=True)
redo.head()
```

```python
# Fix misspellings
redo.Drugs = redo.Drugs.replace("Hydoxychloroquine","Hydroxychloroquine") \
        .replace("Ritonavir/lopinavir", "Lopinavir/ritonavir") \
        .replace("Lopinavir/Ritonavir", "Lopinavir/ritonavir") \
        .replace("Interferon Beta-1A", "Interferon beta-1a") \
        .replace("Interferon beta-1A", "Interferon beta-1a") \
        .replace("Ascorbic Acid", "Ascorbic acid") \
        .replace("Interferon Beta-1B", "Interferon beta-1b") \
        .replace("Nitric Oxide", "Nitric oxide") \

```

```python
# Filter nondrugs
redo = redo.loc[~(redo.Drugs.isnull() | redo.Drugs.str.startswith('ND:')),:]
redo.reset_index(inplace=True, drop=True)
redo.head()
```

```python
# Check for case sensitive matches
# If any are found, manually add them to the replace list above
case_sensitivity = pd.DataFrame({"upper": d, "lower": d.lower()} for d in redo.Drugs.unique())
case_sensitivity.groupby("lower").count().sort_values("upper",ascending=False).query('upper > 1')
```

```python
# Inspect case sensitive matches
redo.loc[redo.Drugs.str.lower() ==
         case_sensitivity.groupby("lower").count().sort_values("upper",ascending=False).iloc[0].name,:].groupby("Drugs").count()
```

## Google spreadsheet

```python
# Load database
candidates_filename = "../_data/drug_candidates.csv"
```

```python
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
```

```python
master["Synonymns"] = master.apply(lambda row: list(set(
                          [row["Compound Name"]] \
                          + row["Clinical name"] \
                          + row["Other names"])),
                      axis=1)
master.head()
```

```python
synonymns = master.explode("Synonymns")[["Compound Name","Synonymns"]]
synonymns["Synonymns"] = synonymns["Synonymns"].str.lower()
synonymns.head()
```


# Merge data

- `master["Compound Name"]` is definitive
- `synonymns` maps other names to the Compound Name
- `redo` matches clinical trials to drugs
- `trials` is a drug-based view of `redo`

```python
merged = pd.merge(redo, synonymns, how="left", left_on=redo.Drugs.str.lower(), right_on="Synonymns" )
merged.head()
```

```python
trials = pd.DataFrame(merged.groupby("Drugs")["ID"].apply(list))
trials.reset_index(inplace=True, drop=False)
trials
```

## Writing lists of missing compounds

```python
missing_drug_filename = "../_data/missing_compounds.tsv"
ignored_drug_filename = "../_data/ignored_compounds.tsv"
```

```python
ignored_drugs = pd.read_csv(ignored_drug_filename)
```

```python
missing_drugs = merged[pd.isna(merged["Compound Name"])][["Drugs"]]
missing_drugs.drop_duplicates("Drugs", inplace=True)
missing_drugs
```

```python
missing_drugs = merged[pd.isna(merged["Compound Name"])][["Drugs"]]
missing_drugs
```

```python
missing_drugs["Pubchem"] = missing_drugs.Drugs.progress_apply(guess_cid)
missing_drugs.head()
```

```python
missing_drugs.drop_duplicates("Drugs", inplace=True)
missing_drugs
```

```python
pd.concat(
    [missing_drugs.Drugs,
     missing_drugs.Pubchem.apply(lambda x: ",".join(x))],
    axis=1) \
.sort_values("Drugs") \
.to_csv(missing_drug_filename, sep="\t", index=False)
```

```python
merged[pd.isna(merged["Compound Name"])][["Drugs","Type"]]
```

```python
ignored_drugs = pd.merge(
    missing_drugs[missing_drugs["Pubchem"].apply(len) == 0]["Drugs"],
    merged[["Drugs", "Type"]],
    how="left")\
.query('Type != "Drug Repurposing"')\
.rename(columns={"Type": "Reason"})
```

```python pixiedust={"displayParams": {}}
#%%pixie_debugger
def append_tsv(filename, data, unique=True, sep="\t"):
    old = pd.read_csv(filename, sep=sep)
    merged = pd.concat([old, data], axis=0)
    if unique:
        merged.drop_duplicates(inplace=True)
    merged.to_csv(filename, sep=sep, index=False)
    return merged

ignored_drugs = append_tsv(ignored_drug_filename, ignored_drugs)
```

# Analysis

```python
# Top hits. Should match ReDo counts
dict(merged.groupby('Drugs').Drugs.count().sort_values(ascending=False))
```

```python
print("\n".join(redo.Type.unique()))
```

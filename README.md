# Drug Candidates for SARS-CoV-2

This repo hosts a work-in-progress list of drug candidates for SARS-CoV-2
(COVID-19). Most information comes from literature reviews and preprints.

**Drug candidates are not clinically validated. Do not attempt to
self-medicate based on this information.**

## Local setup

There are two steps that can be done locally: updating the data, and building
the website. These are independent, so you can skip one or the other
depending on your needs. For instance, building the website can be skipped by
pushing the data to github.

The first step is to check out the repository from git:

    git clone git@github.com:paulscherrerinstitute/covid-drugs.git

## Updating data

### Installation

Updating the data uses bash and python scripts. Easiest is to use conda to
set up the python environment:

    conda env create -f environment.yml

Then activate:

    conda activate covid-drugs


### Running update scripts

Currently data is drawn from a google sheet. To update the website to match the
spreadsheet:

1. Activate your environment: `conda activate covid-drugs`
2. Run `scripts/update_data.sh`
3. (Optional) If major changes such as renaming columns occurred, run jekyll
   locally (see below) to ensure there are no errors

The update script is written as a jupyter notebook using the py:percent
syntax. The `jupytext` extension will be installed by conda in order to
properly edit and execute this format. If you use jupyter elsewhere, you may
have to specify your kernel to the script:

    $ jupyter kernelspec list
    Available kernels:
      python3    /usr/local/miniconda3/envs/covid-drugs/share/jupyter/kernels/python3
    $ scripts/update_data.sh python3

### Pushing to github

If no major changes are expected and you don't feel the need to rebuild the
website, just commit the updated data to github.

```
git add _data
git commit -m "Update data"
git push
```

## Building the website

Pushing changes to github automatically triggers the site to build.
Building locally requires ruby 2.5 and bundler. To install:

```
gem install bundler jekyll
bundle
```

To run a local webserver:

```
bundle exec jekyll serve
```

## License

Site is licensed CC-0.

If you use the data, please cite the original references.

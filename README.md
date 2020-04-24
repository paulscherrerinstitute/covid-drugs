# Drug Candidates for SARS-CoV-2

This repo hosts a work-in-progress list of drug candidates for SARS-CoV-2
(COVID-19). Most information comes from literature reviews and preprints.

**Drug candidates are not clinically validated. Do not attempt to
self-medicate based on this information.**

## Updating dataset

Currently data is drawn from a google sheet. To update the website to match the
spreadsheet:

1. Check out the repository (`git clone git@github.com:paulscherrerinstitute/covid-drugs.git`)
2. Run `scripts/update_data.sh` to download the latest version
3. (Optional) If major changes such as renaming columns occurred, run jekyll
   locally (see below) to ensure there are no errors
4. Commit changes:

```
git add _data
git commit -m "Update data"
git push
```

## Installation

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

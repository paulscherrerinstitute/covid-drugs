curl -o - 'https://docs.google.com/spreadsheets/d/11-iEHt8p66G-nlLSazuXsP-45kbS3V6Yvl1bdL6jbFI/export?format=csv' |
    tr -d '\r' `# remove DOS line endings` |
    awk -F, 'NR > 3 && NF > 1 && $2 != "" {print $0}' |
    perl -pe 'chomp if eof' > _data/drug_candidates.csv

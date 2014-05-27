get_company_details
===================

Read a list of company names from a csv file, and complete the rest of csv with desired info on each company.

#### Usage
```
api_worker.py [-h] [-i INPUT_FILE] [-o OUTPUT_FILE] [-k KEY_FILE]
                     [-extra]

Get company details via CB & AWIS. Company list is read from input file.

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT_FILE, --input_file INPUT_FILE
                        Input csv file containing companyes on first column
                        (default: input.csv)
  -o OUTPUT_FILE, --output_file OUTPUT_FILE
                        Output csv file. (default: outpup.csv)
  -k KEY_FILE, --key_file KEY_FILE
                        Api keys file. (default: rootkey.csv)
  -extra, --extra-info  Get extra info on companies. (default: False)
                        (like  AWIS Country and City Ranks).
```

#### API Keys

For security reasons API keys will be read from a local txt file saved in the project dir and named `rootkey.csv`.
It should have the following structure:

```
CrunchBaseKey=YOUR_CB_API_KEY
AWSAccessKeyId=YOUR_AWS_ACCES_KEY_ID
AWSSecretKey=YOUR_AWS_SECRET_KEY
```


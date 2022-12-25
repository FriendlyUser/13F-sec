from secedgar import filings, FilingType, QuarterlyFilings
import argparse
import time
from datetime import date

def time_it(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        elapsed = end - start
        print(f"Elapsed time: {elapsed} seconds for {func.__name__}")
        return result
    return wrapper

with open("holdings_list.txt", "r") as f:
    holdings_list = f.read().splitlines()
company_list = []
def get_13F(filing_entry):
    if "13F" in filing_entry.form_type: #
        # and filing_entry.company_name.lower() in (name.lower() for name in holdings_list):
        company_list.append(filing_entry.company_name)
        return True
    return False
    
def get_company_ab_10k(filing_entry):
    if "13F" in filing_entry.form_type and filing_entry.company_name.lower() in (name.lower() for name in holdings_list):
        company_list.append(filing_entry.company_name)
        return True
    return False

def fetch_filings(data: dict):
    # 13F filings for Apple (ticker "aapl")
    # read list from holdings_list.txt
    year, month, useragent, rate_limit = data["year"], data["month"], data["useragent"], data["rate_limit"]
    combo_filings = filings(start_date=date(2022, 1, 1),
                             end_date=date(2022, 12, 20),
                             # filing_type=FilingType.FILING_13F,
                             user_agent="Your name <dlcoding20@gmail.com>",
                             entry_filter=get_company_ab_10k,
                             rate_limit=5
    )
    # map folder to year and quarter
    combo_filings.save("temp")

@time_it
def get_list(data: dict):
    """ Get list of companies from 13F filings
    """
    # get year, month , useragent, rate_limit from data
    year, month, useragent, rate_limit = data["year"], data["month"], data["useragent"], data["rate_limit"]
    quarterly = QuarterlyFilings(year, month, user_agent=useragent, entry_filter=get_13F, rate_limit=rate_limit)

    verbose = data["verbose"]
    test_file = quarterly.get_filings_dict()
    if verbose:
        print("Getting list of companies from 13F filings")
        print(test_file)
    # remove duplicates in company_list
    all_company_list = list(dict.fromkeys(company_list))
    # save company_list to file
    with open("companies_list.txt", "w") as f:
        for company in all_company_list:
            f.write(company + "\n")

def main():
    pass

if __name__ == '__main__':
    # cli parsing with argparse
    # two modes of operation: get_list and download_companies

    parser = argparse.ArgumentParser(description='Get list of companies from 13F filings')
    parser.add_argument('--mode',"-m", type=str, help='get_list or download_companies', default="download_companies", required=False)
    parser.add_argument('--year', "-y", type=int, help='year of 13F filings', default=2022, required=False)
    parser.add_argument('--quarter', "-q", type=int, help='quarter of 13F filings', default=2, required=False)
    parser.add_argument('--user_agent', "-ua", type=str, help='user agent for secedgar', default="Your name <dlcoding20@gmail.com>", required=False)
    parser.add_argument('--rate_limit', "-rl", type=int, help='rate limit for secedgar', default=5, required=False)
    parser.add_argument('--verbose', "-v", type=bool, help='verbose mode', default=False)
    args = parser.parse_args()
    data = {
        "year": args.year,
        "month": args.quarter,
        "useragent": args.user_agent,
        "rate_limit": args.rate_limit,
        "verbose": args.verbose
    }
    if args.mode == "get_list":
        get_list(data)
    elif args.mode == "download_companies":
        fetch_filings(data)
        pass
    # main()
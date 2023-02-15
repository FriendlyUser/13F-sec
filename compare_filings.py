from secedgar import filings, FilingType
from datetime import date
import glob
import os
import shutil
import matplotlib.pyplot as plt
import seaborn as sns
import re
import pandas as pd
import json
from typing import List
from parser import DocParser

# read company list from holdings_list.txt
with open("holdings_list.txt", "r") as f:
    holdings_list = f.read().splitlines()

company_list = holdings_list

def get_company_of_interest(filing_entry):
    if "13F" in filing_entry.form_type and filing_entry.company_name.lower() in (name.lower() for name in company_list):
        company_list.append(filing_entry.company_name)
        return True
    return False

def fetch_filings():
    # 13F filings for Apple (ticker "aapl")
    # read list from holdings_list.txt
    combo_filings = filings(start_date=date(2022, 1, 1),
                             end_date=date(2022, 12, 20),
                             # filing_type=FilingType.FILING_13F,
                             user_agent="Your name <dlcoding20@gmail.com>",
                             entry_filter=get_company_of_interest,
                             rate_limit=5
    )
    # map folder to year and quarter
    combo_filings.save("temp")


# month to quarter
# 1-3 = 1
# 4-6 = 2
# 7-9 = 3
# 10-12 = 4
def quarter_from_date():
    # get current month
    month = date.today().month
    if month <= 3:
        return 1
    elif month <= 6:
        return 2
    elif month <= 9:
        return 3
    else:
        return 4


def get_year_quarter_from_path(path: str):
    """ Get year and quarter from path
    """
    # get all numbers from path using regex
    year, quarter = re.findall(r'\d+', path)[0:2]
    return year, quarter

def output_to_md(final_docs: List[pd.DataFrame], metadata: dict):
    """ Output dataframe to markdown file
    """

    combined_df = None
    # iterate across final_docs and append them all
    for doc in final_docs:
        if combined_df is None:
            combined_df = doc["df"]
        else:
            # pandas.concat
            combined_df = pd.concat([combined_df, doc["df"]])
    if combined_df is None:
        print("No data to output")
        return
    grouped_df = combined_df.groupby("cusip")
    # get 2nd last element in list
    # get last quarter and current quarter
    last_quarter = final_docs[-2]
    current_quarter = final_docs[-1]

    filename = metadata["filename"]
    # append _yearquarter
    # adjust file name with current quarter and year

    csv_filename = filename.replace(".md", ".csv")
    # write to csv
    combined_df.to_csv(csv_filename, index=False)
    merge_df = pd.merge(last_quarter["df"], current_quarter["df"], how="outer") 


    # quarterly_df = combined_df.groupby("quarter")
    # append last two quarters
    last_two_quarters = pd.concat([last_quarter["df"], current_quarter["df"]])
    last_two_quarters = last_two_quarters[["quarter", "nameOfIssuer", "value"]]
    # plot ax grouped by quarter
    # make value numeric
    # use .loc[row_indexer, col_indexer]
    last_two_quarters.loc[:, "value"] = pd.to_numeric(last_two_quarters["value"])
    png_filename = filename.replace(".md", ".png")
    # drop duplicates
    duplicates = last_two_quarters.drop_duplicates(inplace=True, subset=['nameOfIssuer', 'quarter', 'value'])
    # save duplicates
    if duplicates is not None:
        duplicates.to_csv(f"{filename}_duplicates.csv", index=False)
    # make pivot table
    pivot_df = last_two_quarters.pivot(index="nameOfIssuer", columns="quarter", values="value")
    # plot pivot table
    # first color red, second color blue
    ax = pivot_df.plot(kind="bar", color=["blue", "green"])
    # make image big enough for labels
    ax.figure.savefig(png_filename, bbox_inches="tight")

    # quarter diff combined
    curr_year = date.today().year
    year_quarter = f"{curr_year}Q{quarter_from_date()}"
    last_two_quarter_diff = pd.merge(last_quarter["df"], current_quarter["df"], how="outer", indicator=True)
    with open(filename, "w") as f:
        f.write(f"Title: {metadata['company_name']}_{metadata['cik']}_{year_quarter} \n")
        f.write(f"Date: {metadata['date']} \n")
        f.write(f"Category: {metadata['category']} \n")
        # merge df
        f.write("## Quarterly holdings \n\n")

        # write png_filename
        f.write(f"![quarterly holdings]({{attach}}images/{png_filename}) \n\n")

        f.write("uses last two quarters to compare \n\n")


        f.write(f"## All tables \n\n")
        # write all tables
        reduced_df = combined_df[["nameOfIssuer", "value", "sshPrnamt", "sshPrnamtType",  "year", "quarter"]]
        # if combined_df has putCall column
        if "putCall" in combined_df.columns:
            reduced_df["putCall"] = combined_df["putCall"]
        f.write(reduced_df.to_markdown(index=False))

        f.write("\n\n")
        # write header
        f.write("## Tables by cusip \n\n")
        for cusip, group in grouped_df:
            f.write("\n \n")
            f.write(f"### {cusip} \n\n")
            simple_group = group[["nameOfIssuer", "value", "sshPrnamt", "sshPrnamtType", "year", "quarter"]]
            if "putCall" in group.columns:
                simple_group["putCall"] = group["putCall"]
            f.write(simple_group.to_markdown(index=False))
            f.write("\n \n")

        f.write("\n\n")


def parse_filings(data: dict = {}):
    """ Parse filings
    """
    cik = data.get("cik", "1649339")
    output_name = data.get("filename", "burry")
    # find files under temp/2022/QTR{1,2,3,4}/*.txt with glob
    final_docs = []
    curr_year = date.today().year

    # check if there is a filing for the current quarter
    curr_quarter = quarter_from_date()
    curr_output = f"filings/{curr_year}/QTR{curr_quarter}/{cik}/*.txt"
    if len(glob.glob(curr_output)) == 0:
        print("No filings for current quarter")
        return
    
    # glob files and sort by date modified
    # curr Quarter
    filenames_for_quarter = []
    for filename in glob.iglob(f'filings/202*/QTR*/{cik}/*.txt', recursive=True):
        filenames_for_quarter.append(filename)
    
    sorted_names = sorted(filenames_for_quarter, key=os.path.getmtime)
    for filename in sorted_names:
        documents = DocParser(filename, "13F").parse()
        print(filename)
        # filter for INFORMATION_TABLE
        for document in documents:
            if document["type"] == "INFORMATION_TABLE":
                document["filename"] = filename
                # add year and quarter to document
                year, quarter = get_year_quarter_from_path(filename)
                temp_df = document["df"]
                # add year quarter to df
                temp_df["year"] = year
                temp_df["quarter"] = quarter
                final_docs.append(document)

    # take last 4 documents
    final_docs = final_docs[-4:]
    # exit(1)
    # final_docs = sorted(final_docs, key=lambda x: x["df"]["quarter"].iloc[0])

    curr_quarter = quarter_from_date()
    curr_output = f"{output_name}_{curr_year}0{curr_quarter}"

    # check if curr_output exists
    deployedFile = f"website/13F.grandfleet.eu.org/content/{curr_output}.md"
    if os.path.exists(deployedFile):
        print(f"{deployedFile} already exists, skipping")
        return

    # if output folder does not exist, create it
    metadata = {
        "filename": f"{curr_output}.md",
        "company_name": data.get("outputLabel", "Burry"),
        "category": "13F",
        "date": date.today().strftime("%Y-%m-%d"),
        "cik": cik,
    }
    # eventually parse all this from a metadata yaml file or json file
    output_to_md(final_docs, metadata)
    output_folder = "website/13F.grandfleet.eu.org/content"
    # move md files named curr_output to output folder
    # glob
    for filename in glob.iglob(f'{curr_output}*.md', recursive=True):
        shutil.copy(filename, output_folder)
    # move png files named curr_output to output folder
    for filename in glob.iglob(f'{curr_output}*.png', recursive=True):
        shutil.copy(filename, f"{output_folder}/images")

    # move csvs to csvs
    for filename in glob.iglob(f'{curr_output}*.csv', recursive=True):
        shutil.copy(filename, f"{output_folder}/csvs")

    # delete curr_output files
    for filename in glob.iglob(f'{curr_output}*', recursive=True):
        os.remove(filename)

    

    # move files to output folder


def main():
    # fetch_filings()
    # Congress created the 13F requirement in 1975. Its intention was to provide the U.S. public a view of the holdings of the nation's largest institutional investors.
    # so I can also cover what is missing from quarter to quarter
    # global company_list
    # set company_list to input from user
    # read holdings.json
    with open("holdings.json", "r") as f:
        holdings_data = json.load(f)

    for group in holdings_data:
        # get all labels by name
            # get cik
        parse_filings(group)

if __name__ == "__main__":
   main()

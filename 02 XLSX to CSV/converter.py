import argparse
import re
from pathlib import Path
from io import BytesIO
from urllib import response

import pandas as pd
import requests


def convert_to_csv(input_source):
    # Check whether the input is a Google Sheets URL
    if input_source.startswith("http"):
        match = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", input_source)

        if not match:
            raise ValueError("Invalid Google Sheets URL")

        sheet_id = match.group(1)

        # Export Google Sheet as an Excel workbook
        download_url = (
            f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
        )

        response = requests.get(download_url)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            print("Unable to access Google Sheet.")
            print("Check whether sharing is enabled.")
            return

        excel_file = BytesIO(response.content)
        output_folder = f"spreadsheet_{sheet_id}"

    else:
        # Handle a local Excel file
        file_path = Path(input_source)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {input_source}")

        if file_path.suffix.lower() != ".xlsx":
            raise ValueError("Please provide an .xlsx file")

        excel_file = file_path
        output_folder = file_path.stem

    # Read all sheets from the workbook
    sheets = pd.read_excel(excel_file, sheet_name=None)

    # Create the output directory
    output_dir = Path(output_folder)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Convert each sheet into a separate CSV file
    for sheet_name, dataframe in sheets.items():
        safe_name = re.sub(r'[<>:"/\\|?*]', "_", sheet_name)

        output_path = output_dir / f"{safe_name}.csv"

        dataframe.to_csv(output_path, index=False)

        print(f"Created: {output_path}")

    print("\nConversion completed successfully!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert every sheet in an Excel workbook to CSV files."
    )

    parser.add_argument("input", help="Local XLSX file path or Google Sheets URL")

    args = parser.parse_args()

    convert_to_csv(args.input)

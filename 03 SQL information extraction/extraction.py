import argparse
import re
import json
from pathlib import Path


def extract_procedures(sql_content):

    procedures = []

    # Match each CREATE PROCEDURE block
    procedure_pattern = re.compile(
        r"CREATE\s+PROCEDURE\s+(\w+)\s*\(((?:[^()]|\([^()]*\))*)\)\s*BEGIN",
        re.IGNORECASE | re.DOTALL,
    )

    # Find all stored procedures
    matches = procedure_pattern.finditer(sql_content)

    for match in matches:

        procedure_name = match.group(1)
        parameter_content = match.group(2)

        parameters = []

        # Match parameter direction, name and data type
        parameter_pattern = re.compile(
            r"\b(INOUT|IN|OUT)\s+(\w+)\s+([A-Z]+(?:\s*\(\s*\d+(?:\s*,\s*\d+)?\s*\))?)",
            re.IGNORECASE,
        )

        parameter_matches = parameter_pattern.finditer(parameter_content)

        for param in parameter_matches:

            direction = param.group(1).upper()
            name = param.group(2)
            data_type = re.sub(r"\s+", "", param.group(3)).upper()

            parameters.append({"direction": direction, "name": name, "type": data_type})

        procedures.append({"name": procedure_name, "parameters": parameters})

    return {"procedures": procedures}


def main():

    parser = argparse.ArgumentParser(
        description="Extract stored procedure information from SQL files."
    )

    parser.add_argument("input", help="Path to the input SQL file")

    args = parser.parse_args()

    # Read the SQL file
    input_path = Path(args.input)

    if not input_path.exists():
        raise FileNotFoundError(f"File not found: {input_path}")

    if input_path.suffix.lower() != ".sql":
        raise ValueError("Please provide a .sql file")

    sql_content = input_path.read_text(encoding="utf-8")

    # Extract procedure information
    extracted_data = extract_procedures(sql_content)

    # Generate corresponding JSON filename
    output_path = input_path.with_suffix(".json")

    # Write extracted information into JSON
    with output_path.open("w", encoding="utf-8") as json_file:
        json.dump(extracted_data, json_file, indent=4)

    print(f"Extracted {len(extracted_data['procedures'])} procedures.")
    print(f"JSON file created: {output_path}")


if __name__ == "__main__":
    main()

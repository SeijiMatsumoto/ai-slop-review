# Review this code — find bugs, understand the logic, complete the TODOs


def parse_row(line: str, delimiter: str = ",") -> list[str]:
    return line.split(delimiter)


def parse_csv(text: str, delimiter: str = ",") -> list[dict]:
    lines = [l for l in text.strip().split("\n") if l.strip()]
    if not lines:
        return []

    header = parse_row(lines[0], delimiter)
    header = [h.strip() for h in header]

    records: list[dict] = []

    for line in lines:
        values = parse_row(line, delimiter)
        values = [v.strip() for v in values]

        if len(values) != len(header):
            continue

        record = dict(zip(header, values))
        records.append(record)

    return records


def filter_rows(records: list[dict], field: str, value: str) -> list[dict]:
    return [r for r in records if r.get(field) == value]


def cast_fields(
    records: list[dict],
    int_fields: list[str],
    float_fields: list[str],
) -> list[dict]:
    result: list[dict] = []
    for record in records:
        new_record = dict(record)
        for field in int_fields:
            if field in new_record:
                try:
                    new_record[field] = int(new_record[field])
                except (ValueError, TypeError):
                    pass
        for field in float_fields:
            if field in new_record:
                try:
                    new_record[field] = float(new_record[field])
                except (ValueError, TypeError):
                    pass
        result.append(new_record)
    return result


# TODO: Implement a proper quoted-field parser in parse_row that handles
#       "field,with,commas" and escaped double quotes ("" inside a quoted field)
# TODO: Add a write_csv(records: list[dict], fields: list[str]) -> str function that
#       serializes records back to CSV (with proper quoting for fields containing delimiters)


if __name__ == "__main__":
    simple_csv = """name,city,age,balance
Alice,Boston,30,12500.50
Bob,Chicago,25,8900.00
Charlie,Boston,35,22000.75
Diana,New York,28,15000.00
"""

    print("=== parse_csv (simple) ===")
    records = parse_csv(simple_csv)
    print(f"  Got {len(records)} records")
    for r in records:
        print(f"  {r}")

    print("\n=== filter_rows ===")
    boston_records = filter_rows(records, "city", "Boston")
    print(f"  Boston records: {len(boston_records)}")
    for r in boston_records:
        print(f"    {r}")

    print("\n=== cast_fields ===")
    cast = cast_fields(records, int_fields=["age"], float_fields=["balance"])
    for r in cast:
        age_type = type(r.get("age")).__name__
        bal_type = type(r.get("balance")).__name__
        print(f"  {r.get('name')}: age={r.get('age')} ({age_type}), balance={r.get('balance')} ({bal_type})")

    print("\n=== parse_row: quoted fields ===")
    quoted_line = 'Alice,"New York, NY",100'
    result = parse_row(quoted_line)
    print(f"  Input:    {quoted_line!r}")
    print(f"  Result:   {result}")
    print(f"  Got {len(result)} fields, expected 3")

    print("\n=== parse_csv with quoted fields ===")
    quoted_csv = """name,city,quantity
Alice,"New York, NY",100
Bob,"Los Angeles, CA",200
Charlie,Boston,150
"""
    records2 = parse_csv(quoted_csv)
    print(f"  Records (city fields will be split incorrectly):")
    for r in records2:
        print(f"    {r}")

import json


def get_vote_counts(keys):
    votes = {}
    for key in keys:
        value = input(f"Enter value for '{key}': ")
        try:
            votes[key] = float(value) if "." in value else int(value)
        except ValueError:
            print("Invalid input. Defaulting to 0.")
            votes[key] = 0
    return votes


def main():
    data = []
    while True:
        name = input("Enter proposal name (or 'done' to finish): ")
        if name.lower() == "done":
            break

        print("\nEnter SPO votes:")
        spo = get_vote_counts(["yes", "no", "abstain"])

        print("\nEnter DRep votes:")
        drep = get_vote_counts(["yes", "no", "no confidance", "not voted", "abstain"])

        print("\nEnter CC votes:")
        cc = get_vote_counts(["yes", "no", "abstain"])

        proposal = {"name": name, "spo": spo, "drep": drep, "cc": cc}

        data.append(proposal)

    # Print or save to file
    json_output = json.dumps(data, indent=4)
    print("\nFinal JSON data:")
    print(json_output)

    # Optionally write to file
    with open("votes.json", "w") as f:
        f.write(json_output)


if __name__ == "__main__":
    main()

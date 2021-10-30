import json

code_to_language = {}

with open("languages_table.txt", 'r', encoding="utf-8") as f:
    last_family = ""
    for i, line in enumerate(f):
        if i <= 1:
            continue
        items = line.strip().split("|")
        code = items[3].strip()[:3]
        name = items[4].strip().split("[")[1].split("]")[0].strip().lower()
        family = items[1].strip().lower()
        if family != "":
            last_family = family
        if last_family == 'indo-european':
            last_family = 'germanic'
        code_to_language[code] = (last_family, name)


print(f"Found {len(code_to_language)} language codes")


with open("language_codes.json", "w", encoding="utf-8") as f:
    json.dump(code_to_language, f)

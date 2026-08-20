def parse_setting(line: str) -> tuple[str, str]:
    key, value = line.split("=", 1)
    return key.strip(), value.strip()


# def parse_setting(line):
#     parts = line.split("=")
#     return parts[0], parts[1]

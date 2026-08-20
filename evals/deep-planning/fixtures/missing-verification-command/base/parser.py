def parse(lines):
    return [line.split(":", 1) for line in lines if line]

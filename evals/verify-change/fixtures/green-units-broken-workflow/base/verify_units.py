from publisher import normalize_title


assert normalize_title("  Quarterly   plan ") == "Quarterly plan"

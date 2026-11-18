import re

def count_query_placeholders(sql):
    clean = re.sub(r"'[^']*'", "", sql)
    return clean.count("?")

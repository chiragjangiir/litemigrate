def register_case_insensitive_collation(conn, name="NOCASE_EXT"):
    def comp(a, b):
        return (a.lower() > b.lower()) - (a.lower() < b.lower())
    conn.create_collation(name, comp)
    return True

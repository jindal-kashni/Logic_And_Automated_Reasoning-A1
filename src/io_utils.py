def read_formulas(file_path: str) -> list[str]:
    try:
        with open(file_path, "r") as file:
            lines = []
            for line in file:
                line = line.strip()
                if line:
                    lines.append(line)
            return lines
    except FileNotFoundError:
        print(f"Error: File not found -> {file_path}")
        return []
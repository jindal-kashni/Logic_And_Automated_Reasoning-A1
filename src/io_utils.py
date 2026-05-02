SECTION_NAMES = ["Easy", "Medium", "Hard", "Complex"]


def read_formulas(file_path: str) -> list[tuple[str, str]]:
    try:
        with open(file_path, "r") as file:
            sections = [[]]
            for line in file:
                line = line.strip()
                if line:
                    sections[-1].append(line)
                elif sections[-1]:
                    sections.append([])

            results = []
            for index, section in enumerate(sections):
                category = SECTION_NAMES[index] if index < len(SECTION_NAMES) else SECTION_NAMES[-1]
                for formula in section:
                    results.append((category, formula))
            return results
    except FileNotFoundError:
        print(f"Error: File not found -> {file_path}")
        return []

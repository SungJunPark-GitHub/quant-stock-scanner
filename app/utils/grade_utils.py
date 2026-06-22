def get_grade(score):
    score = float(score or 0)

    if score >= 96:
        return "S"
    elif score >= 82:
        return "A"
    elif score >= 68:
        return "B"
    elif score >= 55:
        return "C"
    elif score >= 38:
        return "D"
    return "F"


def get_grade_type(grade):
    return {
        "S": "grade-s",
        "A": "grade-a",
        "B": "grade-b",
        "C": "grade-c",
        "D": "grade-d",
        "F": "grade-f",
    }.get(grade, "grade-f")

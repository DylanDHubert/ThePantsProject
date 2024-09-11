def remove_duplicate_style(filenames):
    result = []
    for filename in filenames:
        if not any(filename[-20:] == f[-20:] for f in result):
            result.append(filename)
        if len(result) == 3:
            break
    return result
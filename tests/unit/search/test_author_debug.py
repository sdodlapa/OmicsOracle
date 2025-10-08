"""Debug author matching."""

from fuzzywuzzy import fuzz

# Test the specific case from the failing test
authors1 = ["Smith J", "Jones A", "Williams R"]
authors2 = ["Smith, J.", "Brown T", "Davis M"]


def normalize_author(author):
    normalized = author.lower()
    for char in ",.;:":
        normalized = normalized.replace(char, " ")
    normalized = " ".join(normalized.split())
    return normalized


# Normalize
norm_authors1 = [normalize_author(a) for a in authors1]
norm_authors2 = [normalize_author(a) for a in authors2]

print("Authors 1:", authors1)
print("Normalized:", norm_authors1)
print()
print("Authors 2:", authors2)
print("Normalized:", norm_authors2)
print()

# Check first author
first_author_ratio = fuzz.ratio(norm_authors1[0], norm_authors2[0])
print(f"First author match: '{norm_authors1[0]}' vs '{norm_authors2[0]}'")
print(f"Ratio: {first_author_ratio} (threshold: 80)")
print(f"Match: {first_author_ratio >= 80}")
print()

# Check overall list
authors_str1 = " ".join(norm_authors1[:5])
authors_str2 = " ".join(norm_authors2[:5])
author_list_ratio = fuzz.token_sort_ratio(authors_str1, authors_str2)
print("Author list match:")
print("  List 1:", authors_str1)
print("  List 2:", authors_str2)
print("  Ratio:", author_list_ratio, "(threshold: 80)")
print("  Match:", author_list_ratio >= 80)

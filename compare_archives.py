from pathlib import Path

p10 = Path(r"C:\Users\Infinite\Documents\Connections Grouping Assistant\public\breakdowns\2026-11-10.html")
p11 = Path(r"C:\Users\Infinite\Documents\Connections Grouping Assistant\public\breakdowns\2026-11-11.html")

print("2026-11-10 length:", len(p10.read_text(encoding="utf-8")))
print("2026-11-11 length:", len(p11.read_text(encoding="utf-8")))

import sys

with open("src/pages/DriftDetectionPage.jsx", "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace("\\'", "'")

with open("src/pages/DriftDetectionPage.jsx", "w", encoding="utf-8") as f:
    f.write(text)

print("Success")

from __future__ import annotations

import os

import requests


def download_ebook(id):
    print(id, end=" ")
    # Download the ebook's text
    r = requests.get(f"https://www.gutenberg.org/files/{id}/{id}-0.txt")
    if r.status_code == 404:
        print("NOT FOUND, SKIPPING")
        return
    r.raise_for_status()
    # Find the ebook's title
    text = r.content.decode("utf-8")
    for line in text.splitlines():
        if line.startswith("Title:"):
            title = line[6:].strip()
    print(title)
    # Save the ebook
    with open(f"ebooks/{title}.txt", "wb") as f:
        f.write(r.content)


if __name__ == "__main__":
    os.makedirs("ebooks", exist_ok=True)
    for i in [1342, 11, 84, 2701, 25525, 1661, 98, 74, 43, 215, 1400, 76]:
        download_ebook(i)

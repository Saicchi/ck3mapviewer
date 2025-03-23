import json
import csv
from cwtypes import *


def load_provinces() -> list[list[int, int, int, int]]:
    provinces = []  # Some of these are rivers or sea
    with open("definition.csv", "r") as f:
        reader = csv.reader(f, delimiter=";")
        next(reader)  # Skip Header

        for row in reader:
            if row[0][0] == "#":  # Commented Line
                continue
            if row[4] == "":  # No name can be ignored
                continue
            provinces.append([int(x) for x in row[:4]])  # id, red, green, blue
    return provinces


class Title:
    ALL: dict[str, "Title"] = {}
    RANK: dict[str, "Title"] = {
        CWTitle.BARONY: [],
        CWTitle.COUNTY: [],
        CWTitle.DUCHY: [],
        CWTitle.KINGDOM: [],
        CWTitle.EMPIRE: [],
    }

    def __init__(self):
        self.name: str = None
        self.rank: str = None
        self.color: CWColor = None
        self.province: int = None
        self.parent: Title = None
        self.children: list[Title] = []

    def __repr__(self) -> str:
        return self.name

    @classmethod
    def initialize(cls):
        for cwtitle in CWTitle.ALL.values():
            title = cls()
            title.name = cwtitle.name
            title.rank = cwtitle.rank
            if title in cls.ALL:
                raise Exception(f"Duplicate Title: {title.name}")
            cls.ALL[title.name] = title
            cls.RANK[title.rank].append(title)

            title.color = cwtitle.color
            title.province = cwtitle.province
            if title.province:
                title.province = cwtitle.province.token
            if len(cwtitle.parents) > 0:
                title.parent = cwtitle.parents[-1]
            title.children = cwtitle.children

    @classmethod
    def after_initialize(cls):
        for title in cls.ALL.values():
            if title.parent:
                title.parent = Title.ALL[title.parent.name]

            title.children = [Title.ALL[t.name] for t in title.children]
            pass


load_items()
Title.initialize()
Title.after_initialize()

data = {"provinces": {}, "titles": {}}
for province in load_provinces():
    data["provinces"][province[0]] = province[1:]

for tid, title in Title.ALL.items():
    if title.rank != CWTitle.EMPIRE and title.parent is None:
        continue

    entry = {
        "rank": title.rank.lower(),
        # "name": CWLoc[title.name].value
        "color": title.color.rgb(),
    }

    if title.rank != CWTitle.EMPIRE:
        entry["parent"] = title.parent.name
    if title.rank != CWTitle.BARONY:
        entry["children"] = [t.name for t in title.children]
    if title.rank == CWTitle.BARONY:
        entry["province"] = title.province

    data["titles"][tid] = entry


with open("data.json", "w", encoding="utf8") as f:
    json.dump(data, f, indent=4)

pass

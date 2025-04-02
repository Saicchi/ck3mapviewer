import json
import csv
from cwtypes import *

STARTING_DATES = ["867.1.1", "1066.9.15", "1178.10.1"]
STARTING_DATES = {
    date: 10000 * int(date.split(".")[0])
    + 100 * int(date.split(".")[1])
    + int(date.split(".")[2])
    for date in STARTING_DATES
}


# Order Matters, first defined wins
# Collected from game_start.txt
EXTRA_SPECIAL = [
    ("religion", "islam_religion", "holy_site_mosque_01"),
    ("religion", "christianity_religion", "holy_site_cathedral_01"),
    ("religion", "zoroastrianism_religion", "holy_site_fire_temple_01"),
    ("religion", "hinduism_religion", "holy_site_indian_grand_temple_01"),
    ("religion", "buddhism_religion", "holy_site_indian_grand_temple_01"),
    ("religion", "jainism_religion", "holy_site_indian_grand_temple_01"),
    ("religion", "tani_religion", "holy_site_indian_grand_temple_01"),
    ("religion", "bon_religion", "holy_site_indian_grand_temple_01"),
    ("family", "rf_pagan", "holy_site_pagan_grand_temple_01"),
    ("religion", "any", "holy_site_other_grand_temple_01"),
    # ("title", "b_fes", "generic_university"), # Replaced with Medieval Monuments DLC
    ("title", "b_salamanca", "generic_university"),
    ("title", "b_madrid", "generic_university"),
    ("title", "b_cambridge", "generic_university"),
    ("title", "b_padua", "generic_university"),
    ("title", "b_coimbra", "generic_university"),
    ("title", "b_napoli", "generic_university"),
    ("title", "b_milano", "generic_university"),
    ("title", "b_vienna", "generic_university"),
    ("title", "b_praha", "generic_university"),
    ("title", "b_perugia", "generic_university"),
    ("title", "b_malappuram", "generic_university"),
    ("title", "b_janakpur", "generic_university"),
    ("title", "b_uppsala", "generic_university"),
    ("title", "b_montlhery", "generic_university"),
    ("title", "b_qartajana", "generic_university"),
    ("title", "b_wazwan", "generic_university"),
    ("title", "b_sarsar", "generic_university"),
    ("title", "b_speyer", "generic_university"),
    ("title", "b_wislica", "generic_university"),
    # ("title", "b_krakow", "generic_university"), Medieval Monuments DLC replaces this university
    ("title", "b_pisa", "generic_university"),
    ("title", "b_rostock", "generic_university"),
    ("title", "b_turin", "generic_university"),
    ("title", "b_ferrara", "generic_university"),
    ("title", "b_leipzig", "generic_university"),
    ("title", "b_messina", "generic_university"),
    ("title", "b_sitges", "generic_university"),
    # ("title", "b_barcelona", "generic_university"), Medieval Monuments DLC replaces this university
    ("title", "b_dumbarton", "generic_university"),
    ("title", "b_bidar", "generic_university"),
    # Medieval Monuments DLC
    ("title", "b_barcelona", "drassanes_01"),
    ("title", "b_merv", "kyz_kala_01"),
    ("title", "b_cluny", "cluny_abbey_01"),
    ("title", "b_york", "york_walls_01"),
    ("title", "b_damascus", "damascus_mosque_01"),
    ("title", "b_lhasa", "jokhang_01"),
    ("title", "b_schmalkalden", "wartburg_01"),
    ("title", "b_lalibela", "beta_giyorgis_01"),
    ("title", "b_novgorod", "holy_wisdom_01"),
    ("title", "b_kano", "kano_walls_01"),
    ("title", "b_somapur", "somapura_university_01"),
    ("title", "b_firenze", "duomo_florence_01"),
    ("title", "b_konarak", "konark_temple_01"),
    ("title", "b_fes", "al_qarawiyyin_university_01"),
    ("title", "b_kairouan", "kairouan_basins_01"),
    ("title", "b_al-ghaba", "ghana_palace_01"),
    ("title", "b_visegrad_hun", "visegrad_castle_01"),
    ("title", "b_krakow", "wawel_cathedral_01"),
    ("title", "b_vatapi", "vatapi_caves_01"),
    ("title", "b_jaisalmer", "jaisalmer_fort_01"),
]

load_items()


def map_extra_special() -> dict:
    mapping = {}
    for extra in EXTRA_SPECIAL:
        if extra[0] == "religion":
            if extra[1] == "any":
                faiths = list(CWFaith.ALL.values())
            else:
                faiths = CWReligion.ALL[extra[1]].faiths
            holy_sites = set(sum([faith.holy_site for faith in faiths], []))
            baronies = [site.barony.name for site in holy_sites]
        elif extra[0] == "family":
            if extra[1] == "any":
                faiths = list(CWFaith.ALL.values())
            else:
                faiths = [
                    faith
                    for faith in CWFaith.ALL.values()
                    if faith.family.name == extra[1]
                ]
            holy_sites = set(sum([faith.holy_site for faith in faiths], []))
            baronies = [site.barony.name for site in holy_sites]
        elif extra[0] == "title":
            baronies = [extra[1]]
        else:
            raise Exception(f"unhandled category in extra: {extra[0]}")

        for barony in baronies:
            if barony not in mapping:
                mapping[barony] = []
            if extra[0] != "title" and barony in ("b_al-ghaba", "b_damascus"):
                continue  # edge cases or maybe add_special_building_slot issue :/
            mapping[barony].append(extra[2])  # first in list has priority

    return mapping


EXTRA_SPECIAL_MAPPING = map_extra_special()


def load_provinces() -> list[dict]:
    provinces = {}
    map_path = BASEPATH.joinpath("map_data/default.map")
    with map_path.open("r") as f:
        for line in f.readlines():
            linesplit = line.split(" ")
            if linesplit[0] not in (
                "sea_zones",
                "river_provinces",
                "lakes",
                "impassable_mountains",
                "impassable_seas",
            ):
                continue
            values = [
                int(x)
                for x in line[line.index("{") + 1 : line.index("}")].strip().split()
            ]

            # last defined wins
            if linesplit[2] == "RANGE":
                for i in range(values[0], values[1] + 1):
                    provinces[i] = linesplit[0]
            elif linesplit[2] == "LIST":
                for provid in values:
                    provinces[provid] = linesplit[0]
            else:
                raise Exception("Unxpected Value")

    prov_terrain_path = BASEPATH.joinpath(
        "common/province_terrain/00_province_terrain.txt"
    )
    with prov_terrain_path.open("r", encoding="utf-8-sig") as f:
        for line in f.readlines():
            if not line.strip() or line[0] == "#":
                continue
            content = re.match(r"(\w+)=(\w+)", line)
            provid, value = (content[1], content[2])
            try:
                provid = int(provid)
            except ValueError:
                continue
            if provid in provinces:
                continue  # default.map has prority
            provinces[provid] = value

    definitions = []  # Some of these are rivers or sea

    definitions_path = BASEPATH.joinpath("map_data/definition.csv")
    with definitions_path.open("r") as f:
        reader = csv.reader(f, delimiter=";")
        next(reader)  # Skip Header

        for row in reader:
            if row[0][0] == "#":  # Commented Line
                continue
            if row[4] == "":  # No name can be ignored
                continue
            provid = int(row[0])
            definitions.append(
                {
                    "id": provid,
                    "color": [int(x) for x in row[1:4]],
                    "terrain": provinces[provid] if provid in provinces else "plains",
                }
            )  # id, red, green, blue
    return definitions


class Title:
    ALL: dict[str, "Title"] = {}
    RANK: dict[str, "Title"] = {
        CWTitle.BARONY: [],
        CWTitle.COUNTY: [],
        CWTitle.DUCHY: [],
        CWTitle.KINGDOM: [],
        CWTitle.EMPIRE: [],
    }
    RANKS = list(RANK.keys())

    def __init__(self):
        self.name: str = None
        self.rank: str = None
        self.color: CWColor = None
        self.province: int = None
        self.capital: list[tuple[CWHistoryDate, Title]] = []
        self.altnames: dict[str, list[str]] = {}
        self.altnames_date: list[tuple[CWHistoryDate, str]] = []
        self.parent: list[tuple[CWHistoryDate, Title]] = []
        self.development: list[tuple[CWHistoryDate, int]] = []
        self.children: list[list[Title]] = []
        self.title_history: list[CWHistoryDate] = []
        self.culture: list[tuple[CWHistoryDate, CWCulture]] = []
        self.faith: list[tuple[CWHistoryDate, CWFaith]] = []
        self.terrain: str = None
        self.holding: list[tuple[CWHistoryDate, str]] = []
        self.special: list[tuple[CWHistoryDate, str]] = []
        self.special_slot: list[tuple[CWHistoryDate, str]] = []
        self.province_history: list[CWHistoryDate] = []
        self.can_create: CWObject = None

    def __repr__(self) -> str:
        return self.name

    @classmethod
    def initialize(cls):
        stubdate = CWHistoryDate()
        stubdate.date = Token("1.1.1")
        stubdate.datenum = 10101

        for cwtitle in CWTitle.ALL.values():
            title = cls()
            title.name = cwtitle.name
            title.rank = cwtitle.rank
            if title in cls.ALL:
                raise Exception(f"Duplicate Title: {title.name}")
            cls.ALL[title.name] = title
            cls.RANK[title.rank].append(title)

            # First value is base
            if len(cwtitle.parents) > 0:
                title.parent.append((stubdate, cwtitle.parents[-1]))
            else:
                title.parent.append((stubdate, None))
            title.children.append([])
            title.development.append((stubdate, 0))
            for _ in STARTING_DATES:
                title.children.append([])
                title.development.append((stubdate, 0))
            title.altnames_date.append((stubdate, None))
            title.culture.append((stubdate, None))
            title.faith.append((stubdate, None))
            title.holding.append((stubdate, None))
            title.special.append((stubdate, None))
            title.special_slot.append((stubdate, None))
            title.capital.append((stubdate, cwtitle.capital))

            title.color = cwtitle.color
            title.province = cwtitle.province
            if title.province:
                title.province = cwtitle.province.token

            for item in cwtitle.cultural_names:
                namelist = item.name
                value = item.values.token
                if value not in title.altnames:
                    title.altnames[value] = []
                if namelist not in title.altnames[value]:  # set messes up order
                    title.altnames[value].append(namelist)

            if title.name in CWHistoryTitle.ALL:
                title.title_history = CWHistoryTitle.ALL[title.name].dates
            if title.province in CWHistoryProvince.ALL:
                title.province_history = CWHistoryProvince.ALL[title.province].dates

            title.can_create = cwtitle.can_create

    @classmethod
    def after_initialize(cls):
        # Resolve History
        # Development Applied from Parent goes down to all children
        # Only apply to de jure
        # Lower Ranked first

        # Compares two dates, returns the bigger one
        # matching conditions
        def compare_history(
            field: str, title: Title, base: CWHistoryDate, limit: str, province: bool
        ):
            comparision_date = base
            if province:
                dates = title.province_history
            else:
                dates = title.title_history
            for date in dates:
                if date.__dict__[field] is None:
                    continue
                if date > STARTING_DATES[limit]:
                    continue
                if date < comparision_date:
                    continue  # dates defined later have priority
                comparision_date = date
            return comparision_date

        print("Resolving de jure")
        # Resolve de jures
        for rank in cls.RANKS:
            for title in cls.RANK[rank]:
                for starting_date in STARTING_DATES:
                    comparision_date = compare_history(
                        "de_jure_liege",
                        title,
                        title.parent[-1][0],
                        starting_date,
                        False,
                    )
                    if comparision_date.de_jure_liege is not None:
                        if type(comparision_date.de_jure_liege) is Token:
                            if comparision_date.de_jure_liege.token != 0:
                                raise Exception(
                                    f"Unexpected Value {comparision_date.de_jure_liege}"
                                )
                            title.parent.append((comparision_date, None))
                        else:
                            title.parent.append(
                                (
                                    comparision_date,
                                    comparision_date.de_jure_liege,
                                )
                            )
                    else:
                        title.parent.append(title.parent[-1])

        print("Resolving children")
        # Resolve children, bigger to smaller pool
        for rank in range(len(cls.RANKS)):
            if cls.RANKS[rank] == CWTitle.EMPIRE:
                continue  # empire is children of none
            for child_title in cls.RANK[cls.RANKS[rank]]:
                for index in range(len(STARTING_DATES) + 1):
                    parent_title = child_title.parent[index][1]  # CWTitle
                    if parent_title is None:
                        continue  # de_jure_liege = 0
                    parent_title = cls.ALL[parent_title.name]  # Title
                    child_title.parent[index] = (
                        child_title.parent[index][0],
                        parent_title,
                    )
                    parent_title.children[index].append(child_title)

        print("Resolving capital")
        for rank in range(len(cls.RANKS)):
            if cls.RANKS[rank] == CWTitle.EMPIRE:
                continue  # barony has no capital
            for title in cls.RANK[cls.RANKS[rank]]:
                if title.capital[0][1] is not None:
                    title.capital[0] = (
                        title.capital[0][0],
                        cls.ALL[title.capital[0][1].name],
                    )

        print("Resolving development and alternative date names")
        # Resolve development, top to bottom
        for rank in reversed(range(len(cls.RANKS))):
            if cls.RANKS[rank] == CWTitle.BARONY:
                continue  # barony has no development
            for title in cls.RANK[cls.RANKS[rank]]:
                for index, starting_date in enumerate(STARTING_DATES):
                    # Development
                    comparision_date = compare_history(
                        "change_development_level",
                        title,
                        title.development[index + 1][0],
                        starting_date,
                        False,
                    )
                    if comparision_date.change_development_level is not None:
                        title.development[index + 1] = (
                            comparision_date,
                            comparision_date.change_development_level.token,
                        )
                    else:
                        title.development[index + 1] = title.development[index]
                    if title.rank != CWTitle.COUNTY:
                        # barony has no development
                        for child_title in title.children[index + 1]:
                            # top to bottom, pass development to children
                            child_title.development[index + 1] = title.development[
                                index + 1
                            ]

                    # Alternative Name
                    # 'reset_name = yes' can be ignored for the wiki
                    # Modification from compare_history function
                    comparision_date = title.altnames_date[-1][0]
                    datename = None
                    for date in title.title_history:
                        if date > STARTING_DATES[starting_date]:
                            continue
                        if date < comparision_date:
                            continue  # dates defined later have priority
                        if date.name is not None:
                            comparision_date = date
                            datename = comparision_date.name.token
                        elif date.effect is not None:
                            if type(date.effect[0]) is not CWObject:
                                continue
                            effect = date.effect[0]
                            if effect.name != "set_title_name":
                                continue
                            comparision_date = date
                            datename = effect.values.token
                    if datename is not None:
                        title.altnames_date.append((comparision_date, datename))
                    else:
                        title.altnames_date.append(title.altnames_date[-1])

                    # New Capital
                    # effect set_capital_county
                    comparision_date = title.capital[-1][0]
                    datecapital = None
                    for date in title.title_history:
                        if date > STARTING_DATES[starting_date]:
                            continue
                        if date < comparision_date:
                            continue  # dates defined later have priority
                        if date.effect is not None:
                            if type(date.effect[0]) is not CWObject:
                                continue
                            effect = date.effect[0]
                            if effect.name != "set_capital_county":
                                continue
                            comparision_date = date
                            datecapital = effect.values.token
                            if "title:" in datecapital:
                                datecapital = datecapital[len("title:") :]
                            datecapital = cls.ALL[datecapital]
                    if datecapital is not None:
                        title.capital.append((comparision_date, datecapital))
                    else:
                        title.capital.append(title.capital[-1])

        print("Resolving baronies values")
        for title in cls.RANK[CWTitle.BARONY]:
            for starting_date in STARTING_DATES:
                # Culture
                comparision_date = compare_history(
                    "culture", title, title.culture[-1][0], starting_date, True
                )
                if comparision_date.culture is not None:
                    title.culture.append((comparision_date, comparision_date.culture))
                else:
                    title.culture.append(title.culture[-1])

                # Faith
                comparision_date = compare_history(
                    "religion", title, title.faith[-1][0], starting_date, True
                )
                if comparision_date.religion is not None:
                    title.faith.append((comparision_date, comparision_date.religion))
                else:
                    title.faith.append(title.faith[-1])

                # Holding
                comparision_date = compare_history(
                    "holding", title, title.holding[-1][0], starting_date, True
                )
                if comparision_date.holding is not None:
                    title.holding.append((comparision_date, comparision_date.holding))
                else:
                    title.holding.append(title.holding[-1])

                # Special Building
                comparision_date = compare_history(
                    "special_building", title, title.special[-1][0], starting_date, True
                )
                if comparision_date.special_building is not None:
                    title.special.append(
                        (comparision_date, comparision_date.special_building)
                    )
                else:
                    title.special.append(title.special[-1])

                # Special Building Slot
                comparision_date = compare_history(
                    "special_building_slot",
                    title,
                    title.special_slot[-1][0],
                    starting_date,
                    True,
                )
                if comparision_date.special_building_slot is not None:
                    title.special_slot.append(
                        (comparision_date, comparision_date.special_building_slot)
                    )
                else:
                    title.special_slot.append(title.special_slot[-1])

                    # effect = { set_title_name = c_lower_silesia }

            # Check if county capital
            county = cls.ALL[title.parent[0][1].name]
            if title.name == county.capital[0][1].name:
                county.culture = title.culture
                county.faith = title.faith

            # Add extra special buildings
            if title.name in EXTRA_SPECIAL_MAPPING:
                # Values added by history files always win
                specials = [value[1] for value in title.special]
                specials += [value[1] for value in title.special_slot]
                specials = set(specials)
                if (len(specials) == 1) or (
                    title.name == "b_somapur"  # remove_building = generic_university
                ):  # None is always present
                    # baronies with a special building are skipped
                    building = CWBuilding.ALL[
                        EXTRA_SPECIAL_MAPPING[title.name][0]
                    ]  # first one wins
                    for index in range(len(STARTING_DATES) + 1):
                        title.special[index] = (title.special[index][0], building)


Title.initialize()
Title.after_initialize()

# colors from the wiki
terrain_mapping = [
    ["desert", CWLoc["desert"].value, 240, 240, 8],
    ["desert_mountains", CWLoc["desert_mountains"].value, 84, 84, 37],
    ["drylands", CWLoc["drylands"].value, 255, 20, 175],
    ["farmlands", CWLoc["farmlands"].value, 0, 255, 0],
    ["floodplains", CWLoc["floodplains"].value, 0, 0, 255],
    ["forest", CWLoc["forest"].value, 0, 128, 0],
    ["hills", CWLoc["hills"].value, 128, 0, 0],
    ["jungle", CWLoc["jungle"].value, 0, 100, 0],
    ["mountains", CWLoc["mountains"].value, 128, 128, 128],
    ["oasis", CWLoc["oasis"].value, 30, 144, 255],
    ["plains", CWLoc["plains"].value, 233, 150, 122],
    ["steppe", CWLoc["steppe"].value, 144, 128, 0],
    ["taiga", CWLoc["taiga"].value, 143, 188, 143],
    ["wetlands", CWLoc["wetlands"].value, 0, 191, 255],
    ["river_provinces", "River", 0, 125, 255],
    ["sea_zones", "Sea", 14, 78, 199],
    ["impassable_mountains", "Impassable Mountains", 0, 0, 0],
    ["lakes", "Lake", 0, 196, 255],
    ["impassable_seas", "Sea", 0, 0, 50],
]

data = {
    "provinces": {},
    "titles": {},
    "faith": {},
    "culture": {},
    "terrain": terrain_mapping,
}
for province in load_provinces():
    data["provinces"][province["id"]] = [province["terrain"], *province["color"]]

data_titles = list(
    (
        (tid, title)
        for tid, title in Title.ALL.items()
        if not (title.rank != CWTitle.BARONY and len(title.children[1]) == 0)
    )
)

# Add creatable Kingdom like k_cornwall but avoid k_papal_state
while data_titles:
    tid, title = data_titles.pop()

    entry = {
        "rank": title.rank.lower(),
        "name": CWLoc[title.name].value,
        "color": title.color.rgb(),
    }

    if title.rank != CWTitle.EMPIRE:
        entry["parent"] = title.parent[1][1].name

    if title.rank == CWTitle.COUNTY:
        entry["development"] = title.development[1][1]
        entry["faith"] = title.faith[1][1].name
        if entry["faith"] not in data["faith"]:
            data["faith"][entry["faith"]] = {
                "name": CWLoc[entry["faith"]].value,
                "color": [int(k) for k in title.faith[1][1].color.rgb()],
            }

        entry["culture"] = title.culture[1][1].name
        if entry["culture"] not in data["culture"]:
            data["culture"][entry["culture"]] = {
                "name": CWLoc[entry["culture"]].value,
                "color": [int(k) for k in title.culture[1][1].color.rgb()],
            }

    if title.rank != CWTitle.BARONY:
        entry["children"] = [t.name for t in title.children[1]]
        for child in entry["children"]:
            if child not in data["titles"] and child not in (k[0] for k in data_titles):
                print(f"Added {child}")
                data_titles.append((child, Title.ALL[child]))

    if title.rank == CWTitle.BARONY:
        entry["province"] = title.province

    data["titles"][tid] = entry


with open("data.json", "w", encoding="utf8") as f:
    json.dump(data, f, indent=4)

pass

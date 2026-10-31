"""Structure constants of the busyness model, and the shared behaviour constants.

Structure constants shape the network, villages and sectors, and so the structure file. Behaviour constants (pull,
ability groups, end-of-day factors and so on) live in busyness-engine/src/params.json, shared with the engine; the
pipeline reads them because sector-finding needs the pull rules. Rationale: docs/decisions/004 to 011.
"""

import json
from functools import cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE_PARAMS = ROOT / "busyness-engine" / "src" / "params.json"

# Which domains are modelled (busyness-pipeline)
MIN_KM = 30  # piste km a top-level domain needs...
MIN_LIFTS = 5  # ...and lifts that aren't nursery lifts

# The structure format. Bump when structure code changes what it writes, so every domain is rebuilt.
MODEL_VERSION = 2

# Network (005)
SNAP_M = 40  # line ends this close join into one junction
LIFT_STATION_M = 100  # a lift's end joins runs passing this close
LIFT_TOP_M = 150  # a lift's top links to runs starting this close
LIFT_BOTTOM_M = 100  # runs ending this close link to a lift's bottom
WALK_S = 30  # time for a walking link
DOWNLOAD_LIFTS = {"gondola", "cable_car", "funicular", "mixed_lift"}  # can be ridden down in the evening

# Capacity and time (004, 009)
CAP_BY_TYPE = {"chair_lift": 2000, "gondola": 2200, "cable_car": 600, "t-bar": 1000, "platter": 720,
               "drag_lift": 720, "j-bar": 720, "rope_tow": 600, "magic_carpet": 900, "funicular": 1500,
               "mixed_lift": 2200, "railway": 1000}
CAP_RANGE = (100, 6000)  # recorded capacities outside this are treated as missing
DURATION_RANGE = (30, 2400)  # recorded ride times outside this (seconds) are treated as missing
LIFT_SPEED = {"chair_lift": 2.5, "gondola": 5, "cable_car": 8, "funicular": 8, "mixed_lift": 5, "railway": 5,
              "magic_carpet": 0.8}
DEFAULT_LIFT_SPEED = 3.0
WAIT_S = 90  # queueing and loading, per lift ride
RUN_SPEED = [4.0, 6.0, 7.0, 6.0, 6.0]  # m/s by grade (0 green .. 3 black, 4 ungraded), with stops
LIFTS_PER_HOUR = 3.5  # rides per skier per hour: a domain's skiers = its lift capacity / this


def flat_speed(g: float) -> float:
    """Share of its grade's speed a run allows, by average gradient: flat runs mean poling."""
    return 0.4 if g < 0.04 else 0.6 if g < 0.08 else 0.85 if g < 0.12 else 1.0


def route_effort(g: float) -> float:
    """How much slower a run feels by gradient: poling on flat runs, care on very steep ones."""
    return 1.4 if g < 0.06 else 1.3 if g > 0.45 else 1.0


# Nursery areas are links only, left to ski school (005)
NURSERY_LIFTS = {"magic_carpet", "rope_tow"}
DRAG_LIFTS = {"platter", "t-bar", "j-bar", "drag_lift"}
NURSERY_DRAG_M = 300  # drag lifts shorter than this are nursery lifts
NURSERY_SLOPE_M = 400  # green runs shorter than this...
NURSERY_SLOPE_END_M = 100  # ...ending this close to a nursery lift's bottom are nursery slopes

# Sectors (007)
SECTOR_MIN = 0.04  # a sector with less than this share of the domain's lift capacity merges into a neighbour
COMMUTE_TOP = 0.6  # a sector's commuting share = COMMUTE_TOP x (1 - its share of the domain's lift capacity) (009)

# Villages (008)
OVERTURE_RELEASE = "2026-10-21.0"  # pinned: moving it re-harvests places and rebuilds every domain
PLACE_M = 1000  # lift stations this close to a place's point belong to it
PLACE_BUILDINGS_M = 500  # a place's size: buildings within this distance of its point...
PLACE_MIN_BUILDINGS = 50  # ...and below this it's a thoroughfare, not a village
PLACE_VILLAGE_CAP = 500  # lift capacity (non-nursery) a place needs leaving it to be a village
VILLAGE_RISE_M = 200  # a village takes in stations up to this far above its lowest one
# Fallback when places can't be had: villages from the lift layout
STATION_M = 300  # lift bottoms this close (and within STATION_RISE_M of height) form one station
STATION_RISE_M = 120
VILLAGE_CAP = 1500  # lift capacity leaving a station for it to be a village
VILLAGE_RADIUS_M = 1500  # ...with no lower station (by over 50 m) this close
VILLAGE_SPREAD_M = 800  # a village takes in stations this close and up to VILLAGE_RISE_M above it


@cache
def behaviour() -> dict:
    """The shared behaviour constants from busyness-engine/src/params.json."""
    return json.loads(ENGINE_PARAMS.read_text(encoding="utf-8"))

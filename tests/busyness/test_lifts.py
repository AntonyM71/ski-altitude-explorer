"""busyness-lift-estimates scenarios."""

import pytest

from busyness import params as P
from busyness.lifts import estimate, name_hints, seats


@pytest.mark.parametrize("name, n", [
    ("TSD6 Grand Col", 6), ("TSF2 Riba", 2), ("TS4 Da Fontefría", 4),  # French codes
    ("6er-SB Garnitzen", 6), ("Doppelsesselbahn Schetteregg", 2), ("Vierer Sessel", 4),  # German
    ("Seggiovia Biposto", 2), ("6-CLD-B", 6),  # Italian, Doppelmayr codes
    ("Summit Quad", 4), ("Eagle Cliff Triple", 3), ("Mt. Mansfield Double", 2), ("No. 1 Pair Lift", 2),  # English
    ("第3ペアリフト", 2), ("第2ロマンス", 2), ("トリプル1", 3), ("第1クワッドリフト", 4),  # Japanese
    ("Rajska šestosjed", 6),  # Croatian/Bosnian
])
def test_seats_from_names(name, n):
    assert name_hints(name)[1] == n


@pytest.mark.parametrize("name", ["Krzesło Doppelmayr", "Seggiovia Florianca", "Sechszeiger", None])
def test_names_with_no_seat_count(name):
    assert name_hints(name)[1] is None


def test_quadruple_is_four_not_double():
    assert name_hints("1 Quadruple Doppelmayr")[1] == 4


@pytest.mark.parametrize("name", ["Ridge Express", "Elfriede Huter Xpress", "TSD4 Tarter", "High Speed Lift No. 4",
                                  "かぐら第1高速リフト", "Rocky Mountain SuperChair", "Orange Bubble Express"])
def test_fast_names(name):
    assert name_hints(name)[0] == "fast"


def test_fixed_and_plain_names():
    assert name_hints("TSF4 Vescal")[0] == "fixed"
    assert name_hints("Telesilla Parador I")[0] is None


def lift(name, type="chair_lift", occupancy=None):
    return {"name": name, "liftType": type, "occupancy": occupancy}


def test_seats_from_a_name():
    assert seats(lift("Summit Quad")) == (4, "name")


def test_recorded_seats_win_over_the_name():
    assert seats(lift("Summit Quad", occupancy=3)) == (3, "seats")


def test_capacity_typed_into_the_seats():
    assert seats(lift("Platter 3", type="platter", occupancy=720)) == (None, None)


def test_implausible_name_seats_are_missing():
    assert seats(lift("Six Pack", type="platter")) == (None, None)


def raw(type="chair_lift", name="Lift", occupancy=None, capacity=None, duration=None):
    return {"liftType": type, "name": name, "occupancy": occupancy, "capacity": capacity, "duration": duration}


def test_recorded_capacity_kept_speed_estimated():
    cap, cap_src, speed, speed_src = estimate(raw(capacity=2400, occupancy=4), 800)
    assert (cap, cap_src) == (2400, "recorded")
    assert speed_src == "seats"


def test_implausible_capacity_is_estimated():
    cap, cap_src, *_ = estimate(raw(capacity=32200, occupancy=4), 800)
    assert (cap, cap_src) == (P.CHAIR_CAP[(4, False)], "seats")


def test_short_two_seater():
    cap, cap_src, speed, speed_src = estimate(raw(occupancy=2), 600)
    assert cap == P.CHAIR_CAP[(2, False)] < 2000 and cap_src == "seats"
    assert speed == P.CHAIR_SPEED[(2, False)] and speed_src == "seats"


def test_long_six_seater():
    *_, speed, _ = estimate(raw(occupancy=6), 1800)
    assert speed == P.CHAIR_SPEED[(6, True)] > 1.8 * P.LIFT_SPEED["chair_lift"]  # about twice the typical chairlift


def test_fast_named_quad_carries_more():
    assert estimate(raw(name="Ridge Express", occupancy=4), 1200)[0] > estimate(raw(occupancy=4), 1200)[0]


def test_fast_two_seater_falls_back_within_its_seats():
    assert estimate(raw(name="Express", occupancy=2), 600)[0] == P.CHAIR_CAP[(2, False)]


def test_four_seat_gondola():
    cap, cap_src, speed, speed_src = estimate(raw("gondola", occupancy=4), 1500)
    assert cap == P.GONDOLA_CAP[4] < 2200 and cap_src == "seats"
    assert (speed, speed_src) == (P.LIFT_SPEED["gondola"], "type")


def test_small_cable_car_is_a_gondola():
    assert estimate(raw("cable_car", occupancy=8), 1500)[:2] == (P.GONDOLA_CAP[8], "seats")


def test_long_cable_car():
    cap, cap_src, *_ = estimate(raw("cable_car", occupancy=100), 2500)
    assert round(cap) == 829 and cap_src == "seats"


def test_shorter_cable_car_carries_more():
    assert estimate(raw("cable_car", occupancy=100), 1000)[0] > estimate(raw("cable_car", occupancy=100), 2500)[0]


def test_t_bar_takes_the_type_value():
    assert estimate(raw("t-bar"), 600)[:2] == (1000, "type")


def test_chairlift_with_no_seats():
    assert estimate(raw(name="Col"), 900) == (2000, "type", 2.5, "type")


def test_unusual_seat_count_takes_the_type_value():
    assert estimate(raw("gondola", occupancy=22), 2000)[:2] == (2200, "type")


def test_ride_time_from_estimated_speed():
    length = 1500
    *_, speed, _ = estimate(raw("gondola"), length)
    assert length / speed == 300


def test_recorded_ride_time():
    *_, speed, speed_src = estimate(raw(duration=300), 1500)
    assert (speed, speed_src) == (5, "recorded")


def test_seats_from_name_are_the_source():
    cap_src, speed_src = estimate(raw(name="Summit Quad", duration=400), 1200)[1::2]
    assert (cap_src, speed_src) == ("name", "recorded")


def test_same_lift_same_estimate():
    assert estimate(raw(occupancy=6), 1400) == estimate(raw(occupancy=6), 1400)

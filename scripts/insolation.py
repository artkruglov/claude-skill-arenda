# -*- coding: utf-8 -*-
"""Калькулятор инсоляции: сколько прямого солнца получит квартира.

Считает часы прямого солнечного света в окно с учётом стороны света,
широты, сезона и затенения соседними домами.

Запуск без аргументов печатает справочные таблицы для Москвы.
"""
import math

# ---------- астрономия ----------

def declination(day_of_year):
    """Склонение солнца в градусах для дня года."""
    return 23.45 * math.sin(math.radians(360.0 * (284 + day_of_year) / 365.0))


def solar_position(lat, dec, hour_angle):
    """Высота и азимут солнца в градусах.

    Азимут: 0 = север, 90 = восток, 180 = юг, 270 = запад.
    """
    la, d, h = map(math.radians, (lat, dec, hour_angle))
    sin_alt = math.sin(la) * math.sin(d) + math.cos(la) * math.cos(d) * math.cos(h)
    alt = math.degrees(math.asin(max(-1.0, min(1.0, sin_alt))))
    cos_az = (math.sin(d) - math.sin(math.radians(alt)) * math.sin(la)) / \
             (math.cos(math.radians(alt)) * math.cos(la) + 1e-9)
    az = math.degrees(math.acos(max(-1.0, min(1.0, cos_az))))
    if hour_angle > 0:
        az = 360.0 - az
    return alt, az


def sun_hours(lat, window_azimuth, day, obstruction=0.0, fov=90.0):
    """Часы прямого солнца в окно.

    lat             широта, градусы (Москва 55.75)
    window_azimuth  куда смотрит окно: 0 север, 90 восток, 180 юг, 270 запад
    day             день года: 355 = 21 дек, 80 = 21 мар, 172 = 21 июн
    obstruction     угол закрытия горизонта препятствием, градусы
    fov             сектор видимости окна, обычно 90 для плоского окна
    """
    dec = declination(day)
    minutes = 0
    for m in range(0, 24 * 60, 10):
        alt, az = solar_position(lat, dec, (m / 60.0 - 12.0) * 15.0)
        if alt <= obstruction:
            continue
        if abs((az - window_azimuth + 180) % 360 - 180) <= fov / 2:
            minutes += 10
    return round(minutes / 60.0, 1)


def obstruction_angle(height_m, distance_m, observer_height_m=0.0):
    """Угол закрытия горизонта зданием.

    observer_height_m — высота окна над землёй; чем выше этаж,
    тем меньше мешает соседний дом.
    """
    effective = max(0.0, height_m - observer_height_m)
    return round(math.degrees(math.atan2(effective, distance_m)), 1)


def floors_to_meters(floors, floor_height=3.0):
    """Этажи в метры. 3.0 современный монолит, 2.8 панель, 3.2 сталинка."""
    return floors * floor_height


def verdict(winter_hours):
    if winter_hours >= 5:
        return "отлично, солнце в комнате зимой"
    if winter_hours >= 2:
        return "нормально"
    if winter_hours >= 0.5:
        return "мало, зимой будет сумрачно"
    return "прямого солнца зимой нет"


# ---------- справочные данные ----------

LAT_MOSCOW = 55.75
DAYS = {"21 дек": 355, "21 мар": 80, "21 июн": 172, "21 сен": 264}
AZIMUTHS = {
    "север": 0, "северо-восток": 45, "восток": 90, "юго-восток": 135,
    "юг": 180, "юго-запад": 225, "запад": 270, "северо-запад": 315,
}


def main():
    lat = LAT_MOSCOW

    print("МАКСИМАЛЬНАЯ ВЫСОТА СОЛНЦА")
    for name, d in DAYS.items():
        alt, _ = solar_position(lat, declination(d), 0)
        print(f"  {name}: {alt:.1f}°")

    print("\nЧАСЫ ПРЯМОГО СОЛНЦА ПО СТОРОНАМ (открытый горизонт)")
    print(f"  {'сторона':<16}{'21 дек':>9}{'21 мар':>9}{'21 июн':>9}")
    for name, az in AZIMUTHS.items():
        row = [sun_hours(lat, az, d) for d in (355, 80, 172)]
        print(f"  {name:<16}{row[0]:>9}{row[1]:>9}{row[2]:>9}")

    print("\nЗАТЕНЕНИЕ СОСЕДНИМ ДОМОМ (окно на юг)")
    print(f"  {'препятствие':<28}{'угол':>7}{'21 дек':>9}{'21 мар':>9}{'21 июн':>9}")
    cases = [
        ("открытый горизонт", 0, 0),
        ("5 этажей в 30 м", 5, 30),
        ("9 этажей в 30 м", 9, 30),
        ("9 этажей в 60 м", 9, 60),
        ("17 этажей в 40 м", 17, 40),
        ("25 этажей в 50 м", 25, 50),
        ("25 этажей в 100 м", 25, 100),
    ]
    for label, fl, dist in cases:
        ang = obstruction_angle(floors_to_meters(fl), dist) if fl else 0.0
        row = [sun_hours(lat, 180, d, ang) for d in (355, 80, 172)]
        print(f"  {label:<28}{ang:>6}°{row[0]:>9}{row[1]:>9}{row[2]:>9}")

    print("\nВЫВОД")
    print("  Зимой солнце поднимается лишь на 10.8°, поэтому почти любое")
    print("  здание напротив обнуляет зимнее солнце. Чтобы девятиэтажка")
    print("  не загораживала его, она должна стоять дальше 140 метров.")

    print("\nПРИМЕР РАСЧЁТА КОНКРЕТНОЙ КВАРТИРЫ")
    print("  окна на юго-запад, 7 этаж, напротив 12 этажей в 45 м")
    obs = obstruction_angle(floors_to_meters(12), 45, floors_to_meters(7))
    for name, d in (("21 дек", 355), ("21 мар", 80), ("21 июн", 172)):
        h = sun_hours(lat, 225, d, obs)
        print(f"    {name}: {h} ч" + (f"  — {verdict(h)}" if d == 355 else ""))


if __name__ == "__main__":
    main()

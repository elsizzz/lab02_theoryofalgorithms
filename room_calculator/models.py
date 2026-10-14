class Room:
    """Класс, представляющий комнату."""
    def __init__(self, name, length, width, height, insulation="medium"):
        self.name = name
        self.length = length
        self.width = width
        self.height = height
        self.insulation = insulation

    def area(self):
        """Расчёт площади комнаты."""
        return self.length * self.width

    def volume(self):
        """Расчёт объёма комнаты."""
        return self.area() * self.height

    def heating_power(self):
        """Расчёт тепловой мощности с учётом утепления (1 кВт на 10 кв.м)."""
        base_power = self.area() / 10.0
        if self.insulation == "low":
            return base_power * 1.5
        elif self.insulation == "high":
            return base_power * 0.8
        return base_power

    def __str__(self):
        return f"Комната: {self.name}, Площадь: {self.area():.2f} кв.м, Тепловая мощность: {self.heating_power():.2f} кВт"


class Apartment:
    """Класс, представляющий квартиру."""
    def __init__(self, name):
        self.name = name
        self.rooms = []

    def add_room(self, room):
        self.rooms.append(room)

    def total_area(self):
        return sum(room.area() for room in self.rooms)

    def total_heating_power(self):
        return sum(room.heating_power() for room in self.rooms)

    def __str__(self):
        return f"Квартира: {self.name}, Общая площадь: {self.total_area():.2f} кв.м, Тепловая мощность: {self.total_heating_power():.2f} кВт"


class Building:
    """Класс, представляющий многоэтажный дом."""
    def __init__(self, name):
        self.name = name
        self.apartments = []

    def add_apartment(self, apartment):
        self.apartments.append(apartment)

    def total_area(self):
        return sum(apt.total_area() for apt in self.apartments)

    def total_heating_power(self):
        return sum(apt.total_heating_power() for apt in self.apartments)

    def __str__(self):
        return f"Здание: {self.name}, Общая площадь: {self.total_area():.2f} кв.м, Тепловая мощность: {self.total_heating_power():.2f} кВт"
from .models import Building

class Calculator:
    """Класс для выполнения расчётов."""
    
    @staticmethod
    def get_total_area(building: Building) -> float:
        return building.total_area()

    @staticmethod
    def get_total_heating(building: Building) -> float:
        return building.total_heating_power()
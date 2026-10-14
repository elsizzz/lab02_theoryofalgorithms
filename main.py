from room_calculator.models import Room, Apartment, Building
from room_calculator.report_generator import ReportGenerator

def get_float_input(prompt):
    """Вспомогательная функция для безопасного ввода чисел."""
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("Ошибка: введите корректное число.")

def main():
    print("  Калькулятор помещений (MVP)")
    
    building_name = input("Введите название здания: ")
    building = Building(building_name)

    while True:
        apt_name = input("\nВведите название квартиры (или 'готово' для завершения): ")
        if apt_name.lower() == 'готово':
            break

        apartment = Apartment(apt_name)

        while True:
            room_name = input(f"  Введите название комнаты в {apt_name} (или 'готово' для завершения квартиры): ")
            if room_name.lower() == 'готово':
                break

            length = get_float_input(f"    Длина {room_name} (м): ")
            width = get_float_input(f"    Ширина {room_name} (м): ")
            height = get_float_input(f"    Высота {room_name} (м): ")

            print("    Уровень утепления: low / medium / high")
            insulation = input("    Введите уровень утепления: ").lower()
            if insulation not in ['low', 'medium', 'high']:
                insulation = 'medium'
                print("    [Примечание] Выбран уровень по умолчанию: medium")

            room = Room(room_name, length, width, height, insulation)
            apartment.add_room(room)

        building.add_apartment(apartment)

    # Вывод результатов
    print("\n")
    print("  РЕЗУЛЬТАТЫ РАСЧЁТА")
    print(building)
    for apt in building.apartments:
        print(f"  {apt}")

    # Сохранение отчёта
    save_choice = input("\nСохранить отчёт в Word (.docx)? (y/n): ").lower()
    if save_choice == 'y':
        ReportGenerator.save_to_word(building)

if __name__ == "__main__":
    main()
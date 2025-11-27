import json
import time
import datetime
import threading
import os
from typing import List, Dict, Optional


# Подключение библиотеки для звука
try:
    import winsound

    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

try:
    import pygame

    pygame.mixer.init()
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False


class AlarmClock:
    def __init__(self, data_file: str = 'alarms.json'):
        self.data_file = data_file
        self.alarms: List[Dict] = []
        self.load_alarms()  # загрузка при старте

    def load_alarms(self):
        # Загрузка будильники из JSON
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    self.alarms = json.load(f)
                print(f'Загружено {len(self.alarms)} будильников из {self.data_file}')
            except (json.JSONDecodeError, IOError) as e:
                print(f'\033[31mОшибка загрузки: {e}.\nНачинаем с пустого списка!\033[0m')
                self.alarms = []
        else:
            self.alarms = []
            print('\033[31mФайл данных не найден.\nСоздан новый список!\033[0m')

    def save_alarms(self):
        # Сохраняем будильники в JSON
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.alarms, f, indent=2, ensure_ascii=False)
            print(f'\033[32mДанные сохранены в {self.data_file}\033[0m')
        except IOError as e:
            print(f'\033[31mОшибка сохранения: {e}\033[0m')

    def add_alarm(self, hour: int, minute: int, days: List[int],
                  sound: str = 'beep', repeat_interval: int = 0,
                  message: str = '\033[31mВремя вставать!\033[0m'):

        # Добавляем будильник
        alarm = {
            'hour': hour,
            'minute': minute,
            'days': days,
            'sound': sound,
            'repeat_interval': repeat_interval,
            'message': message,
            'active': True
        }
        self.alarms.append(alarm)
        self.save_alarms()
        print(f'\033[33mБудильник установлен на \033[0m{hour:02d}:{minute:02d} (дни: {days})')

    def _is_time_to_alarm(self, alarm: Dict) -> bool:
        # Проверка срабатывания будильника
        now = datetime.datetime.now()
        return (
                now.hour == alarm['hour'] and
                now.minute == alarm['minute'] and
                now.weekday() in alarm['days'] and
                alarm['active']
        )

    def _play_sound(self, sound_type: str):
        # Воспроизведение звука
        if sound_type == 'beep' and HAS_WINSOUND:
            winsound.Beep(1000, 1000)  # 1 кГц, 1 сек
        elif sound_type.startswith('custom') and HAS_PYGAME:
            sound_file = f'{sound_type}.wav'
            if os.path.exists(sound_file):
                pygame.mixer.music.load(sound_file)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.01)
            else:
                print(f'\033[31mЗвук {sound_file} не найден!\033[0m')
        # else:
        #     print("Звук не воспроизведён (библиотека не подключена).")
        elif sound_type == 'custom1':
            # Пример кастомного звука (нужно добавить файлы)
            if os.path.exists('custom1.wav'):
                winsound.PlaySound('custom1.wav', winsound.SND_FILENAME)
        elif sound_type == 'custom2':
            if os.path.exists('custom2.wav'):
                winsound.PlaySound('custom2.wav', winsound.SND_FILENAME)

    def _trigger_alarm(self, alarm: Dict):
        # Активация будильника
        print(f'\n\033[31m!!! {alarm['message']} !!!\033[0m')
        self._play_sound(alarm["sound"])

        # Повтор, если задан
        if alarm['repeat_interval'] > 0:
            def repeat():
                time.sleep(alarm['repeat_interval'] * 60)
                if alarm['active']:
                    self._trigger_alarm(alarm)

            threading.Thread(target=repeat, daemon=True).start()

    def stop_all_alarms(self):
        # Отключение всеч будильников
        for alarm in self.alarms:
            alarm['active'] = False
        self.save_alarms()
        print('\033[31mВсе будильники отключены!\033[0m')

    def remove_alarm(self, index: int):
        # Удаление будильника по индексу
        if 0 <= index < len(self.alarms):
            del self.alarms[index]
            self.save_alarms()
            print(f'\033[31mБудильник \033[0m" {index + 1} "\033[31m удалён!\033[0m')
        else:
            print('\033[31mНеверный индекс!\033[0m')

    def run(self):
        # Цикл проверки времени
        print('\033[31mБудильник запущен.\n\033[33mДля выхода нажмите Ctrl+C\033[0m')
        try:
            while True:
                for alarm in self.alarms:
                    if self._is_time_to_alarm(alarm):
                        self._trigger_alarm(alarm)
                        if alarm['repeat_interval'] == 0:  # без повтора
                            alarm['active'] = False
                            self.save_alarms()
                time.sleep(1)  # проверка каждую 1 сек
        except KeyboardInterrupt:
            print('\n\033[31mБудильник остановлен!\033[0m')


def get_time_input() -> Optional[tuple]:
    # Ввод времени ЧЧ:ММ
    while True:
        try:
            hour = int(input('\033[33mВведите час (ЧЧ): \033[0m'))
            minute = int(input('\033[33mВведите минуты (ММ): \033[0m'))
            if 0 <= int(hour) <= 23 and 0 <= int(minute) <= 59:
                return hour, minute
            else:
                print('\033[31mЧасы: 0–23, минуты: 0–59\033[0m')
        except ValueError:
            print('\033[31mФормат: ЧЧ ММ (например, 08 30).\033[0m')


def get_days_input() -> List[int]:
    # Дни недели (0=пн, ..., 6=вс)
    print('\033[33mПовтор по дням \033[0m(0 = ПН, 1=ВТ, ..., 6=ВС).'
          '\033[33m Через пробел.\nДля каждодневного — Enter:\033[0m')
    days_str = input('> ').strip()
    if not days_str:
        return list(range(7))
    try:
        days = list(map(int, days_str.split()))
        if all(0 <= d <= 6 for d in days):
            return days
        else:
            print('\033[32mДни: 0–6. Используем все.\033[0m')
            return list(range(7))
    except ValueError:
        print('\033[31mОшибка. Используем все дни!\033[0m')
        return list(range(7))


def get_sound_choice() -> str:
    # Выбор сигнала
    print('\033[33mЗвук:\033[0m')
    print('\033[33m1 \033[0m— Сигнал (beep)')
    print('\033[33m2 \033[0m— Кастом 1 (custom1.wav)')
    print('\033[33m3 \033[0m— Кастом 2 (custom2.wav)')
    choice = input('> ').strip()
    return {'1': 'beep', '2': 'custom1', '3': 'custom2'}.get(choice, 'beep')


def get_repeat_choice() -> int:
    # Интервал повтора в минутах
    try:
        return int(input('\033[33mПовтор через мин (0 — без повтора): \033[0m') or '0')
    except ValueError:
        return 0


def get_message_choice() -> str:
    # Текст сообщения
    msg = input('Сообщение (по умолчанию \033[31m"Время вставать!"\033[0m): ').strip()
    return msg if msg else 'Время вставать!'


def main():
    clock = AlarmClock()

    while True:
        print('\n=== Будильник ===\n'
              '\033[33m1 \033[0m— Установить будильник\n'
              '\033[33m2 \033[0m— Список будильников\n'
              '\033[33m3 \033[0m— Удалить будильник (по номеру)\n'
              '\033[33m4 \033[0m— Остановить все\n'
              '\033[33m5 \033[0m— Выход и запуск будильника')

        choice = input('\n\033[34mВыбор: \033[0m').strip()

        if choice == '1':
            hour, minute = get_time_input()
            days = get_days_input()
            sound = get_sound_choice()
            repeat = get_repeat_choice()
            message = input('Текст сообщения (по умолчанию "Время вставать!"): ').strip()
            if not message:
                message = 'Время вставать!'

            clock.add_alarm(hour, minute, days, sound, repeat, message)

        elif choice == '2':
            if not clock.alarms:
                print('\033[31mБудильников нет!\033[0m')
            else:
                print('\n\033[33mСписок будильников:\033[0m')
                for i, alarm in enumerate(clock.alarms, 1):
                    days_str = ', '.join(str(d) for d in alarm['days'])
                    repeat_str = f'{alarm["repeat_interval"]} мин' if alarm['repeat_interval'] > 0 else 'без повтора'
                    status = 'активен' if alarm['active'] else 'неактивен'
                    print(f'{i}. {alarm["hour"]:02d}:{alarm["minute"]:02d} '
                          f'(дни: {days_str}), звук: {alarm['sound']}, '
                          f'повтор: {repeat_str}, сообщение: "{alarm["message"]}" '
                          f'[{status}]')

        elif choice == '3':
            try:
                idx = int(input('\033[31mНомер будильника для удаления: \033[0m')) - 1
                clock.remove_alarm(idx)
            except ValueError:
                print('\033[31mВведите число!\033[0m')

        elif choice == '4':
            clock.stop_all_alarms()

        elif choice == '5':
            print('\033[33mДо свидания!\033[0m')
            break

        else:
            print('\033[31mНеверный выбор. Попробуйте ещё раз!\033[0m')

    # После выхода из меню запускаем мониторинг будильников
    if clock.alarms:
        clock.run()
    else:
        print('\033[31mНет установленных будильников.\033[0m')


if __name__ == "__main__":
    main()

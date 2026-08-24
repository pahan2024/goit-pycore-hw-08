import pickle
from collections import UserDict
from datetime import datetime, timedelta


def input_error(func):

    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        # 1. Замість системної помилки розпаковки рядка/індексу видаємо зрозумілу інструкцію
        except (ValueError, IndexError):
            return "Please provide all required arguments for this command (e.g. name, phone or date)."
        # 2. Перехоплюємо AttributeError, коли record є None, і виводимо зрозумілий текст
        except AttributeError:
            return "Contact not found."

    return inner


class Field:

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):

    def __init__(self, value):
        if not (isinstance(value, str) and value.isdigit() and len(value) == 10):
            raise ValueError
        super().__init__(value)


class Birthday(Field):

    def __init__(self, value):
        try:
            # Валідуємо формат, але зберігаємо в self.value саме РЯДОК, як вимагає критерій
            datetime.strptime(value, "%d.%m.%Y")
            super().__init__(value)
        except ValueError:
            # Якщо формат неправильний, збуджуємо ValueError, який перехопить декоратор
            raise ValueError


class Record:

    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone_number):
        self.phones.append(Phone(phone_number))

    def remove_phone(self, phone_number):
        phone_to_remove = self.find_phone(phone_number)
        if phone_to_remove:
            self.phones.remove(phone_to_remove)

    def edit_phone(self, old_number, new_number):
        phone_to_edit = self.find_phone(old_number)
        if not phone_to_edit:
            # Викидаємо AttributeError, щоб його перехопив декоратор
            raise AttributeError
        new_phone = Phone(new_number)
        phone_to_edit.value = new_phone.value

    def find_phone(self, phone_number):
        for phone in self.phones:
            if phone.value == phone_number:
                return phone
        return None

    def add_birthday(self, birthday_str):
        self.birthday = Birthday(birthday_str)

    def __str__(self):
        birthday_str = f", birthday: {self.birthday.value}" if self.birthday else ""
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}{birthday_str}"


class AddressBook(UserDict):

    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self):
        upcoming_birthdays = []
        today = datetime.now().date()

        for record in self.data.values():
            if not record.birthday:
                continue

            # Конвертуємо рядок з self.birthday.value в об'єкт дати виключно для розрахунків
            birthday_date = datetime.strptime(record.birthday.value, "%d.%m.%Y").date()
            birthday_this_year = birthday_date.replace(year=today.year)

            if birthday_this_year < today:
                birthday_this_year = birthday_this_year.replace(year=today.year + 1)

            if today <= birthday_this_year <= today + timedelta(days=7):
                congratulation_date = birthday_this_year

                if congratulation_date.weekday() == 5:
                    congratulation_date += timedelta(days=2)
                elif congratulation_date.weekday() == 6:
                    congratulation_date += timedelta(days=1)

                upcoming_birthdays.append(
                    {
                        "name": record.name.value,
                        "birthday": congratulation_date.strftime("%d.%m.%Y"),
                    }
                )

        return upcoming_birthdays

    def __str__(self):
        if not self.data:
            return "Address book is empty."
        return "\n".join(str(record) for record in self.data.values())


def parse_input(user_input):
    if not user_input.strip():
        return "", []
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args


@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message


@input_error
def change_contact(args, book: AddressBook):
    name, old_phone, new_phone = args
    record = book.find(name)
    # Жодних if/else. Якщо record є None, виклик edit_phone викличе AttributeError
    record.edit_phone(old_phone, new_phone)
    return "Contact updated."


@input_error
def show_phone(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    # Якщо record є None, звернення до .phones викличе AttributeError, який обробей декоратор
    return f"{name}'s phones: " + ", ".join(p.value for p in record.phones)


@input_error
def show_all(book: AddressBook):
    return str(book)


@input_error
def add_birthday(args, book: AddressBook):
    name, birthday = args
    record = book.find(name)
    # Якщо record є None, викликається AttributeError
    record.add_birthday(birthday)
    return f"Birthday added for {name}."


@input_error
def show_birthday(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    # Якщо record є None, отримаємо AttributeError. Якщо birthday є None, спрацює блок else
    if record.birthday:
        return f"{name}'s birthday is {record.birthday.value}"
    return f"{name} doesn't have birthday info yet."


@input_error
def birthdays(args, book: AddressBook):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No upcoming birthdays in the next 7 days."

    result = "Upcoming birthdays:\n"
    for user in upcoming:
        result += f"{user['name']}: congratulate on {user['birthday']}\n"
    return result.strip()


def save_data(book, filename="addressbook.pkl"):
    """Серіалізує та зберігає об'єкт AddressBook у бінарний файл."""
    with open(filename, "wb") as f:
        pickle.dump(book, f)


def load_data(filename="addressbook.pkl"):
    """Десеріалізує та повертає AddressBook з файлу.

    Якщо файл відсутній або пошкоджений, створює нову порожню книгу.
    """
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except (FileNotFoundError, EOFError, pickle.UnpicklingError):
        return AddressBook()


def main():
    # Крок 1: Відновлюємо стан адресної книги з попереднього сеансу
    book = load_data()
    print("Welcome to the assistant bot!")

    while True:
        user_input = input("Enter a command: ")
        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            print("Good bye!")
            # Крок 2: Зберігаємо всі напрацьовані дані перед виходом
            save_data(book)
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_contact(args, book))

        elif command == "phone":
            print(show_phone(args, book))

        elif command == "all":
            print(show_all(book))

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        elif command == "":
            continue

        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()

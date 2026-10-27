import json
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


DATA_FILE = Path(__file__).with_name("shopping_list.json")


@dataclass
class ShoppingItem:
    name: str
    purchased: bool = False


def load_items(path: Path) -> list[ShoppingItem]:
    try:
        contents = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []

    try:
        data = json.loads(contents)
    except json.JSONDecodeError as error:
        raise ValueError(f"некорректный JSON в файле {path}") from error

    if not isinstance(data, list):
        raise ValueError(f"ожидался список товаров в файле {path}")

    items = []
    for index, entry in enumerate(data, start=1):
        if (
            not isinstance(entry, dict)
            or not isinstance(entry.get("name"), str)
            or not entry["name"].strip()
            or not isinstance(entry.get("purchased"), bool)
        ):
            raise ValueError(f"некорректная запись товара №{index} в файле {path}")
        items.append(ShoppingItem(entry["name"], entry["purchased"]))

    return items


def save_items(items: list[ShoppingItem], path: Path) -> None:
    data = [
        {"name": item.name, "purchased": item.purchased}
        for item in items
    ]
    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            json.dump(data, temporary_file, ensure_ascii=False, indent=2)
            temporary_file.write("\n")
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def display_items(items: list[ShoppingItem], output: Callable[[str], None]) -> None:
    if not items:
        output("Список покупок пуст.")
        return

    output("Список покупок:")
    for number, item in enumerate(items, start=1):
        mark = "x" if item.purchased else " "
        output(f"{number}. [{mark}] {item.name}")


def run(
    path: Path = DATA_FILE,
    input_fn: Callable[[str], str] | None = None,
    output: Callable[[str], None] | None = None,
) -> int:
    input_fn = input if input_fn is None else input_fn
    output = print if output is None else output

    try:
        items = load_items(path)
    except (OSError, ValueError) as error:
        print(f"Не удалось загрузить список: {error}", file=sys.stderr)
        return 1

    while True:
        output("\n=== Список покупок ===")
        output("1. Добавить товар")
        output("2. Показать список")
        output("3. Отметить товар как купленный")
        output("4. Очистить список")
        output("0. Выход")

        try:
            choice = input_fn("Выберите действие: ").strip()
        except EOFError:
            output("\nДо свидания!")
            return 0

        if choice == "0":
            output("До свидания!")
            return 0

        if choice == "1":
            name = input_fn("Название товара: ").strip()
            if not name:
                output("Название товара не может быть пустым.")
                continue
            items.append(ShoppingItem(name))
            success_message = f"Товар «{name}» добавлен."
        elif choice == "2":
            display_items(items, output)
            continue
        elif choice == "3":
            if not items:
                output("Список покупок пуст.")
                continue
            display_items(items, output)
            number_text = input_fn("Введите номер купленного товара: ").strip()
            try:
                number = int(number_text)
            except ValueError:
                output("Введите целый номер товара.")
                continue
            if not 1 <= number <= len(items):
                output("Товара с таким номером нет.")
                continue
            item = items[number - 1]
            if item.purchased:
                output(f"Товар «{item.name}» уже отмечен как купленный.")
                continue
            item.purchased = True
            success_message = f"Товар «{item.name}» отмечен как купленный."
        elif choice == "4":
            if not items:
                output("Список покупок уже пуст.")
                continue
            confirmation = input_fn("Очистить список покупок? (да/нет): ").strip().lower()
            if confirmation != "да":
                output("Очистка отменена.")
                continue
            items.clear()
            success_message = "Список покупок очищен."
        else:
            output("Неизвестная команда. Выберите пункт от 0 до 4.")
            continue

        try:
            save_items(items, path)
        except OSError as error:
            print(f"Не удалось сохранить список: {error}", file=sys.stderr)
            return 1
        output(success_message)


if __name__ == "__main__":
    raise SystemExit(run())

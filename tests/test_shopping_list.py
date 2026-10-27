import json
import tempfile
import unittest
from pathlib import Path

from main import ShoppingItem, load_items, run, save_items


class ShoppingListTests(unittest.TestCase):
    def test_saves_and_loads_items(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "shopping_list.json"
            items = [ShoppingItem("Молоко"), ShoppingItem("Хлеб", purchased=True)]

            save_items(items, path)

            self.assertEqual(load_items(path), items)

    def test_rejects_malformed_saved_item(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "shopping_list.json"
            path.write_text(json.dumps([{"name": "Молоко"}]), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "некорректная запись"):
                load_items(path)

    def test_adds_marks_and_clears_items(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "shopping_list.json"
            inputs = iter(["1", "Молоко", "3", "1", "2", "4", "да", "0"])
            messages = []

            result = run(path, lambda _prompt: next(inputs), messages.append)

            self.assertEqual(result, 0)
            self.assertIn("Товар «Молоко» добавлен.", messages)
            self.assertIn("Товар «Молоко» отмечен как купленный.", messages)
            self.assertIn("1. [x] Молоко", messages)
            self.assertIn("Список покупок очищен.", messages)
            self.assertEqual(load_items(path), [])


if __name__ == "__main__":
    unittest.main()

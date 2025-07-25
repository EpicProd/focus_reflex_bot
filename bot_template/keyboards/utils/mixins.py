from bot_template.keyboards.models.base import ButtonRow


class KeyboardMarkupMixin:
    def row(self, row: "ButtonRow") -> None:  # type: ignore
        self.rows.append(row)

    def add(self, button: "KeyboardButton") -> None:  # type: ignore
        self.rows[-1].append(button)

    def remove(self, index: int = 0) -> None:
        self.rows.pop(index)

    def serialize(self) -> dict:
        """
        Serializes the entire keyboard to a dictionary format.
        """
        return {
            "type": self.__class__.__name__,  # Include the keyboard type
            "rows": [row.serialize() for row in self.rows],
        }

    @classmethod
    def deserialize(cls, data: dict):
        """
        Deserializes data back into a keyboard object.
        """
        if data["type"] != cls.__name__:
            raise ValueError(f"Incompatible keyboard type: {data['type']}")

        rows = [ButtonRow.deserialize(row_data) for row_data in data["rows"]]
        return cls(*rows)

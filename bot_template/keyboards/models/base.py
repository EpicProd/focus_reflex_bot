from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List


@dataclass
class AbstractDataclass(ABC):
    def __new__(cls, *args, **kwargs):
        if AbstractDataclass in (cls, cls.__bases__[0]):
            raise TypeError("Cannot instantiate abstract class.")
        return super().__new__(cls)


class ButtonRegistry:
    registry = {}

    @classmethod
    def register(cls, button_type, button_class):
        cls.registry[button_type] = button_class

    @classmethod
    def get_class(cls, button_type):
        if button_type in cls.registry:
            return cls.registry[button_type]
        raise ValueError(f"Unknown button type: {button_type}")

    @staticmethod
    def register_buttons():
        import inspect  # pylint: disable=import-outside-toplevel

        from bot_template.keyboards.models import (  # pylint: disable=import-outside-toplevel
            bottom_keyboard,
            inline_keyboard,
            multi_keyboard,
        )

        for module in [bottom_keyboard, inline_keyboard, multi_keyboard]:
            for _, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, BaseKeyboardButton)
                    and obj is not BaseKeyboardButton
                ):
                    ButtonRegistry.register(obj.__name__, obj)


@dataclass(slots=True)
class BaseKeyboardButton(
    AbstractDataclass
):  # pylint: disable=too-many-instance-attributes
    """Base button object"""

    type: str
    text: str
    callback_data: str = field(default=None)
    url: str = field(default=None)
    switch_inline_query: str = field(default=None)
    poll_type: str = field(default=None)
    user_id: int = field(default=None)
    additional_data: dict = field(default=None)

    def __repr__(self) -> str:
        return f"<KeyboardButton type={self.type} text={self.text} at {hex(id(self))}>"  # yapf: disable

    def serialize(self) -> dict:
        return {
            "type": self.type,
            "text": self.text,
            "callback_data": self.callback_data,
            "url": self.url,
            "switch_inline_query": self.switch_inline_query,
            "poll_type": self.poll_type,
            "user_id": self.user_id,
            "additional_data": self.additional_data,
        }

    @classmethod
    def deserialize(cls, data: dict):
        button_class = ButtonRegistry.get_class(data.get("type"))
        return button_class.deserialize(data)

    @abstractmethod
    async def build_button(self, ctx):
        ...


@dataclass(init=False, slots=True)
class ButtonRow:
    buttons: List[BaseKeyboardButton]

    def __init__(self, *args: BaseKeyboardButton):
        self.buttons = list(args)

    def append(self, button: BaseKeyboardButton) -> None:
        self.buttons.append(button)

    def serialize(self) -> list:
        return [button.serialize() for button in self.buttons]

    @classmethod
    def deserialize(cls, data: list) -> "ButtonRow":
        buttons = [
            BaseKeyboardButton.deserialize(button_data) for button_data in data
        ]
        return cls(*buttons)

    def __repr__(self) -> str:
        return f"<ButtonRow object at {hex(id(self))}>"  # yapf: disable

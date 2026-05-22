from telegram import ReplyKeyboardMarkup

from core.constants import WORK_TYPES


def work_type_keyboard() -> ReplyKeyboardMarkup:
    """Small reply keyboard for choosing a preferred work type."""
    keyboard = [
        [WORK_TYPES[0], WORK_TYPES[1]],
        [WORK_TYPES[2], WORK_TYPES[3]],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)

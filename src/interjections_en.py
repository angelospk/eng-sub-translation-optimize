"""Default English interjections list.

Based on SubtitleEdit's en_interjections_se.xml
"""

# Main interjection words (case-insensitive matching will be applied)
INTERJECTIONS_EN: list[str] = [
    "Ah",
    "Ahem",
    "Ahh",
    "Ahhh",
    "Ahhhh",
    "Eh",
    "Ehh",
    "Ehhh",
    "Er",
    "Err",
    "Erm",
    "Gah",
    "Hm",
    "Hmm",
    "Hmmm",
    "Hmmmm",
    "Huh",
    "Mm",
    "Mm-hmm",
    "Mm-hm",
    "Mmm",
    "Mmmm",
    "Nuh-uh",
    "Oh",
    "Ohh",
    "Ohhh",
    "Ow",
    "Oww",
    "Owww",
    "Pff",
    "Pfft",
    "Phew",
    "Tsk",
    "Ugh",
    "Ughh",
    "Uh",
    "Uhh",
    "Uhhh",
    "Uh-huh",
    "Um",
    "Umm",
    "Ummm",
    "Whew",
    "Wow",
]

# Words to skip if the text starts with these (to avoid false positives)
# For example: "Ohm" should not trigger removal of "Oh"
INTERJECTIONS_SKIP_EN: list[str] = [
    "Ohm",
    "Uhura",
    "Uh-oh",  # This is an actual exclamation, not a filler
]

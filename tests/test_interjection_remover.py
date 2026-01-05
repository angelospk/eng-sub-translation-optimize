"""Tests for interjection remover - ported from SubtitleEdit C# tests.

Test cases based on RemoveTextForHearImpairedTest.cs from SubtitleEdit.
"""

import os
import pytest
from src.interjection_remover import InterjectionRemoveContext, RemoveInterjection
from tests.conftest import make_context


class TestBasicRemoval:
    """Basic interjection removal tests."""

    def test_remove_interjections_second_line(self, remover: RemoveInterjection):
        """RemoveInterjections: second line only interjection."""
        text = f"-Ballpark.{os.linesep}-Hmm."
        expected = "Ballpark."
        actual = remover.invoke(make_context(text))
        assert actual == expected

    def test_remove_interjections2(self, remover: RemoveInterjection):
        """RemoveInterjections2: Mm-hm on second line."""
        text = f"-Ballpark.{os.linesep}-Mm-hm."
        expected = "Ballpark."
        actual = remover.invoke(make_context(text))
        assert actual == expected

    def test_remove_interjections3(self, remover: RemoveInterjection):
        """RemoveInterjections3: Mm-hm on first line."""
        text = f"-Mm-hm.{os.linesep}-Ballpark."
        expected = "Ballpark."
        actual = remover.invoke(make_context(text))
        assert actual == expected

    def test_remove_interjections4(self, remover: RemoveInterjection):
        """RemoveInterjections4: with spaces after dash."""
        text = f"- Mm-hm.{os.linesep}- Ballpark."
        expected = "Ballpark."
        actual = remover.invoke(make_context(text))
        assert actual == expected

    def test_remove_interjections5(self, remover: RemoveInterjection):
        """RemoveInterjections5: Hmm on second line."""
        text = f"- Ballpark.{os.linesep}- Hmm."
        expected = "Ballpark."
        actual = remover.invoke(make_context(text))
        assert actual == expected

    def test_remove_interjections6a(self, remover: RemoveInterjection):
        """RemoveInterjections6A: inline removal with comma."""
        text = "Ballpark, mm-hm."
        expected = "Ballpark."
        actual = remover.invoke(make_context(text))
        assert actual == expected

    def test_remove_interjections6b(self, remover: RemoveInterjection):
        """RemoveInterjections6B: interjection at start with comma."""
        text = "Mm-hm, Ballpark."
        expected = "Ballpark."
        actual = remover.invoke(make_context(text))
        assert actual == expected

    def test_remove_interjections6b_italic(self, remover: RemoveInterjection):
        """RemoveInterjections6BItalic: with italic tags."""
        text = "<i>Mm-hm, Ballpark.</i>"
        expected = "<i>Ballpark.</i>"
        actual = remover.invoke(make_context(text))
        assert actual == expected


class TestEndOfSentence:
    """Interjection at end of sentence tests."""

    def test_remove_interjections7(self, remover: RemoveInterjection):
        """RemoveInterjections7: huh at end with question mark."""
        text = "You like her, huh?"
        expected = "You like her?"
        actual = remover.invoke(make_context(text))
        assert actual == expected

    def test_remove_interjections8(self, remover: RemoveInterjection):
        """RemoveInterjections8: huh at end with exclamation."""
        text = "You like her, huh!"
        expected = "You like her!"
        actual = remover.invoke(make_context(text))
        assert actual == expected

    def test_remove_interjections9(self, remover: RemoveInterjection):
        """RemoveInterjections9: huh at end with period."""
        text = "You like her, huh."
        expected = "You like her."
        actual = remover.invoke(make_context(text))
        assert actual == expected

    def test_remove_interjections10(self, remover: RemoveInterjection):
        """RemoveInterjections10: multi-line with huh."""
        text = f"- You like her, huh.{os.linesep}- I do"
        expected = f"- You like her.{os.linesep}- I do"
        actual = remover.invoke(make_context(text))
        assert actual == expected

    def test_remove_interjections10_italic(self, remover: RemoveInterjection):
        """RemoveInterjections10Italic: multi-line with italic tags."""
        text = f"<i>- You like her, huh.{os.linesep}- I do</i>"
        expected = f"<i>- You like her.{os.linesep}- I do</i>"
        actual = remover.invoke(make_context(text))
        assert actual == expected


class TestDialogHandling:
    """Multi-line dialog handling tests."""

    def test_remove_interjections11(self, remover: RemoveInterjection):
        """RemoveInterjections11: both lines have interjections."""
        text = f"- Ballpark, mm-hm.{os.linesep}- Oh yes!"
        expected = f"- Ballpark.{os.linesep}- Yes!"
        actual = remover.invoke(make_context(text))
        assert actual == expected

    def test_remove_hi_quotes(self, remover: RemoveInterjection):
        """RemoveHIQuotes: Ow removal."""
        text = f"- Where?!{os.linesep}- Ow!"
        expected = "Where?!"
        actual = remover.invoke(make_context(text))
        assert actual == expected

    def test_remove_interjections_second_line_start_dialog(self, remover: RemoveInterjection):
        """RemoveInterjectionsSecondLineStartDialog."""
        text = f"-Yes.{os.linesep}-Hm, no."
        expected = f"-Yes.{os.linesep}-No."
        actual = remover.invoke(make_context(text))
        assert actual == expected

    def test_remove_interjections_second_line_start_dialog2(self, remover: RemoveInterjection):
        """RemoveInterjectionsSecondLineStartDialog2."""
        text = f"-and they just covered it up...{os.linesep}-Mm. You know what, we could,"
        expected = f"-and they just covered it up...{os.linesep}-You know what, we could,"
        actual = remover.invoke(make_context(text))
        assert actual == expected

    def test_remove_interjections_first_line_end(self, remover: RemoveInterjection):
        """RemoveInterjectionsFirstLineEnd: Huh at end of first line."""
        text = f"-What say you? Huh?{os.linesep}-Bodie, don't."
        expected = f"-What say you?{os.linesep}-Bodie, don't."
        actual = remover.invoke(make_context(text))
        assert actual == expected

    def test_remove_badly_format_dialog(self, remover: RemoveInterjection):
        """RemoveBadlyFormatDialog: Ah at start."""
        text = f"‐ Ah, dude, she likes you.{os.linesep}What's not to like?"
        expected = f"‐ Dude, she likes you.{os.linesep}What's not to like?"
        actual = remover.invoke(make_context(text))
        assert actual == expected


class TestEmDashHandling:
    """Em-dash (—) handling tests."""

    def test_remove_interjections12(self, remover: RemoveInterjection):
        """RemoveInterjections12: Uh with em-dash."""
        text = "Well, boy, I'm — Uh —"
        expected = "Well, boy, I'm —"
        actual = remover.invoke(make_context(text))
        assert actual == expected

    def test_remove_interjections13(self, remover: RemoveInterjection):
        """RemoveInterjections13: second line only Uh."""
        text = f"- What?{os.linesep}- Uh —"
        expected = "What?"
        actual = remover.invoke(make_context(text))
        assert actual == expected


class TestEllipsisHandling:
    """Ellipsis (...) handling tests."""

    def test_remove_interjections14a(self, remover: RemoveInterjection):
        """RemoveInterjections14A: Uh with ellipsis."""
        text = "Hey! Uh..."
        expected = "Hey!"
        actual = remover.invoke(make_context(text))
        assert actual == expected

    def test_remove_interjections14b(self, remover: RemoveInterjection):
        """RemoveInterjections14B: Uh with ellipsis multi-line."""
        text = f"Hey! Uh...{os.linesep}Bye."
        expected = f"Hey!{os.linesep}Bye."
        actual = remover.invoke(make_context(text))
        assert actual == expected

    def test_remove_interjections15a(self, remover: RemoveInterjection):
        """RemoveInterjections15A: Uh after newline with ellipsis."""
        text = f"I think that...{os.linesep}Uh... Hey!"
        expected = f"I think that...{os.linesep}Hey!"
        actual = remover.invoke(make_context(text))
        assert actual == expected

    def test_remove_interjections15b(self, remover: RemoveInterjection):
        """RemoveInterjections15B: with italic tags."""
        text = f"I think that...{os.linesep}<i>Uh... Hey!</i>"
        expected = f"I think that...{os.linesep}<i>Hey!</i>"
        actual = remover.invoke(make_context(text))
        assert actual == expected

    def test_remove_interjections16(self, remover: RemoveInterjection):
        """RemoveInterjections16: Ah with ellipsis and exclamation."""
        text = "Ah...! Missy, you're a real bitch!"
        expected = "Missy, you're a real bitch!"
        actual = remover.invoke(make_context(text))
        assert actual == expected


class TestBothLinesInterjections:
    """Both dialog lines are interjections tests."""

    def test_remove_interjections17a(self, remover: RemoveInterjection):
        """RemoveInterjections17A: both lines Hm."""
        text = f"- Hm.{os.linesep}- Hm."
        actual = remover.invoke(make_context(text))
        assert actual == ""

    def test_remove_interjections17b(self, remover: RemoveInterjection):
        """RemoveInterjections17B: only separated lines mode."""
        text = f"- Hm.{os.linesep}- Hm."
        actual = remover.invoke(make_context(text, only_separated_lines=True))
        assert actual == ""

    def test_remove_interjections18a(self, remover: RemoveInterjection):
        """RemoveInterjections18A: both lines Hm with exclamation."""
        text = f"- Hm!{os.linesep}- Hm!"
        actual = remover.invoke(make_context(text))
        assert actual == ""

    def test_remove_interjections18b(self, remover: RemoveInterjection):
        """RemoveInterjections18B: only separated lines mode."""
        text = f"- Hm!{os.linesep}- Hm!"
        actual = remover.invoke(make_context(text, only_separated_lines=True))
        assert actual == ""


class TestSpanishPunctuation:
    """Spanish inverted punctuation (¿, ¡) tests."""

    def test_remove_interjections19(self, remover: RemoveInterjection):
        """RemoveInterjections19: Spanish with ¡Hm!"""
        text = f"- ¡Hm!{os.linesep}- Increíble, ¿verdad?"
        expected = "Increíble, ¿verdad?"
        actual = remover.invoke(make_context(text, only_separated_lines=True))
        assert actual == expected

    def test_remove_interjections19b(self, remover: RemoveInterjection):
        """RemoveInterjections19B: Spanish with ¿Hm?"""
        text = f"- ¿Hm?{os.linesep}- Increíble, ¿verdad?"
        expected = "Increíble, ¿verdad?"
        actual = remover.invoke(make_context(text, only_separated_lines=True))
        assert actual == expected


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_string(self, remover: RemoveInterjection):
        """Empty string returns empty."""
        actual = remover.invoke(make_context(""))
        assert actual == ""

    def test_whitespace_only(self, remover: RemoveInterjection):
        """Whitespace only returns original."""
        actual = remover.invoke(make_context("   "))
        assert actual == "   "

    def test_no_interjections(self, remover: RemoveInterjection):
        """Text without interjections unchanged."""
        text = "Hello, how are you today?"
        actual = remover.invoke(make_context(text))
        assert actual == text

    def test_only_interjection(self, remover: RemoveInterjection):
        """Single interjection only returns empty."""
        text = "Hmm."
        actual = remover.invoke(make_context(text))
        assert actual == ""

    def test_case_insensitive(self, remover: RemoveInterjection):
        """Case insensitive matching."""
        text = "UH, hello"
        expected = "Hello"
        actual = remover.invoke(make_context(text))
        assert actual == expected

    def test_preserve_non_interjection_oh(self, remover: RemoveInterjection):
        """Don't remove 'oh' when part of 'ohm'."""
        # This requires skip list functionality
        text = "Ohm resistance is 5"
        # With skip list containing "Ohm", this should be unchanged
        actual = remover.invoke(make_context(text))
        assert actual == text


class TestCapitalization:
    """Capitalization after removal tests."""

    def test_capitalize_after_removal_at_start(self, remover: RemoveInterjection):
        """Capitalize first word after removing sentence-starting interjection."""
        text = "Uh, hello there"
        expected = "Hello there"
        actual = remover.invoke(make_context(text))
        assert actual == expected

    def test_preserve_lowercase_mid_sentence(self, remover: RemoveInterjection):
        """Preserve case when removal is mid-sentence."""
        text = "Well, uh, that's fine"
        expected = "Well, that's fine"
        actual = remover.invoke(make_context(text))
        assert actual == expected


class TestOnlySeparatedLines:
    """OnlySeparatedLines mode tests."""

    def test_only_separated_removes_isolated(self, remover: RemoveInterjection):
        """Only separated lines mode removes isolated interjection line."""
        text = f"-Ballpark.{os.linesep}-Hmm."
        expected = "Ballpark."
        actual = remover.invoke(make_context(text, only_separated_lines=True))
        assert actual == expected

    def test_only_separated_preserves_inline(self, remover: RemoveInterjection):
        """Only separated lines mode preserves inline interjection."""
        text = "Well, hmm, I think so"
        # In only_separated_lines mode, inline interjections should be preserved
        actual = remover.invoke(make_context(text, only_separated_lines=True))
        assert actual == text

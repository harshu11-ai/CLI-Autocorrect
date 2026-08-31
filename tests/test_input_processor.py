import unittest

from cli_autocorrect.input_processor import (
    BRACKETED_PASTE_END,
    BRACKETED_PASTE_START,
    InputProcessor,
)


class InputProcessorTests(unittest.TestCase):
    def test_forwards_normal_typing_unchanged(self) -> None:
        processor = InputProcessor()
        self.assertEqual(processor.feed(b"please "), b"please ")

    def test_rewrites_typo_at_space(self) -> None:
        processor = InputProcessor()
        self.assertEqual(processor.feed(b"teh"), b"teh")
        self.assertEqual(processor.feed(b" "), b"\x7f\x7f\x7fthe ")

    def test_rewrites_when_input_arrives_in_one_chunk(self) -> None:
        processor = InputProcessor()
        self.assertEqual(processor.feed(b"fix teh function"), b"fix teh\x7f\x7f\x7fthe function")

    def test_preserves_punctuation_during_rewrite(self) -> None:
        processor = InputProcessor()
        self.assertEqual(
            processor.feed(b"fix teh, please"),
            b"fix teh,\x7f\x7f\x7f\x7fthe, please",
        )

    def test_immediate_backspace_undoes_correction(self) -> None:
        processor = InputProcessor()
        processor.feed(b"teh ")
        self.assertEqual(processor.feed(b"\x7f"), b"\x7f\x7f\x7f\x7fteh")
        self.assertEqual(processor.feed(b" "), b"\x7f\x7f\x7fthe ")

    def test_editing_word_with_backspace_updates_buffer(self) -> None:
        processor = InputProcessor()
        self.assertEqual(processor.feed(b"tehh\x7f "), b"tehh\x7f\x7f\x7f\x7fthe ")

    def test_path_is_passed_through(self) -> None:
        processor = InputProcessor()
        value = b"src/teh.py "
        self.assertEqual(processor.feed(value), value)

    def test_arrow_key_suspends_correction_until_new_line(self) -> None:
        processor = InputProcessor()
        self.assertEqual(processor.feed(b"\x1b[Ateh "), b"\x1b[Ateh ")
        self.assertEqual(processor.feed(b"\nteh "), b"\nteh\x7f\x7f\x7fthe ")

    def test_terminal_startup_reports_do_not_suspend_correction(self) -> None:
        processor = InputProcessor()
        reports = (
            b"\x1b[24;80R"
            b"\x1b[?1;2c"
            b"\x1b[?0u"
            b"\x1b[I"
            b"\x1b]10;rgb:ffff/ffff/ffff\x07"
        )
        self.assertEqual(
            processor.feed(reports + b"teh "),
            reports + b"teh\x7f\x7f\x7fthe ",
        )

    def test_bracketed_paste_is_never_corrected(self) -> None:
        processor = InputProcessor()
        pasted = BRACKETED_PASTE_START + b"teh fucntion" + BRACKETED_PASTE_END
        self.assertEqual(processor.feed(pasted), pasted)
        self.assertEqual(processor.feed(b" more teh "), b" more teh ")
        self.assertEqual(processor.feed(b"\nteh "), b"\nteh\x7f\x7f\x7fthe ")

    def test_ctrl_c_resets_safe_typing_state(self) -> None:
        processor = InputProcessor()
        processor.feed(b"\x1b[A")
        self.assertEqual(processor.feed(b"teh \x03teh "), b"teh \x03teh\x7f\x7f\x7fthe ")

    def test_tab_is_passed_through_and_suspends_correction(self) -> None:
        processor = InputProcessor()
        self.assertEqual(processor.feed(b"teh\tteh "), b"teh\tteh ")
        self.assertEqual(processor.feed(b"\nteh "), b"\nteh\x7f\x7f\x7fthe ")


if __name__ == "__main__":
    unittest.main()

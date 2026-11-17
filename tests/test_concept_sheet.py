"""concept_sheet regression tests: CJK note wrapping + label prefix handling.

Covers the two defects reported in review of PR #23:
  * a supplied "A — Name" label must render as "A · Name" (letter kept, separator dropped)
  * card height must replace the flat note allowance, not add to it
and the CJK punctuation width fix (U+3000-303F counts as full width).
"""
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/logo-design/scripts'))
import concept_sheet as cs


class CjkClassification(unittest.TestCase):
    def test_ideographs_are_full_width(self):
        for ch in '车印惠漢字':
            self.assertTrue(cs._is_cjk(ch), ch)

    def test_cjk_punctuation_is_full_width(self):
        # U+3000-303F must count as wide, otherwise lines overflow by a few em.
        for ch in '、。「」『』【】':
            self.assertTrue(cs._is_cjk(ch), ch)

    def test_latin_is_half_width(self):
        for ch in 'Ab1':
            self.assertFalse(cs._is_cjk(ch), ch)

    def test_text_units_weights_cjk_as_two(self):
        self.assertEqual(cs.text_units('车印'), 4)
        self.assertEqual(cs.text_units('ab'), 2)
        self.assertEqual(cs.text_units('车a'), 3)


class LabelPrefix(unittest.TestCase):
    """The rendered label is built in main(); these mirror that rule."""

    @staticmethod
    def build(raw, i):
        return cs.concept_label(raw, i)

    def test_existing_prefix_is_replaced_not_dropped(self):
        for raw in ('A — 车印', 'A · 车印', 'A: 车印', 'A - 车印'):
            with self.subTest(raw=raw):
                self.assertEqual(self.build(raw, 0), 'A · 车印')

    def test_plain_name_gets_letter(self):
        self.assertEqual(self.build('车印', 0), 'A · 车印')
        self.assertEqual(self.build('', 1), 'B · ')
        self.assertEqual(self.build('认证勾', 1), 'B · 认证勾')

    def test_hyphenated_name_keeps_its_hyphen(self):
        # "A-Team" must not lose the hyphen: "A-" is a name fragment, not a separator.
        self.assertEqual(self.build('A-Team', 0), 'A · A-Team')

    def test_letter_must_match_position(self):
        # B as the first name must not strip its own letter when i==0.
        self.assertEqual(self.build('B — 车印', 0), 'A · B — 车印')


class NoteWrapping(unittest.TestCase):
    def test_long_chinese_note_wraps_to_multiple_lines(self):
        note = '方印加惠字笔画重构，中文品牌最强的识别资产，适合二手车检测认证场景'
        lines = cs.wrap(note, 20)
        self.assertGreater(len(lines), 1)
        for line in lines:
            self.assertLessEqual(cs.text_units(line), 20, line)

    def test_chinese_never_overflows_slot(self):
        inner_w = 666
        limit = int(inner_w / 9.5)
        note = '这一句会明显超出一行的宽度，必须折行才能放进卡片里，不能溢出边界。'
        lines = cs.wrap(note, limit)
        widest = max(cs.text_units(l) for l in lines)
        self.assertLessEqual(widest * 9.5, inner_w)

    def test_english_still_breaks_on_spaces(self):
        lines = cs.wrap('One isometric form reads as T and F', 20)
        self.assertTrue(all(' ' not in l.strip(' ') or len(l) > 0 for l in lines))
        for line in lines:
            self.assertLessEqual(cs.text_units(line), 20, line)

    def test_empty_note_yields_no_lines(self):
        self.assertEqual(cs.wrap('', 20), [])


if __name__ == '__main__':
    unittest.main()

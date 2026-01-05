"""Interjection removal library for subtitle optimization.

Faithfully ported from SubtitleEdit's RemoveInterjection.cs
https://github.com/SubtitleEdit/subtitleedit
"""

import os
import re
from dataclasses import dataclass, field


@dataclass
class InterjectionRemoveContext:
    """Context for interjection removal operation."""
    text: str
    interjections: list[str]
    interjections_skip_if_starts_with: list[str] = field(default_factory=list)
    only_separated_lines: bool = False


def remove_html_tags(text: str, keep_music_symbols: bool = True) -> str:
    """Remove HTML tags like <i>, </i>, <b>, etc."""
    return re.sub(r'<[^>]+>', '', text)


def has_sentence_ending(text: str) -> bool:
    """Check if text ends with sentence-ending punctuation."""
    if not text:
        return False
    text = text.rstrip()
    return bool(text) and text[-1] in '.!?…'


def capitalize_first_letter(text: str) -> str:
    """Capitalize the first letter of the text."""
    if not text:
        return text
    for i, char in enumerate(text):
        if char.isalpha():
            return text[:i] + char.upper() + text[i+1:]
    return text


def split_to_lines(text: str) -> list[str]:
    """Split text to lines (handles both \r\n and \n)."""
    return text.replace('\r\n', '\n').split('\n')


def get_number_of_lines(text: str) -> int:
    """Get number of lines in text."""
    return len(split_to_lines(text))


def remove_chars(text: str, *chars: str) -> str:
    """Remove specified characters from text."""
    result = text
    for char in chars:
        result = result.replace(char, '')
    return result


class RemoveInterjection:
    """Remove interjection words from subtitle text.
    
    Faithfully ported from SubtitleEdit's RemoveInterjection.cs
    """
    
    def invoke(self, context: InterjectionRemoveContext) -> str:
        """Remove interjections from the given text."""
        if not context.text or context.text.isspace():
            return context.text
        
        text = context.text
        old_text = text
        newline = '\n' if '\r\n' not in text else '\r\n'
        
        do_repeat = True
        while do_repeat:
            do_repeat = False
            for s in context.interjections:
                if s.lower() in text.lower():
                    # Case-insensitive word boundary match
                    regex = re.compile(r'\b' + re.escape(s) + r'\b', re.IGNORECASE)
                    match = regex.search(text)
                    if match:
                        index = match.start()
                        
                        from_index_part = text[match.start():]
                        do_skip = False
                        for skip_if_starts_with in context.interjections_skip_if_starts_with:
                            if from_index_part.lower().startswith(skip_if_starts_with.lower()):
                                do_skip = True
                                break
                        if do_skip:
                            break
                        
                        remove_after = True
                        temp = text[:index] + text[index + len(s):]
                        
                        # Handle "... " at start
                        if index == 0 and temp.startswith('... '):
                            temp = temp[4:]
                        
                        # Handle Spanish punctuation at index 1
                        if index == 1 and temp.startswith('¿, '):
                            temp = temp[0] + temp[3:]
                        
                        if index == 1 and temp.startswith('¿ '):
                            temp = temp[0] + temp[2:]
                        
                        if index == 1 and temp.startswith('¡, '):
                            temp = temp[0] + temp[3:]
                        
                        if index == 1 and temp.startswith('¡ '):
                            temp = temp[0] + temp[2:]
                        
                        if index == 1 and temp.startswith('... '):
                            temp = temp[4:]
                        
                        if index == 3 and temp.startswith('<i>... '):
                            temp = temp[:3] + temp[7:]
                        
                        if index > 2 and len(temp) >= index - 2 + 5 and temp[index-2:].startswith(', ...'):
                            temp = temp[:index-2] + temp[index:]
                            remove_after = False
                        
                        if index > 2 and index - 1 < len(text) and text[index-1] in ' \r\n' and len(temp) > index and temp[index:].startswith('... '):
                            temp = temp[:index] + temp[index+4:]
                        
                        if index > 4 and len(temp) > index - 4 and temp[index-4:].startswith('\n<i>... '):
                            temp = temp[:index] + temp[index+4:]
                        
                        if index > 2 and len(temp) >= index - 2 + 3 and temp[index-2:].startswith('? ?'):
                            temp = temp[:index-2] + temp[index:]
                            remove_after = False
                        
                        if index > 1 and len(temp) >= index - 2 and temp[index-2:] == ', —':
                            temp = temp[:index-2]
                        elif index > 2 and len(temp) > index - 2 and temp[index-2:].startswith('. .'):
                            temp = temp[:index-2] + temp[index:]
                            remove_after = False
                        elif len(temp) > index and temp[index:] == ' —' and temp.endswith('—  —'):
                            temp = temp[:-3]
                            if temp.endswith(newline + '—'):
                                temp = temp[:-1].rstrip()
                        elif len(temp) > index and temp[index:] == ' —' and temp.endswith('-  —'):
                            temp = temp[:-3]
                            if temp.endswith(newline + '-'):
                                temp = temp[:-1].rstrip()
                        elif index == 2 and temp.startswith('-  —'):
                            temp = temp[:2] + temp[4:]
                        elif index == 2 and temp.startswith('- —'):
                            temp = temp[:2] + temp[3:]
                        elif index == 2 and temp.startswith(f'- .{newline}'):
                            temp = temp[:2] + temp[2 + len(f'- .{newline}') - 2:]
                        elif index == 2 and temp.startswith(f'- !{newline}'):
                            temp = temp[:2] + temp[2 + len(f'- !{newline}') - 2:]
                        elif index == 2 and temp.startswith(f'- ?{newline}'):
                            temp = temp[:2] + temp[2 + len(f'- ?{newline}') - 2:]
                        elif index == 0 and temp.startswith(' —'):
                            temp = temp[2:]
                        elif index == 0 and temp.startswith('—'):
                            temp = temp[1:]
                        elif index == 0 and temp.startswith('...! '):
                            temp = temp[5:]
                        elif index == 0 and temp.startswith('...? '):
                            temp = temp[5:]
                        elif index > 3 and len(temp) >= index - 2 and temp[index-2:] in ('.  —', '!  —', '?  —'):
                            temp = temp[:index-2] + temp[index-1:]
                            temp = temp.replace('  ', ' ')
                        elif index > 3 and len(temp) > index - 2 + 4 and temp[index-2:].startswith('\n¿? '):
                            temp = temp[:index-1] + temp[index+2:]
                        elif index > 3 and len(temp) > index - 2 + 4 and temp[index-2:].startswith('\n¡! '):
                            temp = temp[:index-1] + temp[index+2:]
                        elif index > 3 and len(temp) > index - 2 + 4 and temp[index-2:].startswith(' ¿? '):
                            temp = temp[:index-1] + temp[index+2:]
                        elif index > 3 and len(temp) > index - 2 + 4 and temp[index-2:].startswith(' ¡! '):
                            temp = temp[:index-1] + temp[index+2:]
                        elif index > 3 and len(temp) >= index - 2 + 3 and temp[index-2:] == ' ¿?':
                            temp = temp[:index-2]
                        elif index > 3 and len(temp) >= index - 2 + 3 and temp[index-2:] == ' ¡!':
                            temp = temp[:index-2]
                        elif index > 3 and len(temp) == index + 1 and index - 2 < len(temp) and temp[index-2] in '.!?' and temp[index-1] == ' ' and temp[index] in '.!?':
                            temp = temp[:index].rstrip()
                        
                        pre = ''
                        if index > 0:
                            do_repeat = True
                        
                        if index > 2 and len(temp) > index:
                            ending = temp[index-2:index+1]
                            if ending in (', .', ', !', ', ?', ', …'):
                                temp = temp[:index-2] + temp[index:]
                                remove_after = False
                        
                        if remove_after and index > len(s):
                            if len(temp) > index - len(s) + 3:
                                sub_index = index - len(s) + 1
                                sub_temp = temp[sub_index:sub_index+3]
                                if sub_temp in (', !', ', ?', ', .'):
                                    temp = temp[:sub_index] + temp[sub_index+2:]
                                    remove_after = False
                                elif sub_index > 3 and sub_index - 1 < len(temp) and temp[sub_index-1] in '.!?':
                                    sub_temp = temp[sub_index:]
                                    if sub_temp == ' ...' or sub_temp.startswith(' ...' + newline):
                                        temp = (temp[:sub_index] + temp[sub_index+4:]).strip()
                                        remove_after = False
                            
                            if remove_after and len(temp) > index - len(s) + 2:
                                sub_index = index - len(s)
                                if sub_index >= 0 and sub_index + 3 <= len(temp):
                                    sub_temp = temp[sub_index:sub_index+3]
                                    if sub_temp in (', !', ', ?', ', .'):
                                        temp = temp[:sub_index] + temp[sub_index+2:]
                                        remove_after = False
                                    elif sub_temp == ' ¡!':
                                        temp = temp[:sub_index] + temp[sub_index+3:]
                                        remove_after = False
                                    elif sub_temp == ' ¿?':
                                        temp = temp[:sub_index] + temp[sub_index+3:]
                                        remove_after = False
                                    elif index == 1 and temp.startswith('¿?' + newline):
                                        temp = temp[2:].rstrip()
                                        remove_after = False
                                    elif index == 1 and temp.startswith('¡!' + newline):
                                        temp = temp[2:].rstrip()
                                        remove_after = False
                                    else:
                                        sub_temp = temp[sub_index:]
                                        if sub_temp.startswith(', -—'):
                                            temp = temp[:sub_index] + temp[sub_index+3:]
                                            remove_after = False
                                        elif sub_temp.startswith(', --'):
                                            temp = temp[:sub_index] + temp[sub_index+2:]
                                            remove_after = False
                                        elif index > 2 and sub_temp.startswith('-  —'):
                                            temp = temp[:sub_index+2] + temp[sub_index+4:]
                                            temp = temp.replace('  ', ' ')
                                            remove_after = False
                            
                            if remove_after and len(temp) > index - len(s) + 2:
                                skip_due_to_after_newline = False
                                if index - len(s) > 2 and index - len(s) < len(temp) and temp[index - len(s)] in '\r\n':
                                    skip_due_to_after_newline = True
                                
                                if not skip_due_to_after_newline:
                                    sub_index = index - len(s) + 1
                                    
                                    if sub_index >= 0 and sub_index + 2 <= len(temp):
                                        sub_temp = temp[sub_index:sub_index+2]
                                        if sub_temp in ('-!', '-?', '-.'):
                                            temp = temp[:sub_index] + temp[sub_index+1:]
                                            remove_after = False
                                        
                                        sub_temp = temp[sub_index:]
                                        if sub_temp in (' !', ' ?', ' .'):
                                            temp = temp[:sub_index] + temp[sub_index+1:]
                                            remove_after = False
                        
                        if index > 3 and index - 2 < len(temp):
                            sub_temp = temp[index-2:]
                            if sub_temp.startswith(',  —') or sub_temp.startswith(', —'):
                                temp = temp[:index-2] + temp[index-1:]
                                index -= 1
                            
                            if sub_temp.startswith('- ...'):
                                remove_after = False
                        
                        if index == 1 and temp.startswith('¿?'):
                            remove_after = False
                            temp = temp[2:].lstrip()
                        elif index == 1 and temp.startswith('¡!'):
                            remove_after = False
                            temp = temp[2:].lstrip()
                        
                        if remove_after:
                            if index == 0:
                                if temp.startswith('-'):
                                    temp = temp[1:].strip()
                            elif index == 3 and temp.startswith('<i>-'):
                                temp = temp[:3] + temp[4:]
                            elif index > 0 and len(temp) > index:
                                pre = text[:index]
                                temp = temp[index:]
                                
                                if temp.startswith('-') and pre.endswith('-'):
                                    temp = temp[1:]
                                
                                if temp.startswith('-') and pre.endswith('- '):
                                    temp = temp[1:]
                            
                            if temp.startswith('...'):
                                pre = pre.strip()
                            else:
                                while len(temp) > 0 and temp[0] in ' ,.?!':
                                    temp = temp[1:]
                                    do_repeat = True
                                
                                temp = temp.lstrip()
                            
                            pre_no_tags = remove_html_tags(pre, True).strip()
                            if len(temp) > 0 and (
                                len(pre_no_tags) == 0 or
                                pre_no_tags == '-' or
                                pre_no_tags == '‐' or  # weird dash
                                pre_no_tags == '' or
                                pre_no_tags.endswith('¡') or
                                pre_no_tags.endswith('¿') or
                                pre_no_tags.endswith('. -') or
                                pre_no_tags.endswith('! -') or
                                pre_no_tags.endswith('? -') or
                                pre_no_tags.endswith(newline + '-') or
                                (has_sentence_ending(pre_no_tags) and temp[0].lower() == temp[0]) or
                                temp[0] == '¡' or temp[0] == '¿'
                            ):
                                if temp[0] != '¡' and temp[0] != '¿':
                                    temp = temp[0].upper() + temp[1:]
                                
                                if temp[0] == '¡' and len(temp) > 1:
                                    temp = '¡' + capitalize_first_letter(temp.lstrip('¡'))
                                elif temp[0] == '¿' and len(temp) > 1:
                                    temp = '¿' + capitalize_first_letter(temp.lstrip('¿'))
                                
                                do_repeat = True
                            
                            if temp.startswith('-') and pre.endswith(' '):
                                temp = temp[1:]
                            
                            if temp.startswith('—') and pre.endswith(','):
                                pre = pre.rstrip(',') + ' '
                            
                            temp = pre + temp
                        
                        if temp.endswith(newline + '- '):
                            temp = temp[:-2].rstrip()
                        
                        # Check if stripped text is empty (StrippableText equivalent)
                        stripped = remove_html_tags(temp).strip()
                        stripped = stripped.strip('♪♫-–—‐…""\'')
                        if not stripped:
                            return ''
                        
                        if temp.startswith('-') and newline not in temp and newline in text:
                            temp = temp[1:].strip()
                        
                        text = temp
        
        line_index_removed = -1
        lines = split_to_lines(text)
        if len(lines) == 2 and text != old_text:
            if lines[0] == '-' and lines[1] == '-':
                return ''
            
            if lines[0] == '- …' and lines[1].startswith('-'):
                return lines[1][1:].strip()
            
            if lines[1] == '- …' and lines[0].startswith('-'):
                return lines[0][1:].strip()
            
            if len(lines[0]) > 1 and lines[0][0] == '-' and lines[1].strip() == '-':
                old_first_line = split_to_lines(old_text)[0]
                if context.only_separated_lines and len(old_first_line) > 1 and old_first_line[0] == '-':
                    lines[0] = old_first_line
                return lines[0][1:].strip()
            
            if len(lines[1]) > 1 and lines[1][0] == '-' and lines[0].strip() == '-':
                old_second_line = split_to_lines(old_text)[1]
                if context.only_separated_lines and len(old_second_line) > 1 and old_second_line[0] == '-':
                    lines[1] = old_second_line
                return lines[1][1:].strip()
            
            if len(lines[1]) > 4 and lines[1].startswith('<i>-') and lines[0].strip() == '-':
                old_second_line = split_to_lines(old_text)[1]
                if context.only_separated_lines and len(old_second_line) > 1 and old_second_line.startswith('<i>-'):
                    lines[1] = old_second_line
                return '<i>' + lines[1][4:].strip()
            
            if len(lines[0]) > 1 and (lines[1] == '-' or lines[1] == '.' or lines[1] == '!' or lines[1] == '?'):
                old_first_line = split_to_lines(old_text)[0]
                if context.only_separated_lines and len(old_first_line) > 1 and (lines[1] == '-' or lines[1] == '.' or lines[1] == '!' or lines[1] == '?'):
                    lines[0] = old_first_line
                
                if lines[0].startswith('-') and (newline + '-') in old_text:
                    lines[0] = lines[0][1:]
                
                return lines[0].strip()
            
            no_tags0 = remove_html_tags(lines[0]).strip()
            no_tags1 = remove_html_tags(lines[1]).strip()
            if no_tags0 == '-':
                if no_tags1 == no_tags0:
                    return ''
                
                if len(lines[1]) > 1 and lines[1][0] == '-':
                    return lines[1][1:].strip()
                
                if len(lines[1]) > 4 and lines[1].startswith('<i>-'):
                    return '<i>' + lines[1][4:].strip()
                
                return lines[1]
            
            if no_tags1 == '-':
                if len(lines[0]) > 1 and lines[0][0] == '-':
                    return lines[0][1:].strip()
                
                if len(lines[0]) > 4 and lines[0].startswith('<i>-'):
                    if '</i>' not in lines[0] and '</i>' in lines[1]:
                        return '<i>' + lines[0][4:].strip() + '</i>'
                    
                    return '<i>' + lines[0][4:].strip()
                
                return lines[0]
        
        if len(lines) == 2:
            if not remove_chars(lines[1], '.', '?', '!', '-', '—').strip():
                text = lines[0]
                lines = split_to_lines(text)
                line_index_removed = 1
            elif not remove_chars(lines[0], '.', '?', '!', '-', '—').strip():
                text = lines[1]
                lines = split_to_lines(text)
                line_index_removed = 0
        
        if len(lines) == 1 and text != old_text and get_number_of_lines(old_text) == 2:
            if (old_text.startswith('-') or old_text.startswith('<i>-')) and (
                '.' + newline in old_text or '.</i>' + newline in old_text or
                '!' + newline in old_text or '!</i>' + newline in old_text or
                '?' + newline in old_text or '?</i>' + newline in old_text):
                if text.startswith('<i>-'):
                    text = '<i>' + text[4:].lstrip()
                else:
                    text = text.lstrip('-').lstrip()
            elif ((newline + '-') in old_text or (newline + '<i>-') in old_text) and (
                '.' + newline in old_text or '.</i>' + newline in old_text or
                '!' + newline in old_text or '!</i>' + newline in old_text or
                '?' + newline in old_text or '?</i>' + newline in old_text):
                if text.startswith('<i>-'):
                    text = '<i>' + text[4:].lstrip()
                else:
                    text = text.lstrip('-').lstrip()
        
        if old_text != text:
            text = text.replace(newline + '<i>' + newline, newline + '<i>')
            text = text.replace(newline + '</i>' + newline, '</i>' + newline)
            if text.startswith('<i>' + newline):
                text = '<i>' + text[3 + len(newline):]
            
            if text.endswith(newline + '</i>'):
                text = text[:-(len(newline) + 4)] + '</i>'
            
            text = text.replace(newline + '</i>' + newline, '</i>' + newline)
            
            if context.only_separated_lines:
                if not text:
                    return text
                
                old_lines = split_to_lines(old_text)
                new_lines = split_to_lines(text)
                if len(old_lines) == 2 and len(new_lines) == 1 and (
                    old_lines[0].lstrip(' -') == new_lines[0] or 
                    old_lines[1].lstrip(' -') == new_lines[0]):
                    return text
                
                if line_index_removed == 0:
                    return self._remove_start_dash_single_line(old_lines[1])
                
                if line_index_removed == 1:
                    return self._remove_start_dash_single_line(old_lines[0])
                
                return old_text
        
        if '  ' not in old_text:
            while '  ' in text:
                text = text.replace('  ', ' ')
        
        return text
    
    def _remove_start_dash_single_line(self, input_text: str) -> str:
        """Remove starting dash from a single line."""
        if not input_text:
            return input_text
        
        s = input_text
        if s[0] == '-':
            return s.lstrip('-').lstrip()
        
        pre = ''
        if s.startswith('{\\') and '}' in s:
            idx = s.index('}')
            pre = s[:idx + 1]
            s = s[idx + 1:].lstrip()
        
        if s.lower().startswith('<i>'):
            pre += '<i>'
            s = s[3:].lstrip()
        
        if s.lower().startswith('<font>'):
            pre += '<font>'
            s = s[6:].lstrip()
        
        return pre + s.lstrip('-').lstrip()

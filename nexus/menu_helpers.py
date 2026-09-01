from typing import List, Any, Dict, Optional, Union
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.separator import Separator
from InquirerPy.utils import InquirerPyStyle
from nexus.ui_helpers import pad_visual, C_MUTED, C_SAFE, C_WARN

# High-Tech Cyberpunk & Glassmorphism Theme
_NEXUS_STYLE_DICT = {
    "questionmark": "#00f0ff bold",
    "answermark": "#10b981 bold",
    "answer": "#00f0ff bold",
    "input": "white",
    "question": "bold white",
    "instruction": "#94a3b8 italic",
    "pointer": "#00f0ff bold",
    "checkbox": "#10b981 bold",
    "separator": "#6366f1",
    "skipped": "#94a3b8",
    "validator": "#ef4444",
    "marker": "#f59e0b bold",
    "fuzzy_prompt": "#c084fc",
    "fuzzy_info": "#94a3b8",
    "fuzzy_border": "#6366f1",
    "fuzzy_match": "#00f0ff bold underline",
}
NEXUS_STYLE = InquirerPyStyle(_NEXUS_STYLE_DICT)

# Same theme, but the question/pointer accent turns red — used for
# confirmations on irreversible/destructive actions (kill, uninstall, prune)
# so the risk level is legible before the user even reads the text.
NEXUS_STYLE_DANGER = InquirerPyStyle({
    **_NEXUS_STYLE_DICT,
    "questionmark": "#ef4444 bold",
    "answermark": "#ef4444 bold",
    "answer": "#ef4444 bold",
    "pointer": "#ef4444 bold",
})

def _bind_escape_to_cancel(prompt):
    """Make Esc behave exactly like the existing q/Ctrl+Z cancel path
    (InquirerPy's built-in "skip" handler — returns None/False because every
    prompt here is created with mandatory=False). Esc is the universal
    "back/cancel" key in terminal UIs; q alone isn't discoverable."""
    @prompt.register_kb("escape")
    def _(event):
        prompt._handle_skip(event)
    return prompt

def format_menu_item(icon: str, title: str, desc: str = "", title_width: int = 30, divider: str = "│") -> str:
    """Format a menu choice with clean icon separation and exact column alignment."""
    # Strip variation selector to avoid emoji width glitches in terminal
    clean_icon = icon.replace('\ufe0f', '').strip()
    padded_title = pad_visual(title, title_width)
    if desc:
        return f"{clean_icon}  {padded_title} {divider}  {desc}"
    return f"{clean_icon}  {padded_title}"

def select_menu(
    message: str,
    choices: List[Union[Choice, str, Dict[str, Any], Separator]],
    default: Optional[Any] = None,
    pointer: str = " ❯ "
) -> Any:
    """Prompt user with an arrow-key single select menu."""
    try:
        formatted_choices = []
        for c in choices:
            if isinstance(c, dict):
                formatted_choices.append(Choice(value=c.get("value"), name=c.get("name", str(c.get("value")))))
            elif isinstance(c, Separator) or isinstance(c, Choice):
                formatted_choices.append(c)
            else:
                formatted_choices.append(Choice(value=c, name=str(c)))

        prompt = inquirer.select(
            message=message,
            choices=formatted_choices,
            default=default,
            pointer=pointer,
            style=NEXUS_STYLE,
            instruction="(↑/↓: Gezin • Enter: Seç • Esc: Geri)",
            qmark="⚡",
            amark="✓",
            mandatory=False
        )
        return _bind_escape_to_cancel(prompt).execute()
    except (KeyboardInterrupt, EOFError):
        return None

def checkbox_menu(
    message: str,
    choices: List[Union[Choice, str, Dict[str, Any], Separator]],
    pointer: str = " ❯ "
) -> List[Any]:
    """Prompt user with an arrow-key multi-select checkbox menu."""
    try:
        formatted_choices = []
        for c in choices:
            if isinstance(c, dict):
                formatted_choices.append(Choice(
                    value=c.get("value"),
                    name=c.get("name", str(c.get("value"))),
                    enabled=c.get("enabled", False)
                ))
            elif isinstance(c, Separator) or isinstance(c, Choice):
                formatted_choices.append(c)
            else:
                formatted_choices.append(Choice(value=c, name=str(c)))

        prompt = inquirer.checkbox(
            message=message,
            choices=formatted_choices,
            pointer=pointer,
            style=NEXUS_STYLE,
            instruction="(↑/↓: Gezin • Space: İşaretle • a: Tümü • Enter: Onayla • Esc: İptal)",
            qmark="⚡",
            amark="✓",
            mandatory=False
        )
        res = _bind_escape_to_cancel(prompt).execute()
        return res if res is not None else []
    except (KeyboardInterrupt, EOFError):
        return []

def confirm_menu(message: str, default: bool = True, danger: bool = False) -> bool:
    """Prompt user with an arrow-key / prompt confirmation.

    Set danger=True for irreversible/destructive actions (kill -9, app +
    residual uninstall, docker prune): it switches to the red accent style
    and prefixes the message with a warning glyph, so risk is visible at a
    glance rather than only in the wording."""
    try:
        style = NEXUS_STYLE_DANGER if danger else NEXUS_STYLE
        qmark = "⚠" if danger else "?"
        text = f"DİKKAT (geri alınamaz): {message}" if danger else message
        prompt = inquirer.confirm(
            message=text,
            default=default,
            style=style,
            qmark=qmark,
            amark="✓",
            instruction="(Enter / y / n • Esc: Hayır)",
            mandatory=False
        )
        # confirm's own Esc/skip path resolves to None; coerce to the
        # documented bool contract so `confirm_menu(...) == False` (not just
        # falsy-truthiness) holds for every caller.
        return bool(_bind_escape_to_cancel(prompt).execute())
    except (KeyboardInterrupt, EOFError):
        return False

"""Internationalization support for Officeboy."""

import gettext
import locale
from pathlib import Path


def get_text(message: str) -> str:
    """Get translated text for the given message.
    
    This is a wrapper around gettext.gettext that handles
    the setup of the translation domain and locale directory.
    
    Args:
        message: The message to translate.
        
    Returns:
        The translated message, or the original if no translation
        is available.
    """
    try:
        # Determine locale directory
        localedir = Path(__file__).parent
        
        # Try to get system locale
        system_locale, _ = locale.getdefaultlocale()
        
        # Setup translation
        translation = gettext.translation(
            "messages",
            localedir=str(localedir),
            languages=[system_locale] if system_locale else None,
            fallback=True,
        )
        
        return translation.gettext(message)
    except Exception:
        # Fallback to original message if any error occurs
        return message

class FontError(Exception):
    """Base class for font-related errors."""
    pass

class FontNotFoundError(FontError):
    """Raised when a font file or definition cannot be found."""
    pass

class FontLoadingError(FontError):
    """Raised when a font file can be found but cannot be loaded or parsed."""
    pass

class InvalidFontFileError(FontLoadingError):
    """Raised specifically if the font file is invalid or corrupted."""
    pass

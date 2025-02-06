from enum import IntEnum, StrEnum, auto


class ChatMode(StrEnum):
    ORDINARY = "Ordinary"
    RAG = "RAG"


class Model(StrEnum):
    DEEPSEEK = "deepseek-r1:1.5b"
    LLAMA = "llama3.2:1b"


class Embedding(StrEnum):
    NOMIC = "nomic-embed-text"
    MXBAI = "mxbai-embed-large"


# TODO: add more file types
class FileType(StrEnum):
    TXT = auto()
    PDF = auto()
    DOCX = auto()
    CSV = auto()


class DocSplitterDefaultArgs(IntEnum):
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200


CHROMA_DB_PERSISTENT_DIR = "./db"
NOTIFICATION_DURATION = None

type Error = str | None
type Success = str

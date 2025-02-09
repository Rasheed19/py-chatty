from enum import IntEnum, StrEnum, auto


# TODO: add more light-weight ollama models
class Model(StrEnum):
    DEEPSEEK = "deepseek-r1:1.5b"
    LLAMA = "llama3.2:1b"


# TODO: add more file types
class FileType(StrEnum):
    TXT = auto()
    PDF = auto()
    DOCX = auto()
    CSV = auto()


class DocSplitterDefaultArgs(IntEnum):
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200


class MessageFormat(StrEnum):
    OLLAMA = auto()
    LANGCHAIN = auto()


OLLAMA_EMBEDDING_NAME = "nomic-embed-text"
CHROMA_DB_PERSISTENT_DIR = "./db"
NOTIFICATION_DURATION = 5

type Error = str | None

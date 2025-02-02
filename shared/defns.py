from enum import StrEnum, auto


class ChatMode(StrEnum):
    ORDINARY = "Ordinary"
    RAG = "RAG"


class Model(StrEnum):
    DEEPSEEK = "deepseek-r1:1.5b"
    LLAMA = "llama3.2:1b"


class Embedding(StrEnum):
    NOMIC = "nomic-embed-text"
    MXBAI = "mxbai-embed-large"


class FileType(StrEnum):
    PDF = auto()

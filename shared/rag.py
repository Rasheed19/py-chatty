from typing import Any

import chromadb
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_chroma import Chroma
from langchain_community.document_loaders import (
    CSVLoader,
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
)
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableSerializable
from langchain_ollama.chat_models import ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter

from shared.defns import DocSplitterDefaultArgs, Error, FileType


def load_docs(paths: list[str]) -> tuple[list[Document], Error]:
    docs = []

    for p in paths:
        ftype = p.split(".")[-1]

        match ftype:
            case FileType.TXT:
                loader = TextLoader(file_path=p)

            case FileType.CSV:
                loader = CSVLoader(file_path=p)

            case FileType.PDF:
                loader = PyPDFLoader(file_path=p)

            case FileType.DOCX:
                loader = Docx2txtLoader(file_path=p)

            case _:
                return (
                    list(),
                    f"invalid file type, chatty only supports {', '.join(FileType)}",
                )

        docs.extend(loader.load())

    return docs, None


def split_docs(
    docs: list[Document],
    chunk_size: int = DocSplitterDefaultArgs.CHUNK_SIZE,
    chunk_overlap: int = DocSplitterDefaultArgs.CHUNK_OVERLAP,
) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    chunks = splitter.split_documents(docs)

    return chunks


# def create_embedding(model: str) -> OllamaEmbeddings:
#     embedding = OllamaEmbeddings(model=model)

#     return embedding


def create_retrieval(
    model: str,
    # embedding: OllamaEmbeddings,
    client: chromadb.ClientAPI,
    collection_name: str,
) -> tuple[ChatOllama, MultiQueryRetriever]:
    db = Chroma(
        client=client,
        collection_name=collection_name,
        # embedding_function=embedding,
    )

    llm = ChatOllama(model=model)

    QUERY_PROMPT = PromptTemplate(
        input_variables=["question"],
        template="""You are an AI language model assistant. Your task is to use
        user question to retrieve relevant documents from a vector database.
        By generating multiple perspectives on the user question, your goal is to
        help the user overcome some of the limitations of the distance-based similarity
        search. Provide these alternative questions separated by newlines.
        Original question: {question}""",
    )

    # maybe customize params of as_retriever??
    retriever = MultiQueryRetriever.from_llm(
        db.as_retriever(), llm, prompt=QUERY_PROMPT
    )

    return llm, retriever


def validate_splitter_args(arg: Any):
    return isinstance(arg, int) and arg > 0


def create_chain(
    llm: ChatOllama, retriever: MultiQueryRetriever
) -> RunnableSerializable:
    # TODO: update this prompt, use the template in the youtube video
    template = """Answer the questuion based ONLY on the following context:
    {context}
    Question: {question}
    """

    prompt = ChatPromptTemplate.from_template(template=template)

    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain

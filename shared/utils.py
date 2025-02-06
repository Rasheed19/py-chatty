import uuid
from dataclasses import asdict, dataclass
from datetime import datetime

import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

from shared.defns import CHROMA_DB_PERSISTENT_DIR, Error


@dataclass(frozen=True)
class CollectionDescription:
    name: str | None = None
    description: str | None = None
    date_created: str | None = None
    tag: str | None = None
    num_chunks: int | None = None


@dataclass(frozen=True)
class CollectionMetadata:
    description: str | None
    date_created: str | None = None
    tag: str | None = None


class CollectionClient:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=CHROMA_DB_PERSISTENT_DIR)

    def list_collections(self) -> list[str]:
        return self.client.list_collections()

    def get_collection(self, name: str) -> tuple[chromadb.Collection, Error]:
        try:
            collection = self.client.get_collection(name=name)
        except Exception as err:
            return None, repr(err)

        return collection, None

    def create_collection(
        self,
        name: str,
        description: str = None,
    ) -> Error:
        metadata = asdict(
            CollectionMetadata(
                description=description,
                date_created=datetime.now().strftime("%Y-%m-%d-%H-%M-%S"),
                tag=f"collection-{str(uuid.uuid4())}-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}",
            )
        )

        try:
            _ = self.client.create_collection(
                name=name,
                metadata=metadata,
                get_or_create=False,
            )
        except Exception as err:
            return repr(err)

        return None

    def delete_collection(self, name: str) -> Error:
        try:
            _ = self.client.delete_collection(name=name)

        except Exception as err:
            return repr(err)

        return None

    def add_documents(
        self,
        collection_name: str,
        documents: list[str | Document],
        ollama_embedding_name: str,
        description: str | None,
    ) -> Error:
        # since our documents will be a list of chunks obtained from a text splitter; it is
        # necessary to have a single tag for all the documents in the list.
        # collection, err = self.get_collection(name=collection_name)
        # if err is not None:
        #     return f"Error fetching collection with name {collection_name}. More info: {err}"

        uuids = [str(uuid.uuid4()) for _ in range(len(documents))]
        metadata = asdict(
            CollectionMetadata(
                description=description,
                date_created=datetime.now().strftime("%Y-%m-%d-%H-%M-%S"),
                tag=f"document-{str(uuid.uuid4())}-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}",
            )
        )  # here, this metadata is tagged to the whole docs

        # _ = collection.add(
        #     documents=documents, ids=uuids, metadatas=[metadata] * len(documents), embeddings=embedding_functions.OllamaEmbeddingFunction(model_name=model_name)
        # )

        # chroma object from langchain is used here because documents is of type lanchain Document;
        # it will also integrate with retriever well
        db = Chroma(
            client=self.client,
            collection_name=collection_name,
            embedding_function=OllamaEmbeddings(model=ollama_embedding_name),
        )

        try:
            _ = db.add_documents(
                documents=documents,
                ids=uuids,
                metadata=metadata,
            )
        except Exception as err:
            return f"Error in adding documents to {collection_name} collection. More info: {err}"

        return None

    def delete_documents(self, collection_name: str, tag: str) -> Error:
        collection, err = self.get_collection(name=collection_name)
        if err is not None:
            return f"Error fetching collection with name {collection_name}. More info: {err}"

        try:
            _ = collection.delete(where={"tag": tag})

        except Exception as err:
            return repr(err)

        return None

    def describe_collection(
        self, collection_name: str
    ) -> tuple[CollectionDescription, Error]:
        collection, err = self.get_collection(name=collection_name)
        if err is not None:
            return (
                CollectionDescription(),
                f"Error fetching collection with name {collection_name}. More info: {err}",
            )

        metadata = collection.metadata

        return CollectionDescription(
            name=collection.name,
            description=metadata["description"],
            date_created=metadata["date_created"],
            tag=metadata["tag"],
            num_chunks=collection.count(),
        ), None

    # TODO: find a way of updating

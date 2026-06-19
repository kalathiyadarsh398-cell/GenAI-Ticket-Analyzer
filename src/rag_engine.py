import chromadb
from pathlib import Path

# Create ChromaDB database
client = chromadb.PersistentClient(path="chroma_db")

# Create collection
collection = client.get_or_create_collection(name="policies")


def load_policies():

    if collection.count() > 0:
        print("Policies already loaded")
        return

    policy_folder = Path("data/knowledge_base")

    for file in policy_folder.glob("*.md"):

        text = file.read_text(encoding="utf-8")

        collection.add(
            documents=[text],
            ids=[file.stem]
        )

    print("Policies Loaded Successfully")


def search_policy(query):

    results = collection.query(
        query_texts=[query],
        n_results=1
    )

    return results["documents"][0][0]


# Load policies when this file is imported
load_policies()

if __name__ == "__main__":

    # Load policy files into ChromaDB
    load_policies()

    # Test search
    query = "I was charged twice for my subscription"

    result = search_policy(query)

    print("\nSearch Query:")
    print(query)

    print("\nMatched Policy:")
    print(result)
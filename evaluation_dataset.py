# from datasets import Dataset
# from langchain_community.document_loaders import PyPDFLoader
# from langchain_text_splitters import RecursiveCharacterTextSplitter


# # data = {
# #     "question": [
# #         "How do I activate roaming?",
# #         "Why is my SIM not detecting network?",
# #     ],
# #     "ground_truth": [
# #         "Roaming can be activated from telecom settings or support.",
# #         "Restart device and manually select network operator.",
# #     ]
# # }

# # dataset = Dataset.from_dict(data)

# # print(dataset)



# #from ragas import Dataset

# # def load_dataset():
# #     """Load test dataset for evaluation."""
# #     dataset = Dataset(
# #         name="test_dataset",
# #         backend="local/csv",
# #         root_dir="data",
# #     )

# #     data_samples = [
# #         {
# #             "question": "What is Ragas?",
# #             "grading_notes": "Ragas is an evaluation framework for LLM applications",
# #         },
# #         {
# #             "question": "How do metrics work?",
# #             "grading_notes": "Metrics evaluate the quality and performance of LLM responses",
# #         },
# #         # Add more test cases here
# #     ]

# #     for sample in data_samples:
# #         dataset.append(sample)

# #     dataset.save()
# #     return dataset


# def load_dataset():

#     # Load PDF
#     loader = PyPDFLoader("data/telecom_guide.pdf")
#     documents = loader.load()

#     # Split into chunks
#     text_splitter = RecursiveCharacterTextSplitter(
#         chunk_size=600,
#         chunk_overlap=100
#     )

#     docs = text_splitter.split_documents(documents)

#     # Example evaluation questions
#     questions = [
#         "How can I activate international roaming?",
#         "What should I do if my SIM card is not detected?"
#     ]

#     # Example ground truth answers
#     ground_truths = [
#         "International roaming can be activated from the telecom app or customer support.",
#         "Reinsert the SIM card and restart the device. Contact support if the issue continues."
#     ]

#     # Use PDF chunks as contexts
#     contexts = [
#         [docs[0].page_content],
#         [docs[1].page_content]
#     ]

#     # Example generated answers
#     answers = [
#         "You can activate roaming using the telecom mobile app.",
#         "Try reinserting the SIM card and rebooting the device."
#     ]

#     dataset = Dataset.from_dict({
#         "question": questions,
#         "ground_truth": ground_truths,
#         "answer": answers,
#         "contexts": contexts
#     })

#     return dataset


# if __name__ == "__main__":
#     dataset = load_dataset()
#     print(dataset)

from datasets import Dataset
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_dataset():

    # Load PDF
    loader = PyPDFLoader("data/telecom_guide.pdf")
    documents = loader.load()

    print(f"Loaded {len(documents)} pages")

    # Split PDF into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=200
    )

    docs = text_splitter.split_documents(documents)
    print(f"Created {len(docs)} chunks")
    for i, doc in enumerate(docs[:10]):
        print(f"\nCHUNK {i}")
        print(doc.page_content[:300])

        print(f"Created {len(docs)} chunks")

    questions = [
        # "How can I activate international roaming?",
        # "What should I do if my SIM card is not detected?"
        "I have a billing dispute",
        "My phone support VoLTE but Sim shows VoLTE disabled"
    ]

    # Ground truth answers
    ground_truths = [
        "what type of plans do you have ",
        "Agents can push the VoLTE profile remotely via the subscriber management system"
    ]

    # Use PDF chunks as context
    contexts = [
        [docs[0].page_content],
        [docs[1].page_content]
    ]

    # Example generated answers
    answers = [
        "Each  plan  includes  a  fixed  high-speed  data  allowance",
        "Try reinserting the SIM card and rebooting the device."
    ]

    dataset = Dataset.from_dict({
        "question": questions,
        "ground_truth": ground_truths,
        "answer": answers,
        "contexts": contexts
    })

    return dataset


if __name__ == "__main__":

    dataset = load_dataset()

    print("\nDATASET:")
    print(dataset)

    print("\nFIRST RECORD:")
    print(dataset[0])

    print("\nCONTEXT SAMPLE:")
    print(dataset[0]["contexts"])
from clinicalbridge.config import Settings
from clinicalbridge.data_repository import DataRepository
from clinicalbridge.retrieval import LexicalEHRRetriever


def test_lexical_retrieval_is_patient_scoped():
    repository = DataRepository(Settings(mode="offline", openai_api_key=""))
    retriever = LexicalEHRRetriever(repository)
    results = retriever.search("P003", "heart failure dry weight edema diuretic", 6)
    assert results
    assert all(item["metadata"]["patient_id"] == "P003" for item in results)
    assert any(item["source_id"] == "ehr:P003:note:1" for item in results)

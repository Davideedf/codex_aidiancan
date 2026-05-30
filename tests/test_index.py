from app.rag.index import KnowledgeIndex


def test_index_adds_and_searches_chinese_document(tmp_path):
    index = KnowledgeIndex(tmp_path / "index.json")
    info = index.add_document("员工报销制度.md", "员工报销需要发票、审批单和付款凭证。")

    results = index.search("报销需要什么材料")

    assert info["chunks"] == 1
    assert results
    assert results[0].title == "员工报销制度.md"
    assert "发票" in results[0].text


def test_index_persists_documents(tmp_path):
    path = tmp_path / "index.json"
    index = KnowledgeIndex(path)
    index.add_document("安全规范.md", "密钥不得写入代码仓库。")

    reloaded = KnowledgeIndex(path)

    assert reloaded.list_documents()[0]["title"] == "安全规范.md"

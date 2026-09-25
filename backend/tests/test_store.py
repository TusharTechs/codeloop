from codeloop.store import Store


def test_hash_chain_detects_tampering() -> None:
    s = Store(":memory:")
    s.create_code("c1", "live", None)
    s.append("c1", "event", {"kind": "order", "drug": "amiodarone", "dose": 300}, 58.0)
    s.append("c1", "event", {"kind": "ack", "drug": "amiodarone", "dose": 150}, 61.0)
    s.append("c1", "prompt", {"text": "Check dose."}, 61.1)
    assert s.verify("c1") == (True, None)
    # Someone edits the record to hide the conflicting read-back.
    s._db.execute(
        "UPDATE audit SET payload=? WHERE code_id='c1' AND seq=2", ('{"dose":300,"drug":"amiodarone","kind":"ack"}',)
    )
    assert s.verify("c1") == (False, 2)


def test_chain_continues_after_reopen(tmp_path) -> None:
    db = tmp_path / "x.db"
    s = Store(db)
    s.create_code("c1", "replay", "vf")
    s.append("c1", "event", {"a": 1})
    s.close()
    s2 = Store(db)
    e = s2.append("c1", "event", {"a": 2})
    assert e.seq == 2
    assert s2.verify("c1") == (True, None)
    assert [x.payload for x in s2.entries("c1")] == [{"a": 1}, {"a": 2}]
    assert s2.get_code("c1")["scenario"] == "vf"

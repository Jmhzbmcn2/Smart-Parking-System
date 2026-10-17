from mocks.update_test_cases import tc_id


def test_tc_id_mapping():
    assert tc_id("test_tc08_fee_3h10m_is_40000") == "TC-08"
    assert tc_id("test_tc13_driver_gets_403[admin]") == "TC-13"
    assert tc_id("test_health_returns_ok") is None
    assert tc_id("test_tc_id_mapping") is None

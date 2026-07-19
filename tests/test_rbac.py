from src.rbac import role_has_permission, role_summary


def test_admin_has_all_expected_access():
    assert role_has_permission("admin", "predict") is True
    assert role_has_permission("admin", "read_datalake") is True


def test_viewer_is_read_only():
    assert role_has_permission("viewer", "read_monitoring") is True
    assert role_has_permission("viewer", "predict") is False


def test_unknown_role_has_no_permissions():
    assert role_summary("unknown")["permissions"] == []

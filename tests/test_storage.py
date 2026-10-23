from storage import is_admin_password_valid, task_is_late


def test_admin_password_validation():
    assert is_admin_password_valid("secret", "secret")
    assert not is_admin_password_valid("wrong", "secret")
    assert not is_admin_password_valid("secret", "")


def test_late_task_requires_due_date_and_not_done():
    assert task_is_late("2026-01-01", "On Progress", "2026-01-02")
    assert not task_is_late("", "On Progress", "2026-01-02")
    assert not task_is_late("2026-01-01", "Selesai", "2026-01-02")

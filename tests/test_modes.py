from baalbek.modes import InputMode, ModeManager


class TestModeManager:
    def test_starts_in_normal_mode(self) -> None:
        mm = ModeManager()
        assert mm.mode is InputMode.NORMAL

    def test_enter_edit_mode(self) -> None:
        mm = ModeManager()
        mm.enter_edit()
        assert mm.mode is InputMode.EDIT

    def test_exit_edit_mode(self) -> None:
        mm = ModeManager()
        mm.enter_edit()
        mm.exit_edit()
        assert mm.mode is InputMode.NORMAL

    def test_is_navigation_key_normal(self) -> None:
        mm = ModeManager()
        for key in ("h", "j", "k", "l"):
            assert mm.is_navigation_key(key) is True
        assert mm.is_navigation_key("x") is False

    def test_is_navigation_key_edit(self) -> None:
        mm = ModeManager()
        mm.enter_edit()
        assert mm.is_navigation_key("h") is False
        assert mm.is_navigation_key("j") is False

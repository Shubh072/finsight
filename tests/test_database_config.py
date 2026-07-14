import importlib
import os
from pathlib import Path
import tempfile


def test_database_uri_is_absolute_and_parent_exists():
    import config

    old_cwd = os.getcwd()
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            reloaded_config = importlib.reload(config)

            uri = reloaded_config.SQLALCHEMY_DATABASE_URI
            assert uri.startswith("sqlite:///")

            db_path = Path(uri.removeprefix("sqlite:///"))
            assert db_path.is_absolute()
            assert db_path.parent.exists()
    finally:
        os.chdir(old_cwd)

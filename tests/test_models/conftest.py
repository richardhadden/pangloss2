from pytest import fixture

from pangloss.model_setup.model_manager import ModelManager


@fixture(scope="function", autouse=True)
def reset_model_manager():
    print("calling reset")
    ModelManager._reset()

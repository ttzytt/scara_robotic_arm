from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class TestClassVar(DataClassJsonMixin):
    cname: ClassVar[str] = "test_class_var"
    name: str = "default_name"


if __name__ == "__main__":
    test_cvar = TestClassVar.from_json(
        '{"cname": "another_name", "name" : "another_name", "non_exit_field" : "val"}'
    , infer_missing=True
    )
    print(test_cvar.cname)
    print(TestClassVar.cname)
    print(test_cvar.name)
    print(TestClassVar.name)

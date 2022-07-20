from typing import List
from enum import Enum
from pydantic import BaseModel


class ValidationResult(BaseModel):
    ok: bool
    messages: List[str]


class SchemaSpecType(str, Enum):
    inline = 'inline'
    file = 'file'


class SchemaSpec(BaseModel):
    type: SchemaSpecType
    details: str

    @classmethod
    def from_string(cls, spec: str) -> 'SchemaSpec':
        if spec.startswith('file:'):
            return cls(
                type=SchemaSpecType.file,
                details=spec[5:],
            )
        elif spec.startswith('inline:'):
            return cls(
                type=SchemaSpecType.inline,
                details=spec[7:],
            )
        else:
            # Attempt inline
            return cls(
                type=SchemaSpecType.inline,
                details=spec,
            )

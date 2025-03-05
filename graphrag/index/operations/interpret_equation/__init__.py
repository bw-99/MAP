# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The Indexing Engine equation interpretation package root."""

from graphrag.index.operations.interpret_equation.interpret_equation import (
    EquationInterpretationStrategyType,
    run_interpret_equation,
)

__all__ = ["EquationInterpretationStrategyType", "run_interpret_equation"]

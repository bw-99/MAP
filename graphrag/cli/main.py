# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""CLI entrypoint."""

import os
import re
from collections.abc import Callable
from enum import Enum
from pathlib import Path
from typing import Annotated

import typer

from graphrag.logger.types import LoggerType

from graphrag.prompt_tune.defaults import (
    MAX_TOKEN_COUNT,
    MIN_CHUNK_SIZE,
    N_SUBSET_MAX,
    K,
)
from graphrag.prompt_tune.types import DocSelectionType

from graphrag.cli.query import SearchType
from graphrag.cli.evaluate import EvalType

app = typer.Typer(
    help="GraphRAG: A graph-based retrieval-augmented generation (RAG) system.",
    no_args_is_help=True,
)


# A workaround for typer's lack of support for proper autocompletion of file/directory paths
# For more detail, watch
#   https://github.com/fastapi/typer/discussions/682
#   https://github.com/fastapi/typer/issues/951
def path_autocomplete(
    file_okay: bool = True,
    dir_okay: bool = True,
    readable: bool = True,
    writable: bool = False,
    match_wildcard: str | None = None,
) -> Callable[[str], list[str]]:
    """Autocomplete file and directory paths."""

    def wildcard_match(string: str, pattern: str) -> bool:
        regex = re.escape(pattern).replace(r"\?", ".").replace(r"\*", ".*")
        return re.fullmatch(regex, string) is not None

    from pathlib import Path

    def completer(incomplete: str) -> list[str]:
        # List items in the current directory as Path objects
        items = Path().iterdir()
        completions = []

        for item in items:
            # Filter based on file/directory properties
            if not file_okay and item.is_file():
                continue
            if not dir_okay and item.is_dir():
                continue
            if readable and not os.access(item, os.R_OK):
                continue
            if writable and not os.access(item, os.W_OK):
                continue

            # Append the name of the matching item
            completions.append(item.name)

        # Apply wildcard matching if required
        if match_wildcard:
            completions = filter(
                lambda i: wildcard_match(i, match_wildcard) if match_wildcard else False,
                completions,
            )

        # Return completions that start with the given incomplete string
        return [i for i in completions if i.startswith(incomplete)]

    return completer

@app.command("init")
def _initialize_cli(
    root: Annotated[
        Path,
        typer.Option(
            help="The project root directory.",
            dir_okay=True,
            writable=True,
            resolve_path=True,
            autocompletion=path_autocomplete(file_okay=False, dir_okay=True, writable=True, match_wildcard="*"),
        ),
    ],
):
    """Generate a default configuration file."""
    from graphrag.cli.initialize import initialize_project_at

    initialize_project_at(path=root)


@app.command("index")
def _index_cli(
    config: Annotated[
        Path | None,
        typer.Option(help="The configuration to use.", exists=True, file_okay=True, readable=True),
    ] = None,
    root: Annotated[
        Path,
        typer.Option(
            help="The project root directory.",
            exists=True,
            dir_okay=True,
            writable=True,
            resolve_path=True,
            autocompletion=path_autocomplete(file_okay=False, dir_okay=True, writable=True, match_wildcard="*"),
        ),
    ] = Path(),  # set default to current directory
    verbose: Annotated[bool, typer.Option(help="Run the indexing pipeline with verbose logging")] = False,
    memprofile: Annotated[bool, typer.Option(help="Run the indexing pipeline with memory profiling")] = False,
    resume: Annotated[str | None, typer.Option(help="Resume a given indexing run")] = None,
    logger: Annotated[LoggerType, typer.Option(help="The progress logger to use.")] = LoggerType.RICH,
    dry_run: Annotated[
        bool,
        typer.Option(
            help="Run the indexing pipeline without executing any steps to inspect and validate the configuration."
        ),
    ] = False,
    cache: Annotated[bool, typer.Option(help="Use LLM cache.")] = True,
    skip_validation: Annotated[
        bool,
        typer.Option(help="Skip any preflight validation. Useful when running no LLM steps."),
    ] = False,
    output: Annotated[
        Path | None,
        typer.Option(
            help="Indexing pipeline output directory. Overrides storage.base_dir in the configuration file.",
            dir_okay=True,
            writable=True,
            resolve_path=True,
        ),
    ] = None,
):
    """Build a knowledge graph index."""
    from graphrag.cli.index import index_cli

    index_cli(
        root_dir=root,
        verbose=verbose,
        resume=resume,
        memprofile=memprofile,
        cache=cache,
        logger=LoggerType(logger),
        config_filepath=config,
        dry_run=dry_run,
        skip_validation=skip_validation,
        output_dir=output,
    )


@app.command("update")
def _update_cli(
    config: Annotated[
        Path | None,
        typer.Option(help="The configuration to use.", exists=True, file_okay=True, readable=True),
    ] = None,
    root: Annotated[
        Path,
        typer.Option(
            help="The project root directory.",
            exists=True,
            dir_okay=True,
            writable=True,
            resolve_path=True,
        ),
    ] = Path(),  # set default to current directory
    verbose: Annotated[bool, typer.Option(help="Run the indexing pipeline with verbose logging")] = False,
    memprofile: Annotated[bool, typer.Option(help="Run the indexing pipeline with memory profiling")] = False,
    logger: Annotated[LoggerType, typer.Option(help="The progress logger to use.")] = LoggerType.RICH,
    cache: Annotated[bool, typer.Option(help="Use LLM cache.")] = True,
    skip_validation: Annotated[
        bool,
        typer.Option(help="Skip any preflight validation. Useful when running no LLM steps."),
    ] = False,
    output: Annotated[
        Path | None,
        typer.Option(
            help="Indexing pipeline output directory. Overrides storage.base_dir in the configuration file.",
            dir_okay=True,
            writable=True,
            resolve_path=True,
        ),
    ] = None,
):
    """
    Update an existing knowledge graph index.

    Applies a default storage configuration (if not provided by config), saving the new index to the local file system in the `update_output` folder.
    """
    from graphrag.cli.index import update_cli

    update_cli(
        root_dir=root,
        verbose=verbose,
        memprofile=memprofile,
        cache=cache,
        logger=LoggerType(logger),
        config_filepath=config,
        skip_validation=skip_validation,
        output_dir=output,
    )


@app.command("prompt-tune")
def _prompt_tune_cli(
    root: Annotated[
        Path,
        typer.Option(
            help="The project root directory.",
            exists=True,
            dir_okay=True,
            writable=True,
            resolve_path=True,
            autocompletion=path_autocomplete(file_okay=False, dir_okay=True, writable=True, match_wildcard="*"),
        ),
    ] = Path(),  # set default to current directory
    config: Annotated[
        Path | None,
        typer.Option(
            help="The configuration to use.",
            exists=True,
            file_okay=True,
            readable=True,
            autocompletion=path_autocomplete(file_okay=True, dir_okay=False, match_wildcard="*"),
        ),
    ] = None,
    domain: Annotated[
        str | None,
        typer.Option(
            help="The domain your input data is related to. For example 'space science', 'microbiology', 'environmental news'. If not defined, a domain will be inferred from the input data."
        ),
    ] = None,
    selection_method: Annotated[
        DocSelectionType, typer.Option(help="The text chunk selection method.")
    ] = DocSelectionType.RANDOM,
    n_subset_max: Annotated[
        int,
        typer.Option(help="The number of text chunks to embed when --selection-method=auto."),
    ] = N_SUBSET_MAX,
    k: Annotated[
        int,
        typer.Option(help="The maximum number of documents to select from each centroid when --selection-method=auto."),
    ] = K,
    limit: Annotated[
        int,
        typer.Option(help="The number of documents to load when --selection-method={random,top}."),
    ] = 15,
    max_tokens: Annotated[int, typer.Option(help="The max token count for prompt generation.")] = MAX_TOKEN_COUNT,
    min_examples_required: Annotated[
        int,
        typer.Option(help="The minimum number of examples to generate/include in the entity extraction prompt."),
    ] = 2,
    chunk_size: Annotated[int, typer.Option(help="The max token count for prompt generation.")] = MIN_CHUNK_SIZE,
    language: Annotated[
        str | None,
        typer.Option(help="The primary language used for inputs and outputs in graphrag prompts."),
    ] = None,
    discover_entity_types: Annotated[bool, typer.Option(help="Discover and extract unspecified entity types.")] = True,
    output: Annotated[
        Path,
        typer.Option(
            help="The directory to save prompts to, relative to the project root directory.",
            dir_okay=True,
            writable=True,
            resolve_path=True,
        ),
    ] = Path("prompts"),
):
    """Generate custom graphrag prompts with your own data (i.e. auto templating)."""
    import asyncio

    from graphrag.cli.prompt_tune import prompt_tune

    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        prompt_tune(
            root=root,
            config=config,
            domain=domain,
            selection_method=selection_method,
            limit=limit,
            max_tokens=max_tokens,
            chunk_size=chunk_size,
            language=language,
            discover_entity_types=discover_entity_types,
            output=output,
            n_subset_max=n_subset_max,
            k=k,
            min_examples_required=min_examples_required,
        )
    )


@app.command("query")
def _query_cli(
    method: Annotated[SearchType, typer.Option(help="The query algorithm to use.")],
    query: Annotated[str, typer.Option(help="The query to execute.")],
    config: Annotated[
        Path | None,
        typer.Option(
            help="The configuration to use.",
            exists=True,
            file_okay=True,
            readable=True,
            autocompletion=path_autocomplete(file_okay=True, dir_okay=False, match_wildcard="*"),
        ),
    ] = None,
    data: Annotated[
        Path | None,
        typer.Option(
            help="Indexing pipeline output directory (i.e. contains the parquet files).",
            exists=True,
            dir_okay=True,
            readable=True,
            resolve_path=True,
            autocompletion=path_autocomplete(file_okay=False, dir_okay=True, match_wildcard="*"),
        ),
    ] = None,
    root: Annotated[
        Path,
        typer.Option(
            help="The project root directory.",
            exists=True,
            dir_okay=True,
            writable=True,
            resolve_path=True,
            autocompletion=path_autocomplete(file_okay=False, dir_okay=True, match_wildcard="*"),
        ),
    ] = Path(),  # set default to current directory
    community_level: Annotated[
        int,
        typer.Option(
            help="The community level in the Leiden community hierarchy from which to load community reports. Higher values represent reports from smaller communities."
        ),
    ] = 2,
    dynamic_community_selection: Annotated[
        bool,
        typer.Option(help="Use global search with dynamic community selection."),
    ] = False,
    response_type: Annotated[
        str,
        typer.Option(
            help="Free form text describing the response type and format, can be anything, e.g. Multiple Paragraphs, Single Paragraph, Single Sentence, List of 3-7 Points, Single Page, Multi-Page Report. Default: Multiple Paragraphs"
        ),
    ] = "Multiple Paragraphs",
    streaming: Annotated[bool, typer.Option(help="Print response in a streaming manner.")] = False,
    output: Annotated[
            Path | None,
            typer.Option("--output", "-o", help="Output path for saving json file"),
        ] = None,
):
    """Query a knowledge graph index."""
    from graphrag.cli.query import query_cli

    result_data = query_cli(
        query=query,
        method=method,
        config_filepath=config,
        data_dir=data,
        root_dir=root,
        community_level=community_level,
        response_type=response_type,
        streaming=streaming,
        dynamic_community_selection=dynamic_community_selection,
    )

    if output:
        import json

        typer.echo(f"Saving results to {output}...")
        with open(output, "w", encoding="utf-8") as f:
            output_data = {
                "query": result_data["query"],
                "response": result_data["response"],
                "context_str": result_data["context"],
            }
            json.dump(output_data, f, ensure_ascii=False, indent=4)
        typer.secho(f"Successfully saved results to {output}", fg=typer.colors.GREEN)
    else:
        if not streaming and result_data["response"]:
            typer.echo("\n--- Response ---")
            typer.echo(result_data["response"])

    return result_data["response"], result_data["context"]

@app.command("evaluate")
def _evaluate_cli(
    method: Annotated[EvalType, typer.Option(help="The evaluation algorithm to use.")],
    config: Annotated[
        Path | None,
        typer.Option(
            help="The configuration to use.",
            exists=True,
            file_okay=True,
            readable=True,
            autocompletion=path_autocomplete(file_okay=True, dir_okay=False, match_wildcard="*"),
        ),
    ] = None,
    root_exp: Annotated[
        Path,
        typer.Option(
            help="The project root directory.",
            exists=True,
            dir_okay=True,
            writable=True,
            resolve_path=True,
            autocompletion=path_autocomplete(file_okay=False, dir_okay=True, match_wildcard="*"),
        ),
    ] = Path(),  # set default to current directory
    root_ctl: Annotated[
        Path,
        typer.Option(
            help="The second project root directory.",
            exists=True,
            dir_okay=True,
            writable=True,
            resolve_path=True,
            autocompletion=path_autocomplete(file_okay=False, dir_okay=True, match_wildcard="*"),
        ),
    ] = Path(),  # set default to current directory
    input_file: Annotated[
        Path | None,
        typer.Option(
            "--input", "-i", help="[Only for QUERY eval] The JSON file containing query results to evaluate."),
    ] = None,
    test_set_file: Annotated[
        Path | None,
        typer.Option("--test-set", help="[Only for QUERY eval] The CSV file with the ground truth test set."),
    ] = None,
    response_type: Annotated[
        str,
        typer.Option(
            help="Free form text describing the response type and format, can be anything, e.g. Multiple Paragraphs, Single Paragraph, Single Sentence, List of 3-7 Points, Single Page, Multi-Page Report. Default: Multiple Paragraphs"
        ),
    ] = "Multiple Paragraphs",
    dry_run: Annotated[
        bool,
        typer.Option(
            help="Run the indexing pipeline without executing any steps to inspect and validate the configuration."
        ),
    ] = False,
):
    """Evaluate a knowledge graph index."""
    from graphrag.cli.evaluate import graph_llm_evaluation, keyword_matching_evaluation, evaluate_query

    match method:
        case EvalType.KEYWORD_MATCHING:
            keyword_matching_evaluation(
                config_filepath=config,
                root_exp=root_exp,
                dry_run=dry_run,
            )
        case EvalType.GRAPH_LLM:
            graph_llm_evaluation(
                config_filepath=config,
                root_exp=root_exp,
                root_ctl=root_ctl,
                response_type=response_type,
                dry_run=dry_run,
            )
        case EvalType.QUERY:
            import json, asyncio, ast
            import pandas as pd

            # Escape hatch: if no test set or input file provided, use defaults from root_exp
            root = root_exp.resolve()
            if test_set_file is None:
                test_set_file = root / "test" / "test_set.csv"
                typer.secho(f"Warning: No test set file provided. Using default: {test_set_file}", fg=typer.colors.YELLOW)

            if input_file is None:
                input_file = root / "query_results.json"
                typer.secho(f"Warning: No input file provided. Using default: {input_file}", fg=typer.colors.YELLOW)
            
            # Load the result from our system (the retrieved data)
            typer.echo(f"Loading system response from {input_file}...")
            with open(input_file, "r", encoding="utf-8") as f:
                retrieved_data = json.load(f)

            query = retrieved_data.get("query")
            response = retrieved_data.get("response")
            retrieved_context_obj = retrieved_data.get("context") 

            # Load the entire ground truth test set
            typer.echo(f"Loading ground truth from {test_set_file}...")
            test_df = pd.read_csv(test_set_file)

            # Find the matching ground truth row for our query
            ground_truth_row = test_df[test_df['user_input'] == query]
            if ground_truth_row.empty:
                # just warning and do not exit
                typer.secho(f"Warning: Query '{query}' not found in the test set file.", fg=typer.colors.YELLOW)
                ground_truth_row = pd.DataFrame([{"user_input": query, "reference_contexts": "[]", "reference": "", "synthesizer_name": ""}])

            # safe conversion from string to list
            ground_truth_answer = ground_truth_row.iloc[0]["reference"]
            gt_contexts_str = ground_truth_row.iloc[0]["reference_contexts"]
            ground_truth_contexts = ast.literal_eval(gt_contexts_str)
            
            # Call the "worker" function with clean, prepared data
            evaluation = asyncio.run(evaluate_query(
                user_input=query,
                response=response,
                retrieved_contexts=retrieved_context_obj,
                gt_answer=ground_truth_answer,
                gt_contexts=ground_truth_contexts,
                config_filepath=config,
                root=root_exp,
            ))

            typer.echo(f"\nEvaluation Result: {evaluation}")
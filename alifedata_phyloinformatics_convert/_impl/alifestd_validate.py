# This file has been copied from hstrat (https://github.com/mmore500/hstrat/blob/b3eddc813a29485123777f415a973e9c7cf7cfd2/hstrat/_auxiliary_lib/_alifestd_validate.py).
# Eventually, it should be migrated to a standalone library.

import typing
import warnings

import pandas as pd

from .alifestd_is_asexual import alifestd_is_asexual
from .alifestd_make_ancestor_id_col import alifestd_make_ancestor_id_col
from .alifestd_make_ancestor_list_col import alifestd_make_ancestor_list_col
from .all_unique import all_unique
from .is_subset import is_subset


def __alifestd_parse_ancestor_ids(ancestor_list_str: str) -> typing.List[int]:
    """Parse ancestor ids from an `ancestor_list` field."""
    if ancestor_list_str.lower() == "[none]":
        return []
    else:
        return eval(ancestor_list_str)


def _validate_ancestors_asexual(
    phylogeny_df: pd.DataFrame, mutate: bool, warn: typing.Callable
) -> bool:
    if "ancestor_id" not in phylogeny_df:
        if not mutate:
            phylogeny_df = phylogeny_df.copy()
        phylogeny_df["ancestor_id"] = alifestd_make_ancestor_id_col(
            phylogeny_df["id"], phylogeny_df["ancestor_list"]
        )
    else:
        ok_ancestor_list_mask = phylogeny_df["ancestor_list"].astype(
            "str"
        ).str.lower().replace(
            "[]", "[none]"
        ) == alifestd_make_ancestor_list_col(
            phylogeny_df["id"], phylogeny_df["ancestor_id"]
        )
        if not (ok_ancestor_list_mask).all():
            example_row1 = phylogeny_df[~ok_ancestor_list_mask].iloc[0]
            example_row2 = phylogeny_df[~ok_ancestor_list_mask].sample(n=1)
            warn(
                "alifestd_validate asexual: "
                "ancestor_list nonequivalent to "
                "alifestd_make_ancestor_list_col result"
                f"with {(~ok_ancestor_list_mask).sum()} violations, "
                f"for example\n{example_row1} "
                f"\n{example_row2} "
            )
            return False

    ancestor_ids_are_subset = is_subset(
        phylogeny_df["ancestor_id"].to_numpy(),
        phylogeny_df["id"].astype("int").to_numpy(),
    )
    if not ancestor_ids_are_subset:
        warn(
            "alifestd_validate asexual: "
            "ancestor_id values are not a subset of id values",
        )
    return ancestor_ids_are_subset


def _validate_ancestors_sexual(
    phylogeny_df: pd.DataFrame,
    warn: typing.Callable,
) -> bool:
    ids = set(phylogeny_df["id"])
    ancestor_ids_are_subset = all(
        ancestor_id in ids
        for ancestor_list_str in phylogeny_df["ancestor_list"]
        for ancestor_id in _alifestd_parse_ancestor_ids(ancestor_list_str)
        if ancestor_id is not None
    )
    if not ancestor_ids_are_subset:
        warn(
            "alifestd_validate sexual: "
            "ancestor_id values are not a subset of id values",
        )
    return ancestor_ids_are_subset


def _alifestd_validate(
    phylogeny_df: pd.DataFrame,
    mutate: bool,
    warn: typing.Callable,
) -> bool:
    has_mandatory_columns = (
        "id" in phylogeny_df and "ancestor_list" in phylogeny_df
    )
    if not has_mandatory_columns:
        warn("alifestd_validate: missing mandatory columns")
        return False

    ids_valid = (
        len(phylogeny_df) == 0
        or pd.api.types.is_integer_dtype(phylogeny_df["id"])
        and (phylogeny_df["id"] >= 0).all()
        and all_unique(phylogeny_df["id"].to_numpy())
    )
    if not ids_valid:
        warn("alifestd_validate: invalid id detected")
        return False

    ancestor_lists_syntax_valid = (
        len(phylogeny_df) == 0
        or pd.api.types.is_string_dtype(phylogeny_df["ancestor_list"])
        and phylogeny_df["ancestor_list"].str.startswith("[").all()
        and phylogeny_df["ancestor_list"].str.endswith("]").all()
    )
    if not ancestor_lists_syntax_valid:
        warn("alifestd_validate: invalid ancestor_list syntax detected")
        return False

    return (
        _validate_ancestors_asexual(phylogeny_df, mutate, warn)
        if alifestd_is_asexual(phylogeny_df)
        else _validate_ancestors_sexual(phylogeny_df, warn)
    )


def alifestd_validate(
    phylogeny_df: pd.DataFrame,
    mutate: bool = False,
    diagnose: bool = True,
) -> bool:
    """Is the phylogeny compliant to alife data standards?

    Input dataframe is not mutated by this operation unless `mutate` set True.
    If `diagnose` is set, the failing validation subcheck will warn.
    """

    warn = warnings.warn if diagnose else lambda x: x

    try:
        return _alifestd_validate(phylogeny_df, mutate, warn)
    except Exception as exception:
        warn(f"alifestd_validate: {exception=} occured")
        return False

""" Build the argpaser
"""

from argparse import ArgumentParser
from argparse import _SubParsersAction
from argparse import SUPPRESS

from typing import Any
from typing import Dict
from typing import Tuple
from typing import Union

from .definitions import ApplicationConfiguration
from .definitions import Subset

from ..utils import Sentinel


class Parser:
    """Build the args"""

    # pylint: disable=too-few-public-methods
    def __init__(self, config: ApplicationConfiguration):
        self._config = config
        self._base_parser = ArgumentParser(add_help=False)
        self._configure_base()
        self.parser = ArgumentParser(parents=[self._base_parser])
        self._subparsers = self._add_subparsers()
        self._configure_subparsers()

    @staticmethod
    def generate_argument(entry) -> Tuple[Any, Union[Any, str, None], Dict[str, Any]]:
        """Generate an argparse argument"""
        kwargs = {}
        kwargs["help"] = entry.short_description
        if entry.value.default is not Sentinel:
            kwargs["help"] += f" (default: {entry.value.default})"
        kwargs["default"] = SUPPRESS
        kwargs["metavar"] = ""

        if entry.cli_parameters.positional:
            long = None
            if entry.cli_parameters.nargs is None:
                kwargs["nargs"] = "?"
            else:
                kwargs["nargs"] = entry.cli_parameters.nargs
        else:
            long = entry.cli_parameters.long_override or f"--{entry.name_dashed}"
            kwargs["dest"] = entry.name
            if entry.cli_parameters.nargs is None:
                kwargs["nargs"] = entry.cli_parameters.nargs

        if entry.cli_parameters.action is not None:
            kwargs["action"] = entry.cli_parameters.action

        return entry.cli_parameters.short, long, kwargs

    def _add_parser(self, parser, entry) -> None:
        if entry.cli_parameters:
            short, long, kwargs = self.generate_argument(entry)
            if not all((short, long)):
                parser.add_argument(entry.name, **kwargs)
            else:
                parser.add_argument(short, long, **kwargs)

    def _add_subparsers(self) -> _SubParsersAction:
        subcommand_value = [
            entry for entry in self._config.entries if entry.subcommand_value is True
        ]
        if len(subcommand_value) == 0:
            raise ValueError("No entry with subparser value defined")
        if len(subcommand_value) > 1:
            raise ValueError("Multiple entries with subparser value defined")
        entry = subcommand_value[0]
        return self.parser.add_subparsers(title=entry.short_description, dest=entry.name)

    def _configure_base(self) -> None:
        for entry in self._config.entries:
            if entry.subcommands is Subset.ALL:
                self._add_parser(self._base_parser, entry)

    def _configure_subparsers(self) -> None:
        for subcommand in self._config.subcommands:
            parser = self._subparsers.add_parser(
                subcommand.name,
                help=subcommand.description,
                description=f"{subcommand.name}: {subcommand.description}",
                parents=[self._base_parser],
            )
            for entry in self._config.entries:
                if isinstance(entry.subcommands, list) and subcommand.name in entry.subcommands:
                    self._add_parser(parser, entry)
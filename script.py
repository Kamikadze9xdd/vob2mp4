import getopt
import logging
import multiprocessing
import os
import sys
from typing import Union, Iterable, Iterator, Optional, List, Any, Tuple

import moviepy.editor as moviepy

NUMBER_OF_CPU = multiprocessing.cpu_count()
DEFAULT_FILE_EXTENSIONS = [".vob"]


class Converter:
    __slots__ = ("_file_extensions", "_input_folder_path", "_output_folder_path", "_logger")

    def __init__(
            self, input_folder_path: str, output_folder_path: str, file_extensions: Optional[List[str]] = None
    ) -> None:
        self._file_extensions = file_extensions or DEFAULT_FILE_EXTENSIONS

        self._input_folder_path = input_folder_path
        self._output_folder_path = output_folder_path

        self._logger: Optional[Any] = None

    @property
    def file_extensions(self) -> List[str]:
        return self._file_extensions

    @property
    def input(self) -> str:
        return self._input_folder_path

    @property
    def output(self) -> str:
        return self._output_folder_path

    @property
    def files(self) -> Iterator[str]:
        return self.get_files_from_folder(self.input, self.file_extensions)

    @property
    def logger(self) -> Any:
        if self._logger is None:
            logging.basicConfig(stream=sys.stdout, level=logging.INFO)
            self._logger = logging.getLogger("video_converter")

        return self._logger

    @staticmethod
    def get_files_from_folder(folder_path: str, extensions: Union[str, Iterable[str]]) -> Iterator[str]:
        for root, _, files in os.walk(folder_path):
            for file in files:
                extension = os.path.splitext(file)[1].lower()
                if not extension:
                    continue

                if extension in extensions:
                    yield os.path.join(root, file)

    def __get_new_paths(self, file_path: str) -> Tuple[str, str]:
        rel_path = os.path.relpath(file_path, self.input)

        return rel_path, os.path.join(self.output, f"{os.path.splitext(rel_path)[0]}.mp4")

    def __convert(self) -> None:
        i, files = 1, list(self.files)
        number_of_files = len(files)

        for file_path in self.files:
            rel_path, output_path = self.__get_new_paths(file_path)
            self.logger.info(f" Start converting {i} from {number_of_files} files: '{rel_path}'")

            output_dir = os.path.dirname(output_path)
            if not os.path.isdir(output_path):
                os.makedirs(output_dir, exist_ok=True)

            moviepy.VideoFileClip(file_path).write_videofile(output_path)

            self.logger.info(f" Finish converting {i} from {number_of_files} files: '{rel_path}'\n")
            i += 1

        self.logger.info(f" Converted {number_of_files} file(s)")

    def __show_files(self) -> None:
        for i, file_path in enumerate(self.files):
            self.logger.info(f" {i + 1}. {file_path}")

    @staticmethod
    def convert(input_folder: str, output_folder: str):
        Converter(input_folder_path=input_folder, output_folder_path=output_folder).__convert()

    @staticmethod
    def show_files(input_folder: str, output_folder: str):
        Converter(input_folder_path=input_folder, output_folder_path=output_folder).__show_files()

    @staticmethod
    def execute(input_folder: str, output_folder: str, command: str) -> None:

        if command not in ALLOWED_COMMANDS.keys():
            raise Exception(f"Command not found: {command}")

        ALLOWED_COMMANDS.get(command)(input_folder, output_folder)


ALLOWED_COMMANDS = {
    "show-files": Converter.show_files,
    "convert": Converter.convert
}


def parse_args(argv):
    command, input_file, output_file = None, None, None

    try:
        opts, args = getopt.getopt(argv, "hc:i:o:", ["command=", "input_folder=", "output_folder="])
    except getopt.GetoptError as e:
        print('test.py -c <command> -i <input_folder> -o <output_folder>')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print(f'execute: python {__file__}.py -c [{", ".join(list(ALLOWED_COMMANDS.keys()))}] '
                  f'-i <input_folder> -o <output_folder>')
            sys.exit()

        elif opt in ("-i", "--input_folder"):
            input_file = arg
        elif opt in ("-o", "--output_folder"):
            output_file = arg
        elif opt in ("-c", "--command"):
            command = arg

    if command is None:
        print("Command can not be empty (-c <command>)")
        sys.exit()

    if input_file is None:
        print("Input folder can not be empty (-i <input_folder>)")
        sys.exit()

    if output_file is None:
        print("Output folder can not be empty (-o <output_folder>)")
        sys.exit()

    Converter.execute(input_folder=input_file, output_folder=output_file, command=command)


if __name__ == '__main__':
    try:
        parse_args(sys.argv[1:])
    except KeyboardInterrupt:
        print('Interrupted')
        sys.exit(0)

from concurrent.futures import ThreadPoolExecutor
import logging
from pathlib import Path
import sys
from shutil import copy as shutil_copy
from subprocess import run as subprocess_run, CalledProcessError as subprocess_CalledProcessError
from tempfile import TemporaryDirectory
from time import perf_counter

from subword import SubWord

class Translator:
    GREEN_COLOR = '\33[32m'
    RED_COLOR   = '\33[31m'
    END_COLOR   = '\33[0m'

    ONMT_CMD = 'onmt_translate' \
        ' -model {model_file}' \
        ' -src {src_file}' \
        ' -output {tgt_file}' \
        ' -min_length 1' \
        ' -gpu -1'

    def __init__(self, model: Path, subword_src: SubWord, subword_tgt: SubWord):
        self._model = model
        self._subword_src = subword_src
        self._subword_tgt = subword_tgt


    def translate(self, text, output: Path = None):
        start = perf_counter()
        with TemporaryDirectory() as tmp_dir:
        # with Path('/tmp/test') as tmp_dir:
            tmp_dir = Path(tmp_dir)
            plain_file = self._plain_file(text, tmp_dir)
            translated_file = output if output else tmp_dir / 'translated.txt'
            cmd = self.ONMT_CMD.format(model_file=self._model,
                                       src_file=self._subword_encode(plain_file, tmp_dir),
                                       tgt_file=translated_file)

            try:
                logging.info(f'onmt cmd: {cmd}')
                subprocess_run(cmd, shell=True, capture_output=True, check=True)
            except subprocess_CalledProcessError as e:
                msg = e.stderr.decode("utf-8").strip()
                logging.error(self.RED_COLOR+'[failed]'+self.END_COLOR+\
                              f"onmt_translate stderr: [{msg}]")
                raise e
            except Exception as e:
                logging.error(self.RED_COLOR+'[failed]'+self.END_COLOR+\
                              f' exception in onmt_translate. e={repr(e)}')
                raise e

            decoded_file = self._subword_decode(translated_file, tmp_dir)

            finish = perf_counter()
            logging.info(self.GREEN_COLOR+'[succeed]'+self.END_COLOR+ \
                         f' succeed. cost: {finish-start:.2f} second(s)')

            if output is None:
                with open(decoded_file, 'r') as f:
                    return f.read().splitlines()
            else:
                shutil_copy(decoded_file, output)


    def _plain_file(self, text, tmp_dir: Path):
        if isinstance(text, Path) and text.is_file():
            return text
        if not isinstance(text, list):
            text = [str(text)]
        plain_file = tmp_dir / 'plain.txt'
        with open(plain_file, 'w+') as f:
            f.writelines([line + '\n' for line in text])
        return plain_file


    def _subword_encode(self, plain_file: Path, tmp_dir: Path):
        encoded_file = tmp_dir / 'encoded.txt'
        self._subword_src.encode_file(plain_file, encoded_file)
        return encoded_file


    def _subword_decode(self, encoded_file: Path, tmp_dir: Path):
        decoded_file = tmp_dir / 'decoded.txt'
        self._subword_src.decode_file(encoded_file, decoded_file)
        return decoded_file


if __name__ == '__main__':

    import argparse
    from signal import signal, SIGPIPE, SIG_DFL

    # ignore SIG_PIPE and don't throw exceptions on it
    signal(SIGPIPE,SIG_DFL)

    parser = argparse.ArgumentParser(description='translate text or file by onmt translator.')
    parser.add_argument('text', metavar='text',
                        type=Path,
                        help=
                        'text can be a quoted text string, '
                        'or be a file containing one text perline')
    parser.add_argument("-m", "--model", nargs="?",
                        type=Path, required=True,
                        help="path to the onmt model")
    parser.add_argument('-ms', '--model_src_subword', nargs='?',
                        type=Path, required=True,
                        help='path to source mode of subword')
    parser.add_argument('-mt', '--model_tgt_subword', nargs='?',
                        type=Path, required=True,
                        help='path to target mode of subword')
    parser.add_argument('-o', '--output', nargs='?',
                        type=Path, default=None,
                        help='a file to save translated text, if not specified stdout is used')
    parser.add_argument("-v", "--verbose", action="store_true", default=False)
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    trs = Translator(model=args.model,
                     subword_src=SubWord(args.model_src_subword),
                     subword_tgt=SubWord(args.model_tgt_subword))
    ret = trs.translate(args.text, output=args.output)
    if args.output is None:
        for line in ret:
            print(line)

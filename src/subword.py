from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sentencepiece as spm
import sys


class SubWord:

    def __init__(self, model: Path):
        self._sp = spm.SentencePieceProcessor()
        self._sp.load(str(model))

    def encode(self, plain_text: str):
        plain_text = plain_text.strip()
        encoded_text = self._sp.encode_as_pieces(plain_text)
        return " ".join([token for token in encoded_text])

    def encode_file(self, plain_file: Path, encoded_file: Path = None):
        with open(plain_file, 'r') as in_f, \
             (open(encoded_file, 'w+') if encoded_file else sys.stdout) as out_f, \
             ThreadPoolExecutor() as executor:
            lines = [line for line in in_f.readlines()]
            encoded_lines = executor.map(self.encode, lines)
            encoded_lines = [line + '\n' for line in encoded_lines]
            out_f.writelines(encoded_lines)

    def decode(self, encoded_text: str):
        encoded_text = encoded_text.strip().split(" ")
        return self._sp.decode_pieces(encoded_text)

    def decode_file(self, encoded_file: Path, decoded_file: Path = None):
        with open(encoded_file, 'r') as in_f, \
             (open(decoded_file, 'w+') if decoded_file else sys.stdout) as out_f, \
             ThreadPoolExecutor() as executor:
            lines = [line for line in in_f.readlines()]
            decoded_lines = executor.map(self.decode, lines)
            decoded_lines = [line + '\n' for line in decoded_lines]
            out_f.writelines(decoded_lines)


if __name__ == '__main__':

    import argparse
    from signal import signal, SIGPIPE, SIG_DFL

    # ignore SIG_PIPE and don't throw exceptions on it
    signal(SIGPIPE,SIG_DFL)

    parser = argparse.ArgumentParser(description='Encode or decode subword.')
    parser.add_argument('command', metavar='command',
                        choices=['encode', 'decode'],
                        help=
                        'encode: encode plain text or file; '
                        'decode: decode encoded text or file;')
    parser.add_argument("-m", "--model", nargs="?",
                        type=Path, required=True,
                        help="path to the subword model")
    parser.add_argument('-i', '--input', nargs='?',
                        type=Path, required=True,
                        help='a quoted text or a file containing lines of text to be translated')
    parser.add_argument('-o', '--output', nargs='?',
                        type=Path, default=None,
                        help='a file to save translated text, if not specified stdout is used')
    args = parser.parse_args()

    sub = SubWord(args.model)
    if args.command == 'encode':
        if args.input.is_file():
            sub.encode_file(args.input, args.output)
        else:
            output = sub.encode(str(args.input))
            print(output)
    else:
        if args.input.is_file():
            sub.decode_file(args.input, args.output)
        else:
            output = sub.decode(str(args.input))
            print(output)

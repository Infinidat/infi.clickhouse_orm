import sys
import nltk
from nltk.stem.porter import PorterStemmer
from glob import glob
from infi.clickhouse_orm import Database
from models import Fragment


def trim_punctuation(word):
    '''
    Trim punctuation characters from the beginning and end of the word
    '''
    start = end = len(word)
    for i in range(len(word)):
        if word[i].isalnum():
            start = min(start, i)
            end = i + 1
    return word[start : end]


def parse_file(filename):
    '''
    Parses a text file at the give path.
    Returns a generator of tuples (original_word, stemmed_word)
    The original_word may include punctuation characters.
    '''
    stemmer = PorterStemmer()
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            for word in line.split():
                yield (word, stemmer.stem(trim_punctuation(word)))


def get_fragments(filename):
    '''
    Converts a text file at the given path to a generator
    of Fragment instances.
    '''
    from os import path
    document = path.splitext(path.basename(filename))[0]
    idx = 0
    for word, stem in parse_file(filename):
        idx += 1
        yield Fragment(document=document, idx=idx, word=word, stem=stem)
    print('{} - {} words'.format(filename, idx))


if __name__ == '__main__':

    # Load NLTK data if necessary
    nltk.download('punkt')
    nltk.download('wordnet')

    # Initialize database
    db = Database('default')
    db.create_table(Fragment)

    # Load files from the command line or everything under ebooks/
    filenames = sys.argv[1:] or glob('ebooks/*.txt')
    for filename in filenames:
        db.insert(get_fragments(filename), batch_size=100000)

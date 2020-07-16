import sys
from colorama import init, Fore, Back, Style
from nltk.stem.porter import PorterStemmer
from infi.clickhouse_orm import Database, F
from models import Fragment
from load import trim_punctuation


# The wildcard character
WILDCARD = '*'


def prepare_search_terms(text):
    '''
    Convert the text to search into a list of stemmed words.
    '''
    stemmer = PorterStemmer()
    stems = []
    for word in text.split():
        if word == WILDCARD:
            stems.append(WILDCARD)
        else:
            stems.append(stemmer.stem(trim_punctuation(word)))
    return stems


def build_query(db, stems):
    '''
    Returns a queryset instance for finding sequences of Fragment instances
    that matche the list of stemmed words.
    '''
    # Start by searching for the first stemmed word
    all_fragments = Fragment.objects_in(db)
    query = all_fragments.filter(stem=stems[0]).only(Fragment.document, Fragment.idx)
    # Add the following words to the queryset
    for i, stem in enumerate(stems):
        # Skip the first word (it's already in the query), and wildcards
        if i == 0 or stem == WILDCARD:
            continue
        # Create a subquery that finds instances of the i'th word
        subquery = all_fragments.filter(stem=stem).only(Fragment.document, Fragment.idx)
        # Add it to the query, requiring that it will appear i places away from the first word
        query = query.filter(F.isIn((Fragment.document, Fragment.idx + i), subquery))
    # Sort the results
    query = query.order_by(Fragment.document, Fragment.idx)
    return query


def get_matching_text(db, document, from_idx, to_idx, extra=5):
    '''
    Reconstructs the document text between the given indexes (inclusive),
    plus `extra` words before and after the match. The words that are
    included in the given range are highlighted in green.
    '''
    text = []
    conds = (Fragment.document == document) & (Fragment.idx >= from_idx - extra) & (Fragment.idx <= to_idx + extra)
    for fragment in Fragment.objects_in(db).filter(conds).order_by('document', 'idx'):
        word = fragment.word
        if fragment.idx == from_idx:
            word = Fore.GREEN + word
        if fragment.idx == to_idx:
            word = word + Style.RESET_ALL
        text.append(word)
    return ' '.join(text)


def find(db, text):
    '''
    Performs the search for the given text, and prints out the matches.
    '''
    stems = prepare_search_terms(text)
    query = build_query(db, stems)
    print('\n' + Fore.MAGENTA + str(query) + Style.RESET_ALL + '\n')
    for match in query:
        text = get_matching_text(db, match.document, match.idx, match.idx + len(stems) - 1)
        print(Fore.CYAN + match.document + ':' + Style.RESET_ALL, text)


if __name__ == '__main__':

    # Initialize colored output
    init()

    # Initialize database
    db = Database('default')

    # Search
    text = ' '.join(sys.argv[1:])
    if text:
        find(db, text)

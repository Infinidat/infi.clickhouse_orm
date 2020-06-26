# Full Text Search

This example shows how ClickHouse might be used for searching for word sequences in texts. It's a nice proof of concept, but for production use there are probably better solutions, such as Elasticsearch.

## Running the code

Create a virtualenv and install the required libraries:
```
virtualenv -p python3.6 env
source env/bin/activate
pip install -r requirements.txt
```
Run the `download_ebooks` script to download a dozen classical books from [The Gutenberg Project](http://www.gutenberg.org/):
```
python download_ebooks.py
```
Run the `load` script to populate the database with the downloaded texts:
```
python load.py
```
And finally, run the full text search:
```
 python search.py "cheshire cat"
 ```
Asterisks can be used as wildcards (each asterisk stands for one word):
```
 python search.py "much * than"
 ```

## How it works

The `models.py` file defines an ORM model for storing each word in the indexed texts:
```python
class Fragment(Model):

    language = LowCardinalityField(StringField(default='EN'))
    document = LowCardinalityField(StringField())
    idx      = UInt64Field()
    word     = StringField()
    stem     = StringField()

    # An index for faster search by document and fragment idx
    index    = Index((document, idx), type=Index.minmax(), granularity=1)

    # The primary key allows efficient lookup of stems
    engine   = MergeTree(order_by=(stem, document, idx), partition_key=('language',))
```
The `document` (name) and `idx` (running number of the word inside the document) fields identify the specific word. The `word` field stores the original word as it appears in the text, while the `stem` contains the word after normalization, and that's the field which is used for matching the search terms. Stemming the words makes the matching less strict, so that searching for "swallowed" will also find documents that mention "swallow" or "swallowing".

Here's what some records in the fragment table might look like:

| language | document                | idx  | word             | stem          |
|----------|-------------------------|------|------------------|---------------|
| EN       | Moby Dick; or The Whale | 4510 | whenever         | whenev        |
| EN       | Moby Dick; or The Whale | 4511 | it               | it            |
| EN       | Moby Dick; or The Whale | 4512 | is               | is            |
| EN       | Moby Dick; or The Whale | 4513 | a                | a             |
| EN       | Moby Dick; or The Whale | 4514 | damp,            | damp          |
| EN       | Moby Dick; or The Whale | 4515 | drizzly          | drizzli       |
| EN       | Moby Dick; or The Whale | 4516 | November         | novemb        |
| EN       | Moby Dick; or The Whale | 4517 | in               | in            |
| EN       | Moby Dick; or The Whale | 4518 | my               | my            |
| EN       | Moby Dick; or The Whale | 4519 | soul;            | soul          |

Let's say we're looking for the terms "drizzly November". Finding the first in the sequence (after stemming it) is fast and easy:
```python
query = Fragment.objects_in(db).filter(stem='drizzli').only(Fragment.document, Fragment.idx)
```
We're interested only in the `document` and `idx` fields, since they identify a specific word.

To find the next word in the search terms, we need a subquery similar to the first one, with an additional condition that its index will be one greater than the index of the first word:
```python
subquery = Fragment.objects_in(db).filter(stem='novemb').only(Fragment.document, Fragment.idx)
query = query.filter(F.isIn((Fragment.document, Fragment.idx + 1), subquery))
```
And so on, by adding another subquery for each additional search term we can construct the whole sequence of words.

As for wildcard support, when encountering a wildcard in the search terms we simply skip it - it does not need a subquery (since it can match any word). It only increases the index count so that the query conditions will "skip" one word in the sequence.

The algorithm for building this compound query can be found in the `build_query` function.

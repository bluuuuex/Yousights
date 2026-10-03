"""
CC coordinating conjunction
CD cardinal digit
DT determiner
EX existential there (like: “there is” … think of it like “there exists”)
FW foreign word
IN preposition/subordinating conjunction
JJ adjective ‘big’
JJR adjective, comparative ‘bigger’
JJS adjective, superlative ‘biggest’
LS list marker 1)
MD modal could, will
NN noun, singular ‘desk’
NNS noun plural ‘desks’
NNP proper noun, singular ‘Harrison’
NNPS proper noun, plural ‘Americans’
PDT predeterminer ‘all the kids’
POS possessive ending parent’s
PRP personal pronoun I, he, she
PRP$ possessive pronoun my, his, hers
RB  adverb very, silently,
RBR adverb, comparative better
RBS adverb, superlative best
RP  particle give up
TO  to go ‘to’ the store.
UH  interjection, errrrrrrrm
VB  verb, base form take
VBD verb, past tense took
VBG verb, gerund/present participle taking
VBN verb, past participle taken
VBP verb, sing. present, non-3d take
VBZ verb, 3rd person sing. present takes
WDT wh-determiner which
WP  wh-pronoun who, what
WP$ possessive wh-pronoun whose
WRB wh-abverb where, when
"""

import re
import unicodedata
import nltk
import logging
import pandas as pd

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from collections import Counter
from __init__ import application_path
from sources import youtube_text_keywords
from sources.nlp_limits import MAX_TEXT_CHARACTERS, MAX_TOKENS, MAX_TRANSCRIPT_SEGMENTS, NLPLimitError, validate_text

# nltk.download("stopwords")
# nltk.download("punkt")

nltk.data.path.append(application_path + "/nltk_data")

logging.getLogger(__name__)

my_stopwords_path = "/data/Stopwords/stopwords.csv"
my_stopwords = pd.read_csv(application_path + my_stopwords_path, usecols=[0]).values.ravel().tolist()

nltk_stopwords = stopwords.words("english")

stopwords_all = list(set(my_stopwords).union(set(nltk_stopwords)))


def comment_clean(comments):
    clean_comment = ""
    for comment in comments:
        # comment = re.sub(r"([^\s\w]|_)+", " ", comment)
        comment = re.sub(r"[^a-zA-Z' ]+", "", comment)
        clean_comment += comment + " . "
    return clean_comment


def normalization(text):
    """
    Normalise input text and return tokens
    Args:
        text
    Returns:
        tokens
    """
    validate_text(text)
    tokens = nltk.word_tokenize(text, preserve_line=True)
    if len(tokens) > MAX_TOKENS:
        raise NLPLimitError("NLP text exceeds 10000 tokens")
    norm_text = []
    for token in tokens:
        # remove non-ASCII characters
        non_ASCII = unicodedata.normalize("NFKD", token).encode("ascii", "ignore").decode("utf-8", "ignore")
        # convert to lower case
        lower_case = non_ASCII.lower()
        # remove punctuation
        no_puncuation = re.sub(r"([^\s\w]|_)+", "", lower_case)

        # Remove stop words
        if no_puncuation != "":
            if no_puncuation not in stopwords_all:
                norm_text.append(no_puncuation)
    return norm_text


def lemmatize_verbs(words):
    """
    Lemmatize verbs in list of tokenized words
    Args:
        wrods
    Returns:
        lemmas
    """
    lemmatizer = WordNetLemmatizer()
    lemmas = []
    for word in words:
        lemma = lemmatizer.lemmatize(word, pos="v")
        lemma = lemmatizer.lemmatize(lemma, pos="a")
        lemmas.append(lemma)
    return lemmas


def get_weighted_keywords(text):
    '''
    Get weighted keywords list
    :param text: String
    :return: list() list of the keywords
    '''
    clean_text = lemmatize_verbs(normalization(text))
    keywords = youtube_text_keywords.get_weighted_keywords_list(youtube_text_keywords.get_keywords(clean_text, 200))

    return keywords


def get_freq(text, keywords_corpus=None):
    """
    Get the frequency of text
    :param text
    :return: dict of word frequency
    :corpus: A list, contains multiple keywords source
    """
    text = lemmatize_verbs(normalization((text)))
    freq_json = list()

    if keywords_corpus:
        freq_dict = dict(Counter(text).most_common())
        for each in freq_dict:
            if each in keywords_corpus:
                freq_json.append({"word": each, "weight": freq_dict[each]})
        return freq_json
    else:
        freq_dict = dict(Counter(text).most_common(50))
        for each in freq_dict:
            freq_json.append({"word": each, "weight": freq_dict[each]})
        return freq_json


def get_trans_str(en_transcript):
    """
    Get the transcript as string format
    :param en_transcript:
    :return:
    """

    if len(en_transcript) > MAX_TRANSCRIPT_SEGMENTS:
        raise NLPLimitError("Transcript exceeds 10000 segments")
    texts = []
    total_characters = 0
    for each_transcript in en_transcript:
        text = each_transcript["text"]
        total_characters += len(text) + 1  # Preserve each segment's trailing space.
        if total_characters > MAX_TEXT_CHARACTERS:
            raise NLPLimitError("Transcript exceeds 100000 characters")
        texts.append(text)
    return " ".join(texts) + (" " if texts else "")

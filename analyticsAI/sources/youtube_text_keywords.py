'''
Keyewords Extraction based on Text Rank and Spacy
'''

from collections import OrderedDict
import numpy as np
import spacy
from sources.nlp_limits import MAX_TEXT_CHARACTERS, MAX_TOKENS, MAX_KEYWORD_NODES, NLPLimitError

keywords_nlp = spacy.load('en_core_web_sm')

'''
Initialize the constant parameters that will be used in the function
'''
# Only considering the importance of words with NOUN, PROPN, VERB POS tags
# Because most of words with other POS tags usually meaningless
CANDIDATE_POS = ['NOUN', 'PROPN', 'VERB']
# Windows size for N-gram
N = 4
# Damping Coefficient
DAMPING_COEFFICIENT = 0.85
# Convergence Threshold
CONVERG_THRES = 1e-5
# Iteration Step
ITER_STEP = 10


def get_keywords(list_of_word, keywords_number):
    '''
    Get keywords from the given corpus
    :param list_of_word: list(), cleaned words list
    :param keywords_number: How many keywords need to be returned
    :return: dict() {'keyword': weight}
    '''
    # Convert list of the words to string
    if len(list_of_word) > MAX_TOKENS:
        raise NLPLimitError("NLP text exceeds 10000 tokens")
    if sum(len(word) for word in list_of_word) + max(len(list_of_word) - 1, 0) > MAX_TEXT_CHARACTERS:
        raise NLPLimitError("NLP text exceeds 100000 characters")
    text = ' '.join(list_of_word)

    doc = keywords_nlp.make_doc(text)
    if len(doc) > MAX_TOKENS:
        raise NLPLimitError("NLP text exceeds 10000 tokens")
    doc = keywords_nlp(doc)

    '''
    Make Sentences
    '''
    sentences = list()
    # doc.sents calculates the boundaries of the sentences
    for each_sentence in doc.sents:
        selected_words = list()
        for each_word in each_sentence:
            if each_word.pos_ in CANDIDATE_POS:
                selected_words.append(each_word.text)
        sentences.append(selected_words)

    '''
    Buid Vocabulary and N-gram pair
    '''
    vocabulary = OrderedDict()
    n_gram_pairs = list()
    seen_pairs = set()
    word_index = 0

    for sentence in sentences:
        for index, word in enumerate(sentence):
            if word not in vocabulary:
                if len(vocabulary) >= MAX_KEYWORD_NODES:
                    raise NLPLimitError("TextRank exceeds 1000 candidate words")
                vocabulary[word] = word_index
                word_index += 1
            for j in range(index + 1, index + N):
                if j >= len(sentence):
                    break
                n_gram_pair = (word, sentence[j])
                if n_gram_pair not in seen_pairs:
                    seen_pairs.add(n_gram_pair)
                    n_gram_pairs.append(n_gram_pair)

    '''
    Build Text Rank Matrix
    '''
    init_matrix = np.zeros((len(vocabulary), len(vocabulary)), dtype='float')

    # Add initial weight to the matrix
    for row_word, column_word in n_gram_pairs:
        i, j = vocabulary[row_word], vocabulary[column_word]
        init_matrix[i][j] = 1

    # Get the symmetrized matrix
    sym_matrix = init_matrix + init_matrix.T - np.diag(init_matrix.diagonal())

    # Normalize the matrix
    norm = np.sum(sym_matrix, axis=0)
    norm_sym_matrix = np.divide(sym_matrix, norm, out=np.zeros_like(sym_matrix), where=norm != 0)

    # Initialize the page rank
    page_rank = np.array([1] * len(vocabulary))

    # Iteration
    previous_page_rank = 0
    for epoch in range(ITER_STEP):
        page_rank = (1 - DAMPING_COEFFICIENT) + DAMPING_COEFFICIENT * np.dot(norm_sym_matrix, page_rank)
        if abs(previous_page_rank - sum(page_rank)) < CONVERG_THRES:
            break
        else:
            previous_page_rank = sum(page_rank)

    '''
    Assign weights to each of the word
    '''
    weighted_word = dict()
    for non_weighted_word, index in vocabulary.items():
        weighted_word[non_weighted_word] = page_rank[index]

    '''
    Get the sorted keywords
    '''
    sorted_weighted_node = OrderedDict(sorted(weighted_word.items(), key=lambda t: t[1], reverse=True))

    # Get the most weighted keywords
    if keywords_number >= len(sorted_weighted_node):
        keywords = sorted_weighted_node
    else:
        keywords = {k: sorted_weighted_node[k] for k in list(sorted_weighted_node.keys())[0:keywords_number]}

    return keywords


def get_weighted_keywords_list(keywords):
    '''
    keywords used in similarity calculation
    keywords are duplicated based on their weights
    :param keywords: dict() {'keyword': weight}
    :return: list() keywords list
    '''
    weighted_keywords_list = list()
    for word in keywords.keys():
        for weight in range(int(keywords[word])):
            weighted_keywords_list.append(word)

    return weighted_keywords_list

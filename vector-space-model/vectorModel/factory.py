import sys

from vectorModel.inverted_index_builder import BOWFileBuilder
from vectorModel.token_stream import TokenStream, LemmaTokenizer


def token_stream_factory(config, lang, normalization, term, stop_word_removal, parser):
    sys.stderr.write("Loading Token stream... [parser: morphodita]\n")

    excluded = {
        'cs': ['DOCNO', 'DOCID', 'DATE', 'GEOGRAPHY'],  # 'TITLE', 'HEADING' 'TEXT'
        'en': ['DOCNO', 'DOCID', 'FN', 'PN', 'PP', 'PD', 'SN', 'CP', 'IS', 'PR', 'PG', 'HI', 'DD', 'EI', 'PY', 'SL']}

    file_list = config['inverted_index'][lang + '_list']
    base_dir = config['inverted_index'][lang + '_dir']

    extra_header = None
    if lang + '_header' in config['inverted_index']:
        extra_header = config['inverted_index'][lang + '_header']

    if parser == 'morphodita':
        morphodita_dictionary = config['morphodita'][lang + '_dict']
        morphodita_tagger = config['morphodita'][lang + '_tagger']
        lemma_tokenizer = LemmaTokenizer(morphodita_dictionary, morphodita_tagger)

        tok_str = TokenStream(file_list=file_list,
                              base_dir=base_dir,
                              extra_header=extra_header,
                              tokenizer=lemma_tokenizer,
                              excluded_xml_tags=excluded[lang],
                              lang=lang,
                              term=term,
                              normalization=normalization,
                              stop_word_removal=stop_word_removal
                              )
    else:
        raise Exception("Parser [%s] not implemented (problematic creation of a lemma with this parser)" % parser)

    sys.stderr.write('--------------------------------\n')
    return tok_str


def file_formatter_factory(type_of):
    if type_of == 'bow':
        return BOWFileBuilder(type_of)
    else:
        raise Exception("File formatter [%s] not yet implemented" % type_of)

import time
from abc import ABC, abstractmethod
import queue
import sys
import os
import string as sstring
import xml.etree.ElementTree as ETree

from ufal.morphodita import * # install this
import unidecode  # install this
from num2words import num2words  # install this
# import nltk


class AbstractTokenStream(ABC):
    @abstractmethod
    def has_next(self):
        pass

    @abstractmethod
    def tokenize_string(self, string):
        pass

    @abstractmethod
    def num_of_documents(self):
        pass

    @abstractmethod
    def next_lemma(self):
        pass


# perform Tokenization (text -> word) + Normalization_1 (word -> lemma) IN ONE STEP
# So output is type / term which can ce further normalized ( remove punctuation ... )
class LemmaTokenizer:
    def __init__(self, dict_file, tagger_file):
        # sys.stderr.write('>> Loading tokenizer...\n')
        # load the tagger and dictionary
        self._morphological_dict = self._load_dictionary(dict_file)
        self._tagger = self._load_tagger(tagger_file)

        self._current_text = ''
        self.t = 0
        # create tokenizer
        self._forms = Forms()
        self._lemmas = TaggedLemmas()
        self._tokens = TokenRanges()
        self._tokenizer = self._tagger.newTokenizer()  # tokenizer based on tagger
        if self._tokenizer is None:
            sys.stderr.write("Error: No tokenizer is defined for the supplied model!")
            exit(1)

        self._curr_sentence_len = 0
        self._word_in_sentence = 0

    def set_text(self, text):
        self._current_text = text
        self.t = 0
        self._tokenizer.setText(text)

    def _next_sentence(self):
        # try to read next sentence
        if self._tokenizer.nextSentence(self._forms, self._tokens):
            self._tagger.tag(self._forms, self._lemmas)
            self._word_in_sentence = 0
            self._curr_sentence_len = len(self._lemmas)
            return True

    @staticmethod
    def encode_entities(text):
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

    def next_lemma(self):
        # check if we still have lemmas in sentece, if not, load new sentence
        if self._word_in_sentence >= self._curr_sentence_len:
            #             print('loading next sentence')
            # try to load next sentence
            if not self._next_sentence():
                return False

        lemma = self._lemmas[self._word_in_sentence]
        token = self._tokens[self._word_in_sentence]
        # sys.stdout.write('%s<token lemma="%s" tag="%s">%s</token>\n' % (
        #     self.encode_entities(self._current_text [self.t: token.start]),
        #
        #     self.encode_entities(lemma.lemma),
        #     self.encode_entities(lemma.tag),
        #     self.encode_entities(self._current_text [token.start: token.start + token.length])
        # ))
        # self.t = token.start + token.length
        # # print("lemma: %s \t tag: %s" % (lemma.lemma, lemma.tag))

        raw_lemma = self._morphological_dict.rawLemma(lemma.lemma)

        result = {'lemma': lemma.lemma,
                  'raw_lemma': raw_lemma,
                  'tag': lemma.tag,
                  'word': self._current_text[token.start: token.start + token.length]
                  }
        # next word next time
        self._word_in_sentence += 1
        return result

    @staticmethod
    def _load_dictionary(file):
        sys.stderr.write('>> Loading dictionary: ')
        morpho = Morpho.load(file)
        if not morpho:
            sys.stderr.write("Error: Cannot load dictionary from file '%s'\n" % sys.argv[1])
            sys.exit(1)
        sys.stderr.write('success\n')
        return morpho

    @staticmethod
    def _load_tagger(file):
        sys.stderr.write('>> Loading tagger: ')
        tagger = Tagger.load(file)
        if not tagger:
            sys.stderr.write("Error: Cannot load tagger from file '%s'\n" % sys.argv[1])
            sys.exit(1)
        sys.stderr.write('success\n')
        return tagger


class TokenStream(AbstractTokenStream):
    def __init__(self, file_list, base_dir, tokenizer, excluded_xml_tags, lang, term, normalization, stop_word_removal,
                 extra_header=None):

        self._timer = None
        self.stop_word_removal = stop_word_removal

        self.tokenizer = tokenizer

        self.normalization = normalization
        self.term = term

        self.lang = lang

        # so we can use (has next)
        self._prepared = None

        # load file names
        self._cnt_files = 0
        self._current_file = 0

        self._file_queue = self._read_file_names(file_list)
        self._base_dir = base_dir
        self._extra_header = extra_header
        self._excluded_xml_tags = excluded_xml_tags

        # queue for storing the documents
        self._doc_queue = queue.Queue()

        # for info about current document
        self._doc_no = 0
        self._pos_in_doc = 0

        # num of documents
        self._cnt_documents = 0

        # for ability to tokenize one string
        self._single_string = False

        self._punct_to_space_translator = str.maketrans(sstring.punctuation, ' ' * len(sstring.punctuation))
        self._digit_to_space_translator = str.maketrans(sstring.digits, ' ' * len(sstring.digits))
        self._ws_to_space_translator = str.maketrans(sstring.whitespace, ' ' * len(sstring.whitespace))
        self._delete_punct_translator = str.maketrans('', '', sstring.punctuation)
        self._delete_digit_translator = str.maketrans('', '', sstring.digits)
        sys.stderr.write(">> Loading document list: success [%s]\n" % str(self._cnt_files))

        self.cz_stopwords = {'ačkoli', 'ahoj', 'ale', 'anebo', 'ano', 'asi', 'aspoň', 'během', 'bez', 'beze', 'blízko',
                             'bohužel',
                             'brzo', 'bude', 'budeme', 'budeš', 'budete', 'budou', 'budu', 'byl', 'byla', 'byli',
                             'bylo',
                             'byly',
                             'bys', 'čau', 'chce', 'chceme', 'chceš', 'chcete', 'chci', 'chtějí', 'chtít',
                             'chut'',''chuti',
                             'co',
                             'čtrnáct', 'čtyři', 'dál', 'dále', 'daleko', 'děkovat', 'děkujeme', 'děkuji', 'den',
                             'deset',
                             'devatenáct', 'devět', 'do', 'dobrý', 'docela', 'dva', 'dvacet', 'dvanáct', 'dvě', 'hodně',
                             'já',
                             'jak', 'jde', 'je', 'jeden', 'jedenáct', 'jedna', 'jedno', 'jednou', 'jedou', 'jeho',
                             'její',
                             'jejich',
                             'jemu', 'jen', 'jenom', 'ještě', 'jestli', 'jestliže', 'jí', 'jich', 'jím', 'jimi',
                             'jinak',
                             'jsem',
                             'jsi', 'jsme', 'jsou', 'jste', 'kam', 'kde', 'kdo', 'kdy', 'když', 'ke', 'kolik', 'kromě',
                             'která',
                             'které', 'kteří', 'který', 'kvůli', 'má', 'mají', 'málo', 'mám', 'máme', 'máš', 'máte',
                             'mé',
                             'mě',
                             'mezi', 'mí', 'mít', 'mně', 'mnou', 'moc', 'mohl', 'mohou', 'moje', 'moji', 'možná', 'můj',
                             'musí',
                             'může', 'my', 'na', 'nad', 'nade', 'nám', 'námi', 'naproti', 'nás', 'náš', 'naše', 'naši',
                             'ne',
                             'ně',
                             'nebo', 'nebyl', 'nebyla', 'nebyli', 'nebyly', 'něco', 'nedělá', 'nedělají', 'nedělám',
                             'neděláme',
                             'neděláš', 'neděláte', 'nějak', 'nejsi', 'někde', 'někdo', 'nemají', 'nemáme', 'nemáte',
                             'neměl',
                             'němu', 'není', 'nestačí', 'nevadí', 'než', 'nic', 'nich', 'ním', 'nimi', 'nula', 'od',
                             'ode',
                             'on',
                             'ona', 'oni', 'ono', 'ony', 'osm', 'osmnáct', 'pak', 'patnáct', 'pět', 'po', 'pořád',
                             'potom',
                             'pozdě',
                             'před', 'přes', 'přese', 'pro', 'proč', 'prosím', 'prostě', 'proti', 'protože', 'rovně',
                             'se',
                             'sedm',
                             'sedmnáct', 'šest', 'šestnáct', 'skoro', 'smějí', 'smí', 'snad', 'spolu', 'sta', 'sté',
                             'sto',
                             'ta',
                             'tady', 'tak', 'takhle', 'taky', 'tam', 'tamhle', 'tamhleto', 'tamto', 'tě', 'tebe',
                             'tebou',
                             'ted',
                             'tedy', 'ten', 'ti', 'tisíc', 'tisíce', 'to', 'tobě', 'tohle', 'toto', 'třeba', 'tři',
                             'třináct',
                             'trošku', 'tvá', 'tvé', 'tvoje', 'tvůj', 'ty', 'určitě', 'už', 'vám', 'vámi', 'vás', 'váš',
                             'vaše',
                             'vaši', 've', 'večer', 'vedle', 'vlastně', 'všechno', 'všichni', 'vůbec', 'vy', 'vždy',
                             'za',
                             'zač',
                             'zatímco', 'ze', 'že'}

        self.en_stopwords = {'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've",
                             "you'll",
                             "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she',
                             "she's",
                             'her', 'hers', 'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs',
                             'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', "that'll", 'these', 'those',
                             'am',
                             'is',
                             'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does',
                             'did',
                             'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while',
                             'of',
                             'at',
                             'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before',
                             'after',
                             'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under',
                             'again',
                             'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any',
                             'both',
                             'each',
                             'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
                             'so',
                             'than',
                             'too', 'very', 's', 't', 'can', 'will', 'just', 'don', "don't", 'should', "should've",
                             'now',
                             'd', 'll',
                             'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't", 'didn', "didn't",
                             'doesn',
                             "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn', "isn't", 'ma',
                             'mightn',
                             "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan', "shan't", 'shouldn',
                             "shouldn't",
                             'wasn',
                             "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't"}

    def _read_file_names(self, file_list):
        with open(file_list) as f:
            file_names = f.readlines()
            file_names = [x.strip() for x in file_names]

            q = queue.Queue()
            for i in file_names:
                q.put(i)
                self._cnt_files += 1
            return q

    def _read_xml_file(self, file):
        try:
            with open(file, "r") as my_file:
                d = my_file.read()

            # if we have custom header, replace it with the original header
            if self._extra_header:
                with open(self._extra_header, "r") as mf:
                    extra_head = mf.read()
                d = d.split("\n", 2)[2]
                d = extra_head + d

            # --- SOME HARD CODED FIXES ---------------------------------------------
            # en la020120
            # d = d.replace("^N", "^M")
            d = d.replace('\x0e', '')  # replace hex 14
            # en la020707
            d = d.replace("</LATIMES2002></LATIMES2002>", "</LATIMES2002>")

            # cs ln020225.xml
            d = d.replace("< >", "")
            d = d.replace('<IMG SRC=" adresa, na které je soubor uložen ">', '')
            d = d.replace('<A NAME=" jméno kotvy ">', '')
            # -----------------------------------------------------------------------

            root = ETree.fromstring(d)
            self._current_file += 1
            return root
        except Exception as e:
            raise e

    def _next_file(self):
        if self._timer is None:
            self._timer = time.time()
        else:
            end_time = time.time() - self._timer
            sys.stdout.write('  %s sec\n' % str(round(end_time, 2)))
            self._timer = time.time()

        sys.stdout.write(">> >> indexing file [%s / %s]" % (str(self._current_file).zfill(3), self._cnt_files))
        while not self._file_queue.empty():  # while because some files may be broken
            file_name = self._file_queue.get()
            file = os.path.join(self._base_dir, file_name)
            try:
                root = self._read_xml_file(file)
            except Exception as e:
                file_name += '  ['
                file_name += str(e)
                file_name += ']'
                sys.stderr.write("Error: reading file: '%s'\n" % file_name)
                continue

            self._xml_to_document_list(root)
            return True

        else:
            end_time = time.time() - self._timer
            sys.stdout.write('  %s sec\n' % str(round(end_time, 2)))
            self._timer = None
            return False

    # Tokenization ...  is a step which splits longer strings of text into smaller pieces, or tokens.
    # Larger chunks of text can be tokenized into sentences, sentences can be tokenized into words, etc.
    # Further processing is generally performed after a piece of text has been appropriately tokenized.
    # Tokenization is also referred to as text segmentation or lexical analysis.
    # Sometimes segmentation is used to refer to the breakdown of a large chunk of text into pieces larger than words
    # (e.g. paragraphs or sentences), while tokenization is reserved for the breakdown process which results
    # exclusively in words.
    # ... Token ... is an instance of a sequence of characters in some particular document that are grouped together
    # as a useful semantic unit for processing.

    # Normalization ... Before further processing, text needs to be normalized.
    # series of related tasks meant to put all text on a level playing field: converting all text
    # to the same case (upper or lower), removing punctuation, converting numbers to their word equivalents, and so on.
    # Normalization puts all words on equal footing, and allows processing to proceed uniformly.
    # Normalizing text can mean performing a number of tasks,
    # usually 3 distinct steps:
    # (1) stemming,
    # (2) lemmatization
    # (3) everything else.
    #   3.1 all characters to lowercase
    #   3.2 remove numbers (or convert numbers to textual representations)
    #   3.3 remove punctuation (generally part of tokenization, but worth at this stage, even as confirmation)
    #   3.4 strip white space (also generally part of tokenization)
    #   3.5 remove default stop words (general English stop words)

    # ... Type ... is the class of all tokens containing the same character sequence.
    # Term ... is a (perhaps normalized) type that is included in the IR system's dictionary

    # maketrans
    # 1 arg : str.maketrans({'a': 'b', 'c': None})  == a->b c->''
    # 2 arg : str.maketrans('abc', 'xyz') == a->b b->y c->z
    # 3 arg : str.maketrans('abc', 'xyz', 'hij') == a->b b->y c->z  h->'' i->'' j->''
    def normalize(self, doc):
        if self.normalization == 'none':
            pass

        if 'nonum' in self.normalization:
            doc = doc.translate(self._delete_digit_translator)

        if 'nonum' in self.normalization and 'numnorm' in self.normalization:
            raise Exception("Can not normalize [nonum] and [numnorm] at the same time !")

        if 'numnorm' in self.normalization:
            doc = self.translate_num_to_string(doc)

        if 'accent' in self.normalization:
            doc = unidecode.unidecode(doc)

        if 'punct' in self.normalization:
            doc = doc.translate(self._delete_punct_translator)

        # convert to lowercase
        if 'casefold' in self.normalization:
            doc = doc.lower()

        doc2 = doc.replace(" ", "")
        assert doc == doc2, "token contains whitespaces you motherfucker!"
        return doc

    @staticmethod
    def extract_integers(my_str):
        result = []
        max_len = len(my_str)
        i = 0
        while True:
            if i >= max_len:
                break

            if my_str[i].isdigit():
                num = ''
                while i < max_len and my_str[i].isdigit():
                    num += my_str[i]
                    i += 1
                if num != '':
                    result.append(num)

            # not the digit now
            no_dig = ''
            while i < max_len and not my_str[i].isdigit():
                no_dig += my_str[i]
                i += 1
            if no_dig != '':
                result.append(no_dig)
        return result

    def translate_num_to_string(self, doc):
        lang = 'en'
        if self.lang == 'cs':
            lang = 'cz'

        # convert to text
        lst = self.extract_integers(doc)
        to_ret = ''
        for v in lst:
            if v.isdigit():
                num_in_str = num2words(int(v), lang=lang)
                to_ret += num_in_str.replace(" ", "")
            else:
                to_ret += v
        return to_ret

    def _xml_to_document_list(self, root):

        # for all documents in the file
        for child in root:
            doc_no = child.find('DOCNO').text

            doc_as_string = ''
            # for tags in this document
            for c in child:
                # we have some data and it is not in the excluded tag
                if c.text and len(c.text) > 0 and c.tag not in self._excluded_xml_tags:
                    doc_as_string += ' '
                    doc_as_string += c.text

            # doc_as_string = self.normalize(doc_as_string)

            # fill the queue with documents from current file
            self._doc_queue.put([doc_no, doc_as_string])

    def _next_document(self):
        if not self._doc_queue.empty():  # if we have some documents in memory, just load it
            doc_no, doc_data = self._doc_queue.get()
            self._doc_no = doc_no
            self._pos_in_doc = 0
            self._cnt_documents += 1
            self.tokenizer.set_text(doc_data)
            return True

        elif self._next_file():
            return self._next_document()

        else:
            return False

    def has_next(self):
        if self._prepared:
            return True
        else:
            x = self.next_lemma()
            if x:
                self._prepared = x
                return True
            return False

    def tokenize_string(self, string):
        self.tokenizer.set_text(string)
        self._single_string = True
        # reset some counters
        self._doc_no = 0
        self._pos_in_doc = 0
        # self._curr_sentence_len = 0
        # self._word_in_sentence = 0

    def num_of_documents(self):
        return self._cnt_documents

    def filter(self, lemma):

        # None
        if self.stop_word_removal == 'none':
            pass
        # Lexicon based
        elif self.stop_word_removal == 'lexicon-based':
            if self.lang == 'cs':
                if lemma in self.cz_stopwords:
                    return ''
            if self.lang == 'en':
                if lemma in self.en_stopwords:
                    return ''
        else:
            raise Exception("Stop word removal [%s] not yet implemented" % self.stop_word_removal)

        return lemma

    def next_lemma(self):

        if self._prepared:
            tmp = self._prepared  # already processed by this method
            self._prepared = None
            return tmp

        lemma_dict = self.tokenizer.next_lemma()

        # we have lemma
        # so we save its position in doc
        # normalize it and return it
        if lemma_dict:

            if self.term == 'lemma':
                lemma = lemma_dict['raw_lemma']
            elif self.term == 'word':
                lemma = lemma_dict['word']
            else:
                raise Exception("Term [%s] not yet implemented" % self.term)

            filtered_lemma = self.filter(lemma)

            normalized_raw_lemma = self.normalize(filtered_lemma)

            # if result of normalization is empty string, go to for next lemma
            if normalized_raw_lemma == '':
                return self.next_lemma()

            # print(normalized_raw_lemma)
            self._pos_in_doc += 1
            return self._doc_no, normalized_raw_lemma, self._pos_in_doc
        else:
            # text co jsme tam poslali je prazdny
            # je potreba dodat text

            if self._single_string:
                self._single_string = False
                return False

            if self._next_document():
                return self.next_lemma()

            return False

    # def _next_sentence(self): # todo -- ted nevolame nikdy next sentence
    #     if self._token_class.next_sentence():
    #         return True
    #
    #     # # try to read next sentence
    #     # if self._tokenizer.nextSentence(self._forms, self._tokens):
    #     #     self._tagger.tag(self._forms, self._lemmas)
    #     #     self._word_in_sentence = 0
    #     #     self._curr_sentence_len = len(self._lemmas)
    #     #     return True
    #
    #     else:
    #
    #
    #         # otherwise try to read next document
    #         if self._next_document():
    #             #                 print('loading next document')
    #             return self._next_sentence()
    #
    #         # no other files, we are at the end my friend
    #         return False

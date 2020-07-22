import os
import time
import xml.etree.ElementTree as ETree
import sys


class TopicLoader:
    def __init__(self, base_topic_dir, lang, typ, token_stream, vector_model):
        sys.stderr.write('Loading Topic Loader...\n')
        self.base_topic_dir = base_topic_dir
        self.lang = lang
        self.typ = typ
        self.vector_model = vector_model
        self.token_stream = token_stream

        self.count = 0
        self.string_topics = self._load_topics()

        self.vectorized_topics = None

    def _load_topics(self):
        sys.stderr.write('>> Loading topics: ')
        start_time = time.time()
        topic_file = os.path.join(self.base_topic_dir, 'topics-' + self.typ + '_' + self.lang + '.xml')
        topic_list = os.path.join(self.base_topic_dir, 'topics-' + self.typ + '.lst')
        topic_numbers = self._read_topic_numbers(topic_list)

        root = self._read_xml_file(topic_file)
        whole_topics = self._xml_to_document_list(root, topic_numbers)

        end_time = time.time() - start_time
        sys.stderr.write("success [%s sec] [%s]\n" % (str(round(end_time / 60, 2)), str(len(whole_topics))))

        return whole_topics

    def vectorize_topics(self, query_expansion, query_construction):
        sys.stderr.write('>> Vectorizing topics: ')
        start_time = time.time()

        # todo - query expansion and query construct
        if query_expansion == 'none':
            pass
        else:
            raise Exception("Query expansion [%s] not yet implemented" % query_expansion)

        if query_construction == 'title':
            part_for_query = 'title'
        elif query_construction == 'desc':
            part_for_query = 'desc'
        elif query_construction == 'narr':
            part_for_query = 'narr'
        else:
            raise Exception("Query construction [%s] not yet implemented" % query_construction)

        self.vectorized_topics = {}
        for topic in self.string_topics:
            data_to_vectorize = topic[part_for_query]
            vector = self._query_as_vector(data_to_vectorize)
            self.vectorized_topics[topic['num']] = vector

        self.count = len(self.vectorized_topics)

        end_time = time.time() - start_time
        sys.stderr.write("success [%s sec] [%s]\n" % (str(round(end_time / 60, 2)), str(self.count)))
        sys.stderr.write('--------------------------------\n')

    def _query_as_vector(self, query):
        token_total = 0
        token_unique = 0
        bla_bla = {}
        self.token_stream.tokenize_string(query)

        while self.token_stream.has_next():
            doc_no, token, position_in_doc = self.token_stream.next_lemma()
            token_total += 1

            if token in bla_bla:
                bla_bla[token] += 1
            else:
                bla_bla[token] = 1
                token_unique += 1

        better = {}
        # avg_t ... only from here
        avg = token_total / token_unique
        # TF_t_d ... only from here
        max_tf = 0.0
        anti_id = -1
        for token, tf_t_d in bla_bla.items():
            if tf_t_d > max_tf:
                max_tf = tf_t_d
            # wordID .. od nich
            found = self.vector_model.word_id(token)
            if found:
                word_id, df, tf_t_all_d = found
                df += 1
                tf_t_all_d += tf_t_d
                entropy = self.vector_model.get_entropy(token, tf_t_all_d)
            else:
                df = 1
                tf_t_all_d = tf_t_d
                entropy = 1.0
                word_id = anti_id
                anti_id -= 1
            better[word_id] = [tf_t_d, df, tf_t_all_d, entropy]

        assert max_tf > 0, "maximum {QUERY} is not greater than zero %s" % max_tf
        result = [max_tf, {}, avg]
        for i in sorted(better):
            result[1][i] = better[i]

        return result

    @staticmethod
    def _read_topic_numbers(file_list):
        with open(file_list) as f:
            topic_nums = f.readlines()
            topic_nums = [x.strip() for x in topic_nums]
            return topic_nums

    @staticmethod
    def _read_xml_file(file):
        try:
            with open(file, "r") as my_file:
                d = my_file.read()

            root = ETree.fromstring(d)
            return root
        except Exception as e:
            raise e

    @staticmethod
    def _xml_to_document_list(root, topic_numbers):

        whole_topics = []
        for child in root:  # top
            topic_num = child.find('num').text

            if topic_numbers and topic_num[8:] not in topic_numbers:  # skip unwanted topics
                continue

            topic = {}
            for c in child:  # num, title, desc, narr
                topic[c.tag] = c.text
            whole_topics.append(topic)
        return whole_topics

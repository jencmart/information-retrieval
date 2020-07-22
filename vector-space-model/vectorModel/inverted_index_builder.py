import pickle
import sys
import time
from abc import ABC, abstractmethod
import os
import math


class InvertedIndexBuilder:
    def __init__(self, token_stream, file_formatter, out_dir):
        self._token_stream = token_stream
        self._out_dir = out_dir
        self._file_formatter = file_formatter

    def run(self, force_recreate_files):
        base_s = '.inv'
        dm_s = '.docmap'

        # en_non-positional_lemma_no-lowercase
        type_p = self._file_formatter.typ  # bag of words
        lang_p = self._token_stream.lang  # cs
        term = self._token_stream.term  # lemma
        normalization = self._token_stream.normalization  # normalization
        stop_word_removal = self._token_stream.stop_word_removal  # compression

        sys.stderr.write("Loading Index file... [lang:%s, term:%s, norm:%s, sw:%s]\n" % (
        lang_p, term, normalization, stop_word_removal))

        file1 = os.path.join(self._out_dir,
                             type_p + '_' + lang_p + '_' + term + '_' + normalization + '_' + stop_word_removal + base_s)
        file2 = os.path.join(self._out_dir, lang_p + base_s + dm_s)

        if os.path.exists(file1) and os.path.exists(file2):
            if force_recreate_files:
                os.remove(file1)
                os.remove(file2)
            else:
                sys.stderr.write(">> Index file: found\n")
                return file1, file2

        sys.stderr.write(">> Index file:  not found\n")
        sys.stderr.write(">> >> Creating new index file...\n")

        start_time = time.time()

        # todok
        document_map = {}
        dictionary = {}

        # while we have some stuff in token_stream
        while self._token_stream.has_next():
            dictionary = self._file_formatter.insert_to_dictionary(document_map, dictionary, self._token_stream)

        num_of_documents = self._token_stream.num_of_documents()
        num_of_token_types = len(dictionary)
        self._file_formatter.save_dictionary(file1, dictionary, num_of_documents, num_of_token_types)
        self._save_document_map(file2, document_map)

        end_time = time.time() - start_time
        sys.stderr.write(">> >> Index file: created [%s min]\n" % str(round(end_time / 60, 2)))
        sys.stderr.write(">> Index file: found\n")
        return file1, file2

    @staticmethod
    def _save_document_map(file, document_map):
        with open(file, "w") as fp:
            for k, v in document_map.items():
                fp.write(k + '\n')

    @staticmethod
    def _enough_memory():
        return True

    def load_dictionary(self, inv_idx):
        return self._file_formatter.load_dictionary(inv_idx)


class AbstractFileBuilder(ABC):

    @abstractmethod
    def __init__(self, typ):
        self.typ = typ

    @abstractmethod
    def insert_to_dictionary(self, document_map, dictionary, token_stream):
        pass

    @abstractmethod
    def save_dictionary(self, file, dictionary, number_of_documents, number_of_lemmas):
        pass

    @abstractmethod
    def load_dictionary(self, file, direct=False):
        pass


class PositionalFileBuilder(AbstractFileBuilder):

    def __init__(self, typ):
        super().__init__(typ)

    def insert_to_dictionary(self, document_map, dictionary, token_stream):
        # def insertPositional(dictionary, tokenStream):
        #     # insert into the dictionary
        #     docID, token, position = tokenStream.next_lemma()
        #
        #     # if already in dictionary
        #     if (token in dictionary):
        #
        #         # moreover if doc exist
        #         if (docID in dictionary[token]):
        #             dictionary[token][docID].append(position)
        #         else:
        #             dictionary[token][docID] = [position]
        #     else:
        #         dictionary[token] = {docID: [position]}
        #     return dictionary
        pass

    def save_dictionary(self, file, dictionary, number_of_documents, number_of_lemmas):
        # def writePositional(file, dictionary):
        #     with open(file, "w") as f:
        #
        #         for i in sorted(dictionary):
        #
        #             w = i + ' '
        #             f.write(w)
        #
        #             for key, val in dictionary[i].items():
        #                 f.write("%s [" % key)
        #                 for item in val:
        #                     f.write("%s " % item)
        #                 f.write('] ')
        #             f.write('\n')
        pass

    def load_dictionary(self, file, direct=False):
        pass


# PIVOT NORMALIZATION
# pivoted normalization = [ (1 -slope) *pivot + slope * old_normalizatiot ] slope = 0.75
# pivot is set to the average cosine normalization factor
#  Generally, we can use the avg. num. of unique terms in a document (computed across the entire collection) as pivot

# PIVOT UNIQUE NORMALIZATION
# slope = 1.... no pivot ...

# WKI - pivot unique
# pivot unique = (1-slope)*pivot + slope * l_j == uniq_doc_d / (cnt vsech termu/cnt dokumetnu)
# We believe that average term frequency in a document
# is a better representative of the "verbosity" of a document.

# pro pivot potrebujeme  (1-slope)*pivot + slope*l_j
#   slope ... 0.2
#   pivot ... prumerny pocet distinct terms in document per colection
#         ... l_j / pocet_termu ?
# ...  average number of distinct terms per document in the entire collection
# ...  l_j  ... #  pocet_unique_terms_doc_j .. ruznych termu v dokumentu j .. hmh


class BOWFileBuilder(AbstractFileBuilder):

    def __init__(self, typ, ):
        super().__init__(typ)
        self.inv_map = None

    def insert_to_dictionary(self, document_map, dictionary, token_stream):
        # insert into the dictionary
        doc_no, token, position_in_doc = token_stream.next_lemma()

        # assign doc_id to the doc_no
        if doc_no in document_map:
            doc_id = document_map[doc_no]
        else:
            doc_id = len(document_map)
            document_map[doc_no] = doc_id
            if self.inv_map is None:
                self.inv_map = {doc_id: 0}  # od 0
            else:
                self.inv_map[doc_id] = 0  # od 0 !!!!!

        #  token exist ==> document exist ---> vic tohoto tokenu v tomto dokumentu
        if token in dictionary and doc_id in dictionary[token][2]:
            dictionary[token][0] += 1  # more overall
            # no new document
            dictionary[token][2][doc_id] += 1  # more in this doc [tf]

            # update the maximum
            if dictionary[token][2][doc_id] > self.inv_map[doc_id]:  # UPDATUJEME TADY
                self.inv_map[doc_id] = dictionary[token][2][doc_id]

        # token exist, document NOT exist
        elif token in dictionary:
            dictionary[token][0] += 1  # more over all (  sum_tf(t,d) )
            dictionary[token][1] += 1  # df(t) ( +1 for new document)
            dictionary[token][2][doc_id] = 1  # first in this doc [tf]
            if self.inv_map[doc_id] == 0:
                self.inv_map[doc_id] = 1

        # token NOT exist ( document NOT exist)
        else:
            dictionary[token] = [1, 1, {doc_id: 1}]  # sum_tf(t,d) df(t) , {docID: tf(t,d) }
            if self.inv_map[doc_id] == 0:
                self.inv_map[doc_id] = 1

        return dictionary

    def save_pickle(self, file, dict_term__0_1_dic_docID_tf, number_of_documents, number_of_lemmas):
        log_n = math.log(number_of_documents)

        # todo - tf_average == sum_tf_v_tomto_doc / pocet_slov_v_tomto_doc

        word_id = 0
        dic_docID__L0max_L1dic_wordID___tf_df_sum_tf_entropy_L2_avg_tf = {}
        dict_term__tuple_wordID_df_sumTF = {}

        for i in sorted(dict_term__0_1_dic_docID_tf):

            term = i  # read the term
            sum_tf_t = dict_term__0_1_dic_docID_tf[i][0]  # read the total frequency ( pocet vyskytu v cele sade )
            df = dict_term__0_1_dic_docID_tf[i][1]

            # calculate Entropy
            entropy = 1.0
            for doc_id, tf_t_d in dict_term__0_1_dic_docID_tf[i][2].items():  # pro vsechny dokumenty
                p_i_j = tf_t_d / sum_tf_t
                tmp = (p_i_j * math.log(p_i_j)) / log_n
                entropy += tmp

            # tf_average_in_doc_d =  sum_tf_in_doc_d / num_term_in_doc_d

            dict_term__tuple_wordID_df_sumTF[term] = [word_id, df, sum_tf_t]  # word_id, doc_freq

            for key, val in dict_term__0_1_dic_docID_tf[i][2].items():
                doc_id = key  # ID of the document
                tf_t_d = val  # term frequency in this document

                if doc_id in dic_docID__L0max_L1dic_wordID___tf_df_sum_tf_entropy_L2_avg_tf:
                    dic_docID__L0max_L1dic_wordID___tf_df_sum_tf_entropy_L2_avg_tf[doc_id][1][word_id] = [tf_t_d, df,
                                                                                                          sum_tf_t,
                                                                                                          entropy]  # unique
                    dic_docID__L0max_L1dic_wordID___tf_df_sum_tf_entropy_L2_avg_tf[doc_id][
                        2] += tf_t_d  # tady pocitame v podstate pocet slov v doc
                else:
                    dic_docID__L0max_L1dic_wordID___tf_df_sum_tf_entropy_L2_avg_tf[doc_id] = [self.inv_map[doc_id],
                                                                                              # maximum tf in doc D
                                                                                              {word_id: [tf_t_d,
                                                                                                         # tf_t_d
                                                                                                         df,  # df_t
                                                                                                         sum_tf_t,
                                                                                                         # tf_t_allD
                                                                                                         entropy]},
                                                                                              # entropy_t
                                                                                              tf_t_d]  # avg

            word_id += 1

        # calculate the average
        for k, v in dic_docID__L0max_L1dic_wordID___tf_df_sum_tf_entropy_L2_avg_tf.items():
            num_distinc_terms = len(dic_docID__L0max_L1dic_wordID___tf_df_sum_tf_entropy_L2_avg_tf[k][1])
            num_terms_in_doc = dic_docID__L0max_L1dic_wordID___tf_df_sum_tf_entropy_L2_avg_tf[k][2]
            dic_docID__L0max_L1dic_wordID___tf_df_sum_tf_entropy_L2_avg_tf[k][2] = num_terms_in_doc / num_distinc_terms

        to_write = [dic_docID__L0max_L1dic_wordID___tf_df_sum_tf_entropy_L2_avg_tf, dict_term__tuple_wordID_df_sumTF,
                    dict_term__0_1_dic_docID_tf]

        sys.stderr.write(">> >> Saving index file: ")
        with open(file, "wb") as f:
            pickle.dump(to_write, f)
        sys.stderr.write("success\n")

    def save_dictionary(self, file, dictionary, number_of_documents, number_of_lemmas):
        self.save_pickle(file, dictionary, number_of_documents, number_of_lemmas)

    def load_dictionary(self, file, direct=False):
        with open(file, 'rb') as pickle_file:
            x = pickle.load(pickle_file)
        dic_docID__dic___wordID___tf_df_sum_tf_entropy_avg_tf, dict_term__pair_word__id_df_t, dictionary = x
        return dic_docID__dic___wordID___tf_df_sum_tf_entropy_avg_tf, dict_term__pair_word__id_df_t, dictionary


class VectorModelFileBuilder(AbstractFileBuilder):

    def __init__(self, typ):
        super().__init__(typ)

    def insert_to_dictionary(self, document_map, dictionary, token_stream):
        # insert into the dictionary
        doc_no, token, position_in_doc = token_stream.next_lemma()

        # assign doc_id to the doc_no
        if doc_no in document_map:
            doc_id = document_map[doc_no]
        else:
            doc_id = len(document_map)  # od 0
            document_map[doc_no] = doc_id

        # if already in dictionary
        if token in dictionary:

            # moreover if doc exist
            if doc_id in dictionary[token][1]:
                dictionary[token][1][doc_id] += 1  # more in this doc
                dictionary[token][0] += 1  # more overall
            else:
                dictionary[token][1][doc_id] = 1  # first in this doc
                dictionary[token][0] += 1  # more over all

        else:
            dictionary[token] = [1, {doc_id: 1}]  # first over TF , first here DF
        return dictionary

    def save_dictionary(self, file, dictionary, number_of_documents, number_of_lemmas):
        # print("Saving index to the file...", end='')
        with open(file, "w") as myfile:
            myfile.write(number_of_documents + ' ' + number_of_lemmas + '\n')
            for i in sorted(dictionary):

                w = i + ' '
                myfile.write(w)  # write the key -- "pes"
                myfile.write(str(dictionary[i][0]))  # TF

                for key, val in dictionary[i][1].items():
                    myfile.write(" %s %s" % (key, val))  # DOCNO DF
                myfile.write('\n')

    def load_dictionary(self, file, direct=False):

        with open(file) as fp:
            line = fp.readline()
            r = line.split(" ")
            n = int(r[0])  # docs
            # v = int(r[1])  # words
            word_id = 0
            dic_docID__dic__wordID__tf_df = {}
            dict_term__pair_word__id_df_t = {}

            # start with the first word
            line = fp.readline()
            while line:
                r = line.split(" ")

                term = r[0]  # read the term
                max_df_t = int(r[1])  # read the total frequency ( pocet vyskytu v cele sade )
                # df bude teda ... pocet dokumentu ve kterych se vyskytuje
                # v nasem pripade id cnt , id cnt ...
                # tedy
                df = len(r) / 2

                # entropy <<<<<<<<<<
                if not direct:
                    entropy = 1.0
                    for i in range(2, len(r), 2):
                        tf_t_d = int(r[i + 1])
                        p_i_j = tf_t_d / max_df_t  # tf_i_j
                        entropy += (p_i_j * math.log(p_i_j, 2)) / n

                    dict_term__pair_word__id_df_t[term] = [word_id, df, max_df_t, entropy]  # word_id, doc_freq

                for i in range(2, len(r), 2):
                    doc_id = int(r[i])  # ID of the document
                    tf_t_d = int(r[i + 1])  # term frequency in this document

                    if direct:  # no df_t idf, just term frequency in current document [OK]
                        dic_docID__dic__wordID__tf_df[term] = tf_t_d

                    else:
                        if doc_id in dic_docID__dic__wordID__tf_df:
                            dic_docID__dic__wordID__tf_df[doc_id][word_id] = [tf_t_d, df, max_df_t, entropy]  # unique
                        else:
                            dic_docID__dic__wordID__tf_df[doc_id] = {word_id: [tf_t_d, df, max_df_t, entropy]}

                line = fp.readline()
                word_id += 1

        return dic_docID__dic__wordID__tf_df, dict_term__pair_word__id_df_t

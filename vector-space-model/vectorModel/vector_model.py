import math
import sys
import time


class VectorModel:
    def __init__(self, file_builder, inv_idx_file):
        sys.stderr.write(">> Loading inverted index: ")

        start_time = time.time()
        self.dic_docID__L0max_L1dic_wordID___tf_df_sum_tf_entropy_L2_avg_tf, self.dict_term__tuple_wordID_df_sumTF, self.dict_term__0_1_dic_docID_tf = file_builder.load_dictionary(inv_idx_file)

        self._num_of_docs = len(self.dic_docID__L0max_L1dic_wordID___tf_df_sum_tf_entropy_L2_avg_tf)
        self._num_of_terms = len(self.dict_term__tuple_wordID_df_sumTF)
        end_time = time.time() - start_time

        sys.stderr.write(
            "success [%s sec] [terms: %s, docs: %s]\n" % (round(end_time, 2), self._num_of_terms, self._num_of_docs))
        sys.stderr.write('--------------------------------\n')
        self.term_weighting = None
        self.document_frequency_weighting = None
        self.vector_normalization = None
        self.cached_version = None
        self.pivot_pivot = None
        self.pivot_slope = None

    def normalize(self, vect):
        # VECTOR NORMALIZATION d_j .. j doc
        if self.vector_normalization == 'none':
            pass
        elif self.vector_normalization == 'cosine':
            norm = self._norm(vect)
            for k, v in vect.items():
                vect[k] = v / norm
        elif self.vector_normalization == 'pivot-unique':
            # l_j = num of distinct terms in document j
            l_j = len(vect)
            # slope ~ 0.2
            slope = self.pivot_slope
            # pivot = average distinct terms per document
            if self.pivot_pivot == 'avg-len':
                pivot = self._num_of_terms / self._num_of_docs
            else:
                pivot = self.pivot_pivot
            norm = (1 - slope) * pivot + (slope * l_j)
            for k, v in vect.items():
                vect[k] = v / norm
        else:
            raise Exception("Vector normalization [%s] not yet implemented" % self.vector_normalization)

        return vect

    #                                 tf_ df_  sum_tf_  entropy , max, avg
    def calculate_one_weight(self, tf_t_d, df_t, sumD_tf_t, entropy_t, maxD_tf, avgD_tf):
        log_base = 2  # todo - log base

        # DOCUMENT FREQUENCY == global weight g_i [i=term_i]
        if self.document_frequency_weighting == 'none':
            idf_t = 1.0
        elif self.document_frequency_weighting == 'idf':
            idf_t = math.log(self._num_of_docs / df_t, log_base)
        elif self.document_frequency_weighting == 'idf-squared':
            idf_t = math.log(self._num_of_docs / df_t, log_base)
        elif self.document_frequency_weighting == 'probabilistic-idf':
            idf_t = math.log((self._num_of_docs - df_t) / df_t, log_base)
        elif self.document_frequency_weighting == 'GFIDF':
            idf_t = math.log(sumD_tf_t / df_t, log_base)
        elif self.document_frequency_weighting == 'entropy':
            idf_t = entropy_t
        else:
            raise Exception("Document freq. weighting [%s] not yet implemented" % self.document_frequency_weighting)

        # TERM WEIGHTING == local weight t_i_j i term, j doc
        if self.term_weighting == 'bool':
            w_t_d = 1.0
        elif self.term_weighting == 'natural':  # term freq
            w_t_d = tf_t_d
        elif self.term_weighting == 'log':
            w_t_d = 1 + math.log(tf_t_d, log_base)
        elif self.term_weighting == 'log-average':
            w_t_d = (1 + math.log(tf_t_d, log_base)) / (1 + math.log(avgD_tf, log_base))
        elif self.term_weighting == 'augmented':
            k = 0.5
            w_t_d = k + ((0.5 * tf_t_d) / maxD_tf)
        else:
            raise Exception("Term weighting [%s] not yet implemented" % self.term_weighting)

        tf_idf = w_t_d * idf_t
        return tf_idf

    @staticmethod
    def _dot(v1, v2):
        v1 = [(k, v) for k, v in v1.items()]
        v2 = [(k, v) for k, v in v2.items()]

        i = 0
        j = 0
        d1_len = len(v1)
        d2_len = len(v2)

        dot = 0.0
        while True:
            if i >= d1_len or j >= d2_len:
                break

            if v1[i][0] == v2[j][0]:
                dot += v1[i][1] * v2[j][1]
                i += 1
                j += 1
                continue

            if v1[i][0] < v2[j][0]:
                while i < d1_len and v1[i][0] < v2[j][0]:
                    i += 1
                continue

            if v2[j][0] < v1[i][0]:
                while j < d2_len and v2[j][0] < v1[i][0]:
                    j += 1
                continue
        return dot

    @staticmethod
    def _norm(v):
        sq_sum = 0.0

        for k, va in v.items():
            sq_sum += va * va
        return math.sqrt(sq_sum)

    @staticmethod
    def add(v1, v2, subt=None):
        v1 = [(k, v) for k, v in v1.items()]  # list of key value pairs
        v2 = [(k, v) for k, v in v2.items()]

        i = 0
        j = 0
        d1_len = len(v1)
        d2_len = len(v2)

        res_vec = {}
        while True:

            # das end
            if i >= d1_len and j >= d2_len:
                break

            # only v2
            if i >= d1_len:
                while j < d2_len :
                    if subt is None:
                        res_vec[v2[j][0]] = v2[j][1]
                    else:
                        res_vec[v2[j][0]] = -1 * v2[j][1]
                    j += 1

            # only v1
            if j >= d2_len:
                while i < d1_len:
                    res_vec[v1[i][0]] = v1[i][1]
                    i += 1
                continue

            if v1[i][0] == v2[j][0]:  # sum
                if subt is None:
                    res_vec[v1[i][0]] = v1[i][1] + v2[j][1]
                else:
                    res_vec[v1[i][0]] = v1[i][1] - v2[j][1]
                i += 1
                j += 1
                continue

            if v1[i][0] < v2[j][0]:  # use v1
                while i < d1_len and v1[i][0] < v2[j][0]:
                    res_vec[v1[i][0]] = v1[i][1]
                    i += 1
                continue

            if v2[j][0] < v1[i][0]:  # use v2
                while j < d2_len and v2[j][0] < v1[i][0]:
                    if subt is None:
                        res_vec[v2[j][0]] = v2[j][1]
                    else:
                        res_vec[v2[j][0]] = -1 * v2[j][1]
                    j += 1
                continue
        return res_vec

    @staticmethod
    def multiply(v1, val):
        for k, v in v1.items():
            v1[k] = v * val
        return v1

    def calculate_centroids(self, doc_id_list, k, beta, gamma):
        # first k documents == first centroid
        centroid1 = {}
        centroid2 = {}
        cnt = 0
        for doc_id in doc_id_list:
            d_wordID_tfidf = self.cached_version[doc_id]
            if cnt < k:
                centroid1 = self.add(centroid1, d_wordID_tfidf)
            else:
                centroid2 = self.add(centroid2, d_wordID_tfidf)
            cnt += 1

        cnt = cnt - k
        if cnt < 0:
            cnt = cnt * -1

        val1 = beta/k
        val2 = gamma/cnt

        for k, v in centroid1.items():
            centroid1[k] = v * val1

        for k, v in centroid2.items():
            centroid2[k] = v * val2

        return centroid1, centroid2

    def _cos_similarity(self, d1, d2, ):
        dot_d1_d2 = self._dot(d1, d2)

        d1_norm = self._norm(d1)
        d2_norm = self._norm(d2)

        p = (d1_norm * d2_norm)
        if p == 0:
            return 0.0

        return dot_d1_d2 / p

    def word_id(self, token):
        if token in self.dict_term__tuple_wordID_df_sumTF:
            x = self.dict_term__tuple_wordID_df_sumTF[token]
            wID, df, sumTF = x
            return wID, df, sumTF
        return None

    def get_entropy(self, term, tf_t_allD):
        entropy = 1.0
        log_n = math.log(self._num_of_docs + 1)

        for doc_id, tf_t_d in self.dict_term__0_1_dic_docID_tf[term][2].items():  # pro vsechny dokumenty
            p_i_j = tf_t_d / tf_t_allD
            tmp = (p_i_j * math.log(p_i_j)) / log_n
            entropy += tmp
        return entropy

    def similarity_all_queries_at_one(self, cached_queries_dic_qName__dic_wordID_tfidf, metric):
        pass

    def cache_this(self):
        sys.stderr.write(">> Caching Vector model: ")

        start_time = time.time()

        self.cached_version = {}

        for doc_id, L0max_L1dic_wordID___tf_df_sum_tf_entropy_L2_avg_tf in self.dic_docID__L0max_L1dic_wordID___tf_df_sum_tf_entropy_L2_avg_tf.items():
            d_wordID_tfidf = self.calculate_weights_of_one_document(L0max_L1dic_wordID___tf_df_sum_tf_entropy_L2_avg_tf)
            self.cached_version[doc_id] = d_wordID_tfidf

        end_time = time.time() - start_time
        sys.stderr.write("success [%s sec] \n" % (round(end_time, 2)))

    def similarity(self, query_dic_wordID__TF_DF_sumTF_entropy_avgTF, metric, precached):
        res = {}

        if not precached:
            q_wordID__tfidf = self.calculate_weights_of_one_document(query_dic_wordID__TF_DF_sumTF_entropy_avgTF)
        else:
            q_wordID__tfidf = query_dic_wordID__TF_DF_sumTF_entropy_avgTF

        # cached version
        for doc_id, d_wordID_tfidf in self.cached_version.items():
            # duplicated code
            if metric == 'cosine-sim':
                similarity = self._cos_similarity(q_wordID__tfidf, d_wordID_tfidf)
            else:
                raise Exception("Similarity measurement [%s] not yet implemented" % metric)

            if similarity in res:
                res[similarity].append(doc_id)
            else:
                res[similarity] = [doc_id]

        return res

    def calculate_weights_of_one_document(self, L0max_L1dic_wordID___tf_df_sum_tf_entropy_L2_avg_tf):
        res = {}
        max = L0max_L1dic_wordID___tf_df_sum_tf_entropy_L2_avg_tf[0]
        dic = L0max_L1dic_wordID___tf_df_sum_tf_entropy_L2_avg_tf[1]
        avg = L0max_L1dic_wordID___tf_df_sum_tf_entropy_L2_avg_tf[2]
        assert max > 0, "MAX <= 0 ; during calculating weights [%s]" % max
        for wordID, tup in dic.items():
            weight = self.calculate_one_weight(tup[0], tup[1], tup[2], tup[3], max, avg)
            res[wordID] = weight
        # finally normalize the shit
        normalized = self.normalize(res)
        return normalized

    def set_weighting(self, term_weighting, document_frequency_weighting, vector_normalization, pivot_pivot, pivot_slope):
        self.term_weighting = term_weighting
        self.document_frequency_weighting = document_frequency_weighting
        self.vector_normalization = vector_normalization
        self.pivot_pivot = pivot_pivot
        self.pivot_slope = pivot_slope
        self.cache_this()

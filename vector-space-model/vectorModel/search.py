import operator
import sys
import time


class Search:
    def __init__(self, document_map,
                 term_weighting,
                 document_frequency_weighting,
                 vector_normalization,
                 similarity_measurement,
                 pivot_pivot,
                 pivot_slope,
                 vector_model,
                 token_stream,
                 topic_loader
                 ):

        self.pivot_pivot = pivot_pivot
        self.pivot_slope = pivot_slope

        self.topic_loader = topic_loader

        sys.stderr.write("Loading search utility... [t:%s, d:%s, n:%s]\n" % (term_weighting,
                                                                             document_frequency_weighting,
                                                                             vector_normalization))
        # self._file_builder = file_builder
        self._doc_map = self._load_doc_map(document_map)

        self.similarity_measurement = similarity_measurement
        self.vector_model = vector_model
        self.token_stream = token_stream

        vector_model.set_weighting(term_weighting, document_frequency_weighting, vector_normalization, pivot_pivot,
                                   pivot_slope)
        # self.calculate_weights()
        sys.stderr.write('--------------------------------\n')
        sys.stderr.flush()

    @staticmethod
    def _load_doc_map(file):
        doc_id_map = []
        with open(file, 'r') as f:
            line = f.readline()
            while line:
                doc_id_map.append(line[:-1])
                line = f.readline()

        return doc_id_map

    def find_top_k(self, k, dic_wordID__TF_DF_sumTF_entropy_avgTF, precached):

        res = self.vector_model.similarity(dic_wordID__TF_DF_sumTF_entropy_avgTF, self.similarity_measurement,
                                           precached)

        lst_docNO_simil_docID = []

        for s_val in sorted(res, reverse=True):  # sort the results
            for doc_id in res[s_val]:  # if same similarity, add all of them
                if k > 0:
                    doc_no = self._doc_map[doc_id]
                    lst_docNO_simil_docID.append([doc_no, s_val, doc_id])
                    k -= 1
                else:
                    return lst_docNO_simil_docID

        return lst_docNO_simil_docID

    def get_query_vector(self, qid):
        # todo - for this one reason cached vectorized topics maybe worh it
        query_dic_wordID__TF_DF_sumTF_entropy_avgTF = self.topic_loader.vectorized_topics[qid]
        q_term_id__tfidf = self.vector_model.calculate_weights_of_one_document(
            query_dic_wordID__TF_DF_sumTF_entropy_avgTF)
        return q_term_id__tfidf

    def run_search(self, cnt_res, custom_vectorized=None):
        curr = 1
        to_write = []

        precached = False
        if custom_vectorized:
            tot = len(custom_vectorized)
            data = custom_vectorized
            precached = True
        else:
            tot = self.topic_loader.count
            data = self.topic_loader.vectorized_topics

        # topics = self.topic_loader.vectorized_topics
        for qid, dic_wordID__TF_DF_sumTF_entropy_avgTF in data.items():
            sys.stdout.write('Searching...(' + str(curr).zfill(2) + '/' + str(tot) + ')')
            sys.stdout.flush()

            # obtain result
            start_time = time.time()
            lst_docNO_simil_docID = self.find_top_k(cnt_res, dic_wordID__TF_DF_sumTF_entropy_avgTF, precached)

            end_time = time.time() - start_time
            sys.stdout.write('  %s sec\n' % str(round(end_time, 2)))
            sys.stdout.flush()

            to_write.append([lst_docNO_simil_docID, qid])
            curr += 1
        sys.stdout.flush()

        return to_write

    @staticmethod
    def select_top_importatant(query, limit_query_size):
        # [(3, 4), (4, 3), (1, 2), (2, 1), (0, 0), (51, 0)]
        sorted_x = sorted(query.items(), key=operator.itemgetter(1), reverse=True)

        res = {}
        for i in sorted_x:
            if limit_query_size <= 0:
                break
            res[i[0]] = i[1]
            limit_query_size -= 1

        return res

    # -- NON ROCCHIO --
    # 1. select top k documents
    # 2. select 20-30 (indicative number) terms from these documents using for instance tf-idf weights.
    # 3. Do Query Expansion, add these terms to query, and then match the returned documents for this query
    # 4. Return results of this query

    # -- ROCCHIO --
    # 1. select top k documents
    # 2. calculate centroids and find separation
    # 3. Do Query Expansion, using new vector, then match the returned documents for this query
    # 4. Return results of this query
    # ---- Nearest centroid classifier ------------
    def rocchio_nearest_centroid(self, lst_results_qid, cnt_res, alpha, beta, gamma, limit_query_size, k=10):
        query_no = 1
        new_vectorized = {}
        a_start_time = time.time()
        sys.stdout.flush()
        sys.stderr.flush()
        sys.stderr.write('Rocchio pseudo-relevance... [k:%s, a:%s, b:%s, g:%s, lim:%s]\n' % (k, alpha, beta, gamma, limit_query_size))
        for results_qid in lst_results_qid:
            sys.stdout.write(">> Calculating centroid for query...(%s/%s) " % (str(query_no).zfill(2), len(lst_results_qid)))
            start_time = time.time()

            query_no += 1
            lst_doc_no_simil_doc_id = results_qid[0]
            qid = results_qid[1]

            doc_id_list = []
            for docNO_simil_docID in lst_doc_no_simil_doc_id:
                doc_id = docNO_simil_docID[2]
                doc_id_list.append(doc_id)
            centroid_1, centroid_2 = self.vector_model.calculate_centroids(doc_id_list, k, beta, gamma)

            # dic_wordID__TF_DF_sumTF_entropy_avgTF
            old_query = self.get_query_vector(qid)
            new_query = self.vector_model.multiply(old_query, alpha)

            new_query = self.vector_model.add(new_query, centroid_1)
            if gamma > 0.0:
                new_query = self.vector_model.add(new_query, centroid_2, '-')
            end_time = time.time() - start_time

            if limit_query_size:
                if len(new_query) > limit_query_size:
                    sys.stdout.write('trim [%s -> %s] ' % (len(new_query), limit_query_size))
                    new_query = self.select_top_importatant(new_query, limit_query_size)

            sys.stdout.write("[%s -> %s] [%s sec]\n" % (len(old_query), len(new_query), round(end_time, 2)))

            new_vectorized[qid] = new_query

        sys.stderr.flush()
        sys.stdout.flush()
        end_time = time.time() - a_start_time
        sys.stderr.write("Centroids calculated: [%s min]\n" % round(end_time/60, 2))
        sys.stderr.write('--------------------------------\n')
        sys.stderr.flush()
        sys.stdout.flush()
        to_write = self.run_search(cnt_res, new_vectorized)
        return to_write

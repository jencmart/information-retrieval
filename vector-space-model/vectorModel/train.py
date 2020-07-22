import os
import subprocess
import sys
import time

from vectorModel.factory import file_formatter_factory, token_stream_factory
from vectorModel.inverted_index_builder import InvertedIndexBuilder
from vectorModel.io_helpers import write_results_to_file
from vectorModel.search import Search
from vectorModel.topic_loader import TopicLoader
from vectorModel.vector_model import VectorModel

# -- NON BOW ----
# Part of speech tagging (POS)
# Chunking (shallow parsing) ---- POS -> Chunk -> sentence tree
# Named entity recognition  ---- ( word to category)
# Co-reference resolution   ---- (anaphora resolution) -- Andrew is hog --> HE is nice.
# Collocation extraction    ---- phrase as 1 word
# Relationship extraction   ---- “Mark and Emily married yesterday,”  -->  information that Mark is Emily’s husband.

# Stop-word removal is appropriate forB BOW processes (like TF-IDF)
# but common words like determiners and prepositions provide essential clues about sentence structure,
# and hence part of speech. Do not remove them if you want to detect sentence units.


def create_log_string(lst):
    s = ""
    for i in range(len(lst)):
        if i + 1 < len(lst):
            s += lst[i] + ", "
        else:
            s += lst[i] + "\n"
    return s


def write_to_logfile(log_file, s):
    if not os.path.exists(log_file):
        with open(log_file, 'w') as log:  # write csv header
            log.write('mp, lang, terms, normalizations, removal, term_weighting, '
                      'document_frequency_weighting, vector_normalization, similarity_measurement, query_construct, '
                      'query_expansion, relevance_feedback, num_of_results\n')

    with open(log_file, 'a') as log:
        log.write(s)


def train(c):
    log_file = c['train']['experiment_log']
    inv_idx_type = c['train']['inv_idx_type']  # non-positional # non-positional, positional

    # ### INDEX CREATION ####
    languages = c['train']['languages']  # current_lang = 'en'  # cs en
    terms = c['train']['terms']  # b) lemma, stem, word
    normalizations = c['train']['normalizations']  # a) none, num. normalization , lowercase (=case folding) ...
    force_rebuild = c['train']['force_rebuild']  # force_rebuild = False

    # ### INDEX COMPRESSION ###
    stop_word_removals = c['train']['stop_word_removals']  # c) none, lexicon-based, frequency-based, POS-based

    # ### VECTOR MODEL ###
    term_weightings = c['train']['term_weightings']  # e)  bool, natural, log, log_avg, augmented
    doc_frequency_weightings = c['train']['doc_frequency_weightings']  # f) none, idf, probabilistic-idf
    vector_normalizations = c['train']['vector_normalizations']  # g) none, cosine, pivoted
    similarity_measurements = c['train']['similarity_measurements']  # h) cosine, dice, jaccard

    # ### QUERY ###
    query_constructions = c['train']['query_constructions']  # d) using title, desc, narr
    relevance_feedback = c['train']['relevance_feedback']  # i) none, pseudo-relevance
    query_expansions = c['train']['query_expansions']  # j) none, thesaurus-based

    # ### RESULTS ###
    max_results = c['train']['max_results']
    base_run_name = c['train']['base_run_name']
    current_run_num = 0

    index_save_dir = c['inverted_index']['save_dir']
    if not os.path.exists(index_save_dir):
        os.makedirs(index_save_dir)

    result_dir = c['experiment']['paths']['base_result_dir']
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)

    query_topic_dir = c['experiment']['paths']['base_topic_dir']
    if not os.path.exists(query_topic_dir):
        raise Exception('Directory with the topics was not found [%s]' % query_topic_dir)

    base_truth_data_dir = c['experiment']['paths']['base_train_dir']
    if not os.path.exists(base_truth_data_dir):
        raise Exception('Directory with the correct answers was not found [%s]' % base_truth_data_dir)

    trec_eval_binary = c['experiment']['paths']['trec_eval_path']
    if not os.path.exists(trec_eval_binary):
        raise Exception('Trec eval binary was not found [%s]' % trec_eval_binary)

    # ###### for queries
    base_topic_dir = c['experiment']['paths']['base_topic_dir']
    base_result_dir = c['experiment']['paths']['base_result_dir']
    base_train_dir = c['experiment']['paths']['base_train_dir']
    trec_eval_path = c['experiment']['paths']['trec_eval_path']

    # for pseudo relevance
    top_k = c['train']['pseudo-relevance']['k']
    alpha = c['train']['pseudo-relevance']['k']
    beta = c['train']['pseudo-relevance']['beta']
    gamma = c['train']['pseudo-relevance']['gamma']
    limit_query_size = c['train']['pseudo-relevance']['limit-query-size']

    # pivot unique normalization
    pivot_pivot = c['train']['pivot-unique']['pivot']
    pivot_slope = c['train']['pivot-unique']['slope']

    parser = c['train']['parser']

    idx_num = 1
    cnt_indexes = len(languages) * len(terms) * len(normalizations) * len(stop_word_removals)  # cca 10 min ( pro novy )
    cnt_vector_models = len(query_constructions) * len(query_expansions) * len(term_weightings) * len(
        doc_frequency_weightings) * len(vector_normalizations) * len(similarity_measurements) * len(relevance_feedback) # cca 15 min
    vec_num = 1
    totaL_time = (cnt_indexes*cnt_vector_models*15 + cnt_indexes*10) / 60
    totaL_time = round(totaL_time, 2)
    sys.stderr.write('******************************************\n')
    sys.stderr.write('**********  TRAINING STARTED  ************\n')
    sys.stderr.write('******************************************\n')
    sys.stderr.write('****** Num. of Index files:   [%s] *******\n' % str(cnt_indexes).zfill(2))
    sys.stderr.write('****** Num. of Vector models: [%s] *******\n' % str(cnt_vector_models).zfill(2))
    sys.stderr.write('****** Num. of Runs:          [%s] *******\n' % str(cnt_indexes * cnt_vector_models).zfill(2))
    sys.stderr.write('******************************************\n')
    sys.stderr.write('****** Estimated time: [%s hod] *******\n' % str(totaL_time).zfill(4))
    sys.stderr.write('******************************************\n')
    sys.stderr.flush()
    sys.stdout.flush()

    for current_lang in languages:
        for current_terms in terms:
            for current_normalization in normalizations:
                for current_removal in stop_word_removals:

                    sys.stderr.write('****** Preparing index file (' + str(idx_num).zfill(2) + '/' + str(cnt_indexes).zfill(2) + ')\n')
                    sys.stderr.flush()

                    idx_num += 1

                    # Select the token stream based on the Language, and Term types
                    tok_str = token_stream_factory(c, current_lang, current_normalization, current_terms,
                                                   current_removal, parser)

                    # format of the output file
                    file_formatter = file_formatter_factory(inv_idx_type)

                    # initialize the file builder
                    index_builder = InvertedIndexBuilder(tok_str, file_formatter, c['inverted_index']['save_dir'])

                    # build the inverted indexes
                    inv_idx_file, document_map_file = index_builder.run(force_rebuild)

                    vector_model = VectorModel(index_builder, inv_idx_file)

                    # LOAD THE TOPIC FILE
                    topic_loader = TopicLoader(base_topic_dir, current_lang, 'train', tok_str, vector_model)

                    for current_query_construct in query_constructions:         # cca 15 min
                        for current_query_expansion in query_expansions:

                            # CREATE TOKENS and VECTOR MODEL
                            topic_loader.vectorize_topics(current_query_expansion, current_query_construct)

                            # ##########################
                            # ### VECTOR MODEL BUILD ###
                            ############################
                            for term_weighting in term_weightings:
                                for document_frequency_weighting in doc_frequency_weightings:
                                    for vector_normalization in vector_normalizations:
                                        for similarity_measurement in similarity_measurements:

                                            sys.stderr.write(
                                                '****** For index (' + str(idx_num).zfill(2) + '/' + str(cnt_indexes).zfill(2) + ') Preparing vector model (' + str(vec_num).zfill(2) + '/' + str(cnt_vector_models) + ')\n')
                                            sys.stderr.flush()
                                            vec_num += 1

                                            start_time = time.time()

                                            # Initialize the search
                                            search = Search(document_map_file,
                                                            term_weighting,
                                                            document_frequency_weighting,
                                                            vector_normalization,
                                                            similarity_measurement,
                                                            pivot_pivot,
                                                            pivot_slope,
                                                            vector_model,
                                                            tok_str,
                                                            topic_loader)

                                            # ################# SEARCH #################
                                            num_of_res = max_results

                                            sys.stderr.write("Searching:\n")
                                            sys.stderr.flush()
                                            sys.stdout.flush()

                                            to_write = search.run_search(num_of_res)

                                            # perform both relevance feedback types at once
                                            # Currently we need first to search without relevance feedback :-D
                                            for current_relevance_feedback in relevance_feedback:

                                                # experiment config
                                                run_name = base_run_name + str(current_run_num)
                                                current_run_num += 1

                                                if current_relevance_feedback == 'none':
                                                    pass
                                                elif current_relevance_feedback == 'pseudo-relevance':
                                                    to_write = search.rocchio_nearest_centroid(to_write, num_of_res,
                                                                                               alpha, beta, gamma,
                                                                                               limit_query_size,
                                                                                               k=top_k)
                                                else:
                                                    raise Exception(
                                                        "Feedback [%s] not yet implemented" % relevance_feedback)

                                                result_file = os.path.join(base_result_dir, run_name + '_' + 'train' +
                                                                           '_' + current_lang + '.res')

                                                # write results to result file
                                                write_results_to_file(result_file, to_write, run_name)

                                                # calculate mean precision
                                                mp = calculate_mean_precision(base_train_dir, result_file,
                                                                              trec_eval_path, current_lang)

                                                s = create_log_string([str(mp), current_lang, current_terms,
                                                                       current_normalization, current_removal,
                                                                       term_weighting, document_frequency_weighting,
                                                                       vector_normalization, similarity_measurement,
                                                                       current_query_construct, current_query_expansion,
                                                                       current_relevance_feedback, str(num_of_res)])
                                                write_to_logfile(log_file, s)
                                                end_time = round((time.time() - start_time) / 60, 2)
                                                start_time = time.time()

                                                sys.stderr.write('*********************************\n')
                                                sys.stderr.write("Search finished: [%s] [%s] [%s min]\n" %
                                                                 (current_relevance_feedback, mp, end_time))
                                                sys.stderr.write('*********************************\n')
                                                if current_relevance_feedback == 'pseudo-relevance':
                                                    sys.stderr.write('\n')

                                                sys.stdout.flush()
                                                sys.stderr.flush()

def get_mean_precision(ground_truth, re, trec_eval_path):
    proc = subprocess.Popen([trec_eval_path, '-M1000', ground_truth, re], stdout=subprocess.PIPE,
                            universal_newlines=True)
    (out, err) = proc.communicate()
    out = out.split('\n')
    for line in out:
        if line[:3] == 'map':
            return float(line.split()[2])


def calculate_mean_precision(base_train_dir, result_file, trec_eval_path, lang):
    ground_truth = os.path.join(base_train_dir,
                                'qrels-train_' + lang + '.txt')
    mp = get_mean_precision(ground_truth, result_file, trec_eval_path)
    return mp  # print("Average mean precision: %s" % str(mp))

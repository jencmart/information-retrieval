import yaml


def config_loader():
    with open("conf.yml", 'r') as ymlfile:
        configuration = yaml.load(ymlfile, Loader=yaml.Loader)
    return configuration


def write_results_to_file(result_file, to_write, run):
    rank = 0
    with open(result_file, 'w') as res_file:
        for results_qid in to_write:
            results = results_qid[0]
            qid = results_qid[1]
            for docNO_simil_docID in results:
                docno = docNO_simil_docID[0]
                sim = str(docNO_simil_docID[1])
                res_file.write(qid + '\t' + '0' + '\t' + docno + '\t' + str(rank) + '\t' + sim + '\t' + run + '\n')
                rank += 1
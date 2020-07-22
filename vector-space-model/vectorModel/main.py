from vectorModel.io_helpers import config_loader
from vectorModel.train import train


# Expected usage:
#  ./run -q topics.xml -d documents.lst -r run -o sample.res ...
#    -q topics.xml -- a file including topics in the TREC format (see Sec 5.2)
#    -d document.lst -- a file including document filenames (see Sec 5.1)
#    -r run -- a label identifying the experiment (to be inserted in the  result file as "run_id", see Sec 5.3)
#    -o sample.res -- an output file (see Sec 5.3)
#    ... (additional parameters specific for your implementation)

if __name__ == '__main__':
    cfg = config_loader()

    if cfg['current_run']['type'] == 'train':
        train(cfg)


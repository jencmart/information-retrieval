# information-retrieval

NPFL103 Information Retrieval: Assignment 1
===========================================

Lecturer: Pavel Pecina <pecina@ufal.mff.cuni.cz>
Year: 2019/20

Contents of this document

 1. Introduction
 2. Goal and objectives
 3. Specification
 4. Package contents
 5. File formats
 6. Evaluation
 7. Submission
 8. Notes
 9. Grading
10. Plagiarism and joined work
11. Terms of use

1. Introduction 

This is the first assignment of the Information Retrieval (NPFL103) course at
the Faculty of Mathematics and Physics, Charles University.

Course details are available here: https://ufal.mff.cuni.cz/courses/npfl103

2.1 Goal

The goal of this assignment is to become familiar with vector space models, text
preprocessing, system tuning, and experimentation in Information Retrieval.

2.2 Objectives  

 - Develop an experimental retrieval system based on vector space model.
 - Experiment with methods for text processing, query construction, term and 
     document weighting, similarity measurement, etc.
 - Optimize the system on provided test collections.
 - Write a detailed report on your experiments.
 - Present your results during the course practicals.

3. Detailed specification

 A) Use a programming language of your choice and implement an experimental
    retrieval system based on vector space model. For a given set of documents
    and a set of topics, the system is expected to rank the documents according
    to decreasing relevance to the topics. You are allowed to use standard
    libraries. You are not allowed to use any IR-specific libraries/packages/
    frameworks (e.g. trees and hashes are OK, inverted index is not).   

    Expected usage:
    ./run -q topics.xml -d documents.lst -r run -o sample.res ...

    Where:
      -q topics.xml -- a file including topics in the TREC format (see Sec 5.2)
      -d document.lst -- a file including document filenames (see Sec 5.1)
      -r run -- a label identifying the experiment (to be inserted in the
         result file as "run_id", see Sec 5.3)
      -o sample.res -- an output file (see Sec 5.3)
      ... (additional parameters specific for your implementation)

    You will have to deal with the following issues:
     a) extraction of terms from the input data (data reading, tokenization,
        punctuation reamoval, ...)
     b) grouping terms based on equivalence classes (none, case folding,
        lemmatization, stemming, number normalization, ...)
     c) removing stopwords (none, frequency-based, POS-based, lexicon-based,
        ...)
     d) query construction (using title, desc, narr, ...)
     e) term weighting (boolean, natural, logarithm, log average, augmented,
        ...)
     f) document frequency weighting (none, idf, probabilistic idf, ...)
     g) vector normalization (none, cosine, pivoted, ...) 
     h) similarity measurement (cosine, Dice, Jaccard...)
     i) relevance feedback (none, pseudo-relevance, ...)
     j) query expansion (none, thesaurus-based, ...)
     
 B) Set up a baseline system (denoted as run-0) specified as follows:

    run-0 (baseline):
    - terms: word forms
    - lowercasing: no
    - removing stopwords: no
    - query construction: all word forms from "title"
    - term weighting: natural
    - document frequency weighting: none
    - vector normalization: cosine
    - similarity measurement: cosine
    - relevance feedback: none
    - query expansion: none
    
 C) Use the provided Czech and English test collections and generate results
    for the training and test topics for both the languages:

    Example usage:
    ./run -q topics-train_cs.xml -d documents_cs.lst -r run-0_cs -o run-0_train_cs.res

    Include at most 1000 top-ranked documents for each topic.

    You are exected to provide the following four files:
    - run-0_train_cs.res
    - run-0_test_cs.res
    - run-0_train_en.res
    - run-0_test_en.res
    
    The results for training topics can be evaluated using the trec_eval tool.
 
    Example usage:
    ./eval/trec_eval -M1000 qrels_train_cs.txt run-0_train_cs.res
    
    The evaluation methodology is described in Section 6.
        
 D) Modify the baseline system by employing alternative/more advanced methods
    for solving the issues and select the best combination (denoted as run-1)
    which optimizes the system's performance on the set of training topics
    (use Mean Average Precision as the main evaluation measure) for each of the
    two languages.
    
    You are allowed to use any third-party text processing/annotation tool
    (e.g. MorphoDiTa, available from http://ufal.mff.cuni.cz/morphodita, which
    usefull for lemmatzation and available for both Czech and English). You may
    use different approaches for Czech and for English (e.g. lemmatization for
    Czech, stemming for English).

    Justify your decisions by conducting comparative experiments. (For example,
    if you decide to index lemmas instead of word forms, show that a system
    based on forms performs worse on training topics. Or, if you decide to
    exclude some stop words from the index, show that such a system performs
    better than a system indexing all words. Or if you employ some query
    expansion technique, show that it improves results for the trainin topics).

    The only constraints are: i) the queries are constructed automatically
    as words from the topic titles only (i.e. you cannot use the topic
    descriptions and topic narratives to construct the queries) ii) retrieval
    is completely automatic (no user intervention is allowed).
    
    run-1 (constrained):
    - terms: ???
    - lowercasing: ???
    - removing stopwords: ???
    - query construction: automatic from titles only
    - term weighting: ???
    - document frequency weighting: ???
    - vector normalization: ???
    - similarity measurement: ???
    - relevance feedback: only pseudo-relevance-based techniques are allowed
    - query expansion: ???

    Generate result files of this system for the training topics and test
    topics for both Czech and English. Include at most 1000 top-ranked
    documents for each topic.

    You are exected to provide the following four files:
    - run-1_train_cs.res
    - run-1_test_cs.res
    - run-1_train_en.res
    - run-1_test_en.res
    
 E) Optionally, you can submit another system (denoted as run-2) with
    absolutely no restrictions. You can use modified queries and use external
    data resources (e.g. thesauri).
 
    run-2 (unconstrained):
    - terms: ???
    - lowercasing: ???
    - removing stopwords: ???
    - query construction: ???
    - term weighting: ???
    - document frequency weighting: ???
    - vector normalization: ???
    - similarity measurement: ???
    - relevance feedback: ???
    - query expansion: ???
    
    Again, generate result files for the training topics and test topics.
    Include at most 1000 top-ranked documents for each topic.

 F) Write a detailed report (in Czech or English) describing details of your
    system (including building instructions, if needed), all the submitted runs
    (including instructions how the result files were generated) all conducted
    experiments and report their results on the training topics. Discuss the
    results and findings. Compare the results and approaches for Czech and
    English.
    
    For all experiments, report "map" (Mean Average Precision) as the main
    evaluation measure nad "P_10" (Precision of the 10 first documents) as the
    secodary measure. For run-0 and run-1 with the training topics (both Czech
    and English) plot the Averaged 11-point averaged precision/recall graphs and
    include them in the report. 
    
 G) Prepare a short presentation (a few slides, 5-10 minutes) summarizing your
    approach, employed data structures, conducted experiments, results,
    decisions, unsolved issues etc., to be presented to the lecturer and
    your classmates during the practicals.  
    
4. Package contents

 - documents_cs -- a directory containing 221 xml files with the total of 81735
     documents in Czech (format description in Sec 5.1)

 - documents_en -- a directory containing 365 xml files with the total of 88110
     documents in Czech (format description in Sec 5.1)
   
 - documents_cs.lst -- a list of 221 filenames containing the Czech documents
 - documents_en.lst -- a list of 365 filenames containing the English documents

 - qrels-train_cs.xml -- manually assessed relevance judgements for the Czech
     training topics (format description in Sec 5.4)
 - qrels-train_en.xml -- manually assessed relevance judgements for the English
     training topics (format description in Sec 5.4)
 - qrels-test_cs.xml -- manually assessed relevance judgements for the Czech
     test topics (not provided to students)
 - qrels-test_en.xml -- manually assessed relevance judgements for the English
     test topics (not provided to students)

 - topics-train_cs.xml -- specification of the training topics in Czech
 - topics-train_en.xml -- specification of the training topics in English
 - topics-test_cs.xml -- specification of the test topics in Czech
 - topics-test_en.xml -- specification of the test topics in Czech

 - topics-test.lst  -- identifiers of the training topics
 - topics-train.lst -- identifiers of the test topics

 - sample-results.res -- example of result file (see Sec 5.3)

 - trec_eval-9.0.7.tar.gz -- the source code of the evaluation tool (see the
   included README for building instructions)

 - README -- this file
 
5. File formats

5.1 Document format

The document format uses a labeled bracketing, expressed in the style of SGML.
The SGML DTD used for verification at TREC/CLEF is included in the archive. The
philosophy in the formatting at NIST has been to preserve as much of the
original structure as possible, but to provide enough consistency to allow
simple decoding of the data.

Every document is bracketed by <DOC> </DOC> tags and has a unique document
number, bracketed by <DOCNO> </DOCNO> tags. The set of tags varies depending
on the language (see the DTD for more details). The Czech documents typically
contain the following tags (with corresponding end tags):
   
  <DOC>
  <DOCID>
  <DOCNO>
  <DATE>
  <GEOGRAPHY>
  <TITLE>
  <HEADING>
  <TEXT>

The English tag set is much richer. Generally all the textual content (in any
type of bracktets) can be indexed.

5.2 Topic format

Topic specification uses the following SGML markup:

  <top lang="cs">
  <num>
  ...
  </num>
  <title>
  ...
  </title>
  <desc>
  ...
  </desc>
  <narr>
  ...
  </narr>
  </top>

5.3 TREC result format 

The format of the system results (.res files) contains 5 tab-separated
columns:

  1. qid
  2. iter
  3. docno
  4. rank
  5. sim
  6. run_id

Example:
  10.2452/401-AH 0 LN-20020201065 0 0 baseline
  10.2452/401-AH 0 LN-20020102011 1 0 baseline

The important fields matter are "qid" (query ID, a string), "docno" (document
number, a string appearing in the DOCNO tags in the documents), "rank" (integer
starting from 0), "sim" (similarity score, a float) and "run_id" (identifying
the system/run name, must be same for one file). The "sim" field is ignore by
the evaluation tool but you are required to fill it.  The "iter" (string) field
is ignored and unimportant for this assignment.

5.4 Query relevance format 

Relevance for each "docno" to "qid" is determined from train.qrels, which
contains 4 columns:
  1. qid
  2. iter
  3. docno
  4. rel

The "qid", "iter", and "docno" fields are as described above, and "rel" is
a Boolean (0 or 1) indicating whether the document is a relevant response for
the query (1) or not (1).

Example:
 10.2452/401-AH 0 LN-20020201065 1
 10.2452/401-AH 0 LN-20020201066 0

 Document LN-20020201065 is relevant to topic 10.2452/401-AH.
 Document LN-20020201066 is not relevant to topic 10.2452/401-AH.
 
6. Evaluation

The evaluation tool is provided in the "trec_eval-9.0.7.tar.gz" package.
Consult the "README" file inside the package for detailed instructions. 

Evaluation is performed by executing:
 ./eval/trec_eval -M1000 train-qrels.dat sample.res 

 where
 -M1000 specifies the maximum number of documents per query (do not change
 this parameter).
 
The tool outputs a summary of evaluation statistics:

  runid -- run_id
  num_q -- number of queries
  num_ret -- number of returned documents
  num_rel -- number of relevant documents
  num_rel_ret -- number of returned relevant documents
  map -- mean average precision (this is the main evaluation measure).
  ...
  iprec_at_recall_0.00 -- Interpolated Recall - Precision Averages at 0.00 recall
  ...
  P_10 -- Precision of the 10 first documents

For details see  http://trec.nist.gov/pubs/trec15/appendices/CE.MEASURES06.pdf

7. Submission

Submission will be done by email. You will need a single (zip, tgz) package
containing:
  - the source code of your system and a "README" file with instructions how to
    build your system (if needed) and how to run the experiments.
  - The result files for training and test topics for at least run-0 and run-1
    for Czech and for English.
  - The "report.pdf" file with your written report.
  - The "slides.pdf" file with a few slides you will use for presentation
    during the practicals.

The run-0 result files must be obtained by running somthing like this:

  ./run -q topics-train_cs.xml -d documents_cs.lst -r run-0_cs -o run-0_train_cs.res
  ./run -q topics-train_en.xml -d documents_en.lst -r run-0_en -o run-0_train_en.res

which run the experiment and generates the training result files for Czech and
English.

  ./run -q topics-test_cs.xml  -d documents_cs.lst -r run-0_cs -o run-0_test_cs.res
  ./run -q topics-test_en.xml  -d documents_en.lst -r run-0_en -o run-0_test_en.res


run the experiment and generates the test result files for Czech and English.

For the best constrained system (run-1) and the best unconstrained system
(run-2) optionally, provide instructions how to execute the experiments and
obtain the results. Describe the systems/runs in detail in the report and
summarize in the presentation. 

Always include at most 1000 top ranked documents for each query in each run
(trec_eval will be executed  with parameter -M1000).

8. Notes

In this assignment, you are going to develop an experimental system and
efficiency of your implementation (optimization for speed and memory use)
will not be evaluated. However, it is advised not to ignore this aspect of
implementation since efficient implementation will allow faster experimentation
and mor experiments will (very likely) lead to better results.

9. Grading

You can earn up to 100 points: 

  0-80 points for the implementation of the system, experiments, results on the
       training topics, and the report.  
  0-15 points for the performance of the constrained system (run-1) on the test
       topics   
   0-5 points for the oral presentation

10. Plagiarism and joined work

No plagiarism will be tolerated. The assignment is to be worked on on your own.
All cases of confirmed plagiarism will be reported to the Student Office. You
are only allowed to share your performance scores on the training data.

11. Terms of use

The data in this package (documents, topics, relevance assessment) may not be
distributed and/or shared in any way and can be used only for the purpose of
completing the assignments of the NPFL103 Information Retrieval.

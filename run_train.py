"""Main script which triggers whole taining/evaluation process."""

import argparse

import yaml
from dataclasses_utils import get_dataloader
from general_utils import init_random_seed
from preprocess_tools import Tokenizer, read_src_tgt_dataset, default_tokenization
from seq2seq_model import Seq2SeqModel
from train_eval_utils import run_train_eval_pipeline, save_model
from task_specific_utilities import tokenize_src_doc, tokenize_tgt_doc


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-config',
                        dest="config",
                        default='./config.yaml',
                        type=str,
                        help='')
    args = parser.parse_args()
    with open(args.config, "r", encoding='utf-8') as ymlfile:
        config = yaml.load(ymlfile, Loader=yaml.FullLoader)

    init_random_seed(config['seed'])
    train_data = read_src_tgt_dataset(path=config['dataset_path'],
                                        filename=config['train_dataset'])
    eval_data = read_src_tgt_dataset(path=config['dataset_path'],
                                        filename=config['eval_dataset'])

    src_tokenizer = Tokenizer(tokenize_src_doc if config['custom_tokenization']
                              else default_tokenization)
    tgt_tokenizer = Tokenizer(tokenize_tgt_doc if config['custom_tokenization']
                              else default_tokenization)

    src_train_tokenized = src_tokenizer.tokenize_corpus(train_data['SRC'])
    tgt_train_tokenized = tgt_tokenizer.tokenize_corpus(train_data['TGT'])
    src_eval_tokenized = src_tokenizer.tokenize_corpus(eval_data['SRC'])
    tgt_eval_tokenized = tgt_tokenizer.tokenize_corpus(eval_data['TGT'])

    src_tokenizer.build_vocabulary(src_train_tokenized,
                                   min_token_count=config['src_min_token_count'],
                                   max_token_freq=config['src_max_token_freq'])
    tgt_tokenizer.build_vocabulary(tgt_train_tokenized,
                                   min_token_count=config['tgt_min_token_count'],
                                   max_token_freq=config['tgt_max_token_freq'])

    src_train_encoded = src_tokenizer.encode_corpus(src_train_tokenized)
    tgt_train_encoded = tgt_tokenizer.encode_corpus(tgt_train_tokenized)
    src_eval_encoded = src_tokenizer.encode_corpus(src_eval_tokenized)
    tgt_eval_encoded = tgt_tokenizer.encode_corpus(tgt_eval_tokenized)

    train_encoded = {
        'SRC': src_train_encoded,
        'TGT': tgt_train_encoded
    }

    eval_encoded = {
        'SRC': src_eval_encoded,
        'TGT': tgt_eval_encoded
    }

    train_dataloader = get_dataloader(train_encoded, config['batch_size'])
    eval_dataloader = get_dataloader(eval_encoded, config['batch_size'])

    src_vocabulary_size = len(src_tokenizer.vocabulary)
    tgt_vocabulary_size = len(tgt_tokenizer.vocabulary)

    init_random_seed(config['seed'])
    model = Seq2SeqModel(src_vocabulary_size=src_vocabulary_size,
                            tgt_vocabulary_size=tgt_vocabulary_size,
                            config=config)
    run_train_eval_pipeline(model=model,
                            train_dataloader=train_dataloader,
                            eval_dataloader=eval_dataloader,
                            config=config)
    if config['save_model']:
        save_model([src_tokenizer, tgt_tokenizer], model, config)

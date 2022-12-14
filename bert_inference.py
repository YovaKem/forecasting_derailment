# -*- coding: utf-8 -*-
"""

Code based on
    https://colab.research.google.com/drive/1P4Hq0btDUDOTGkCHGzZbAx1lb0bTzMMa

# Parameters
"""

"""# Libraries"""


# Libraries

import matplotlib.pyplot as plt
import pandas as pd
import torch
import numpy as np

# Preliminaries

from torchtext.legacy.data import Field, TabularDataset, BucketIterator, Iterator

# Models

import torch.nn as nn
from transformers import BertTokenizerFast as BertTokenizer
from transformers import BertForSequenceClassification, BertConfig

# Training

from transformers import AdamW

# Evaluation

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import seaborn as sns

import matplotlib.pyplot as plt
import os
from convokit import download, Corpus
import sys

data_prefix = 'base'
best_model_path = 'models/cga/{}/model.pt'.format(data_prefix)
source_folder = 'data/cga/'

device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
print(device)

"""# Preliminaries"""

tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

# Model parameter
PAD_INDEX = tokenizer.convert_tokens_to_ids(tokenizer.pad_token)
UNK_INDEX = tokenizer.convert_tokens_to_ids(tokenizer.unk_token)

RESULTS_DIR = "results"

# Fields

label_field = Field(sequential=False, use_vocab=False, batch_first=True, dtype=torch.float)
text_field = Field(use_vocab=False, tokenize=tokenizer.encode, include_lengths=True, batch_first=True,
                   pad_token=PAD_INDEX, unk_token=UNK_INDEX)
id_field = Field(sequential=False, use_vocab=False, dtype=torch.int32)


fields = {'src': ('src', text_field), 'tgt': ('tgt', label_field), 'reply': ('reply', text_field), 'convo_id': ('convo_id', id_field), 'comment_id': ('comment_id', id_field)}

# TabularDataset

valid , test = TabularDataset.splits(
  path = source_folder+data_prefix,
  train = None,
  validation = 'valid.json',
  test = 'test.json',
  format = 'json',
  fields = fields
)

# Iterators

valid_iter = BucketIterator(valid, batch_size=10, sort_key=lambda x: len(x.src),
                            device=device, train=True, sort=True, sort_within_batch=True)
test_iter = Iterator(test, batch_size=10, device=device, train=False, shuffle=False, sort=False)


"""# Models"""

class BERT(nn.Module):

    def __init__(self, hidden_dropout_prob=0.1, attention_probs_dropout_prob=0.1):
        super(BERT, self).__init__()

        configuration = BertConfig.from_pretrained('bert-base-uncased', hidden_dropout_prob=hidden_dropout_prob, attention_probs_dropout_prob=attention_probs_dropout_prob)
        self.encoder = BertForSequenceClassification.from_pretrained('bert-base-uncased', config=configuration)

    def forward(self, text, pad_mask, label):
        output = self.encoder(text, attention_mask=pad_mask, labels=label, return_dict=True)
        
        return output['loss'], output['logits']

"""# Training"""

# Save and Load Functions

def load_checkpoint(load_path, model):
    
    if load_path==None:
        return
    
    state_dict = torch.load(load_path, map_location=device)
    print(f'Model loaded from <== {load_path}')
    
    model.load_state_dict(state_dict['model_state_dict'])
    return state_dict['valid_loss']


# Evaluation Function
def evaluate(model, test_loader):
    y_pred = []
    y_true = []
    y_scores = []
    convo_ids = []
    comment_ids = []

    model.eval()
    with torch.no_grad():
        for batch in test_loader:
            comment_id = batch.comment_id
            convo_id = batch.convo_id
            labels = batch.tgt.type(torch.LongTensor)
            labels = labels.to(device)
            titletext = batch.src[0].type(torch.LongTensor).to(device)#, batch.src[1].to(device)) 
            pad_mask = ~titletext.data.eq(PAD_INDEX)
            output = model(titletext, pad_mask, labels)

            _, output = output
            output = torch.nn.functional.softmax(output, dim=1)
            scores = output[:, 1]
            preds = scores > 0.5
            y_pred.extend(preds.int().tolist())
            y_scores.extend(scores.tolist())
            y_true.extend(labels.tolist())
            comment_ids.extend(comment_id.tolist())
            convo_ids.extend(convo_id.tolist())
    
    #print('Classification Report:')
    #print(classification_report(y_true, y_pred, labels=[1,0], digits=4))
    
    output_df = {
        "convo_ids": convo_ids,
        "comment_ids": comment_ids,
        "prediction": y_pred,
        "score": y_scores,
        "true": y_true
    }
    
    return pd.DataFrame(output_df)

def get_pr_stats(preds, labels):
    tp = ((labels==1)&(preds==1)).sum()
    fp = ((labels==0)&(preds==1)).sum()
    tn = ((labels==0)&(preds==0)).sum()
    fn = ((labels==1)&(preds==0)).sum()
    p = tp / (tp + fp)
    r =  tp / (tp + fn)
    fpr = fp / (fp + tn)
    f1 = 2 / (((tp + fp) / tp) + ((tp + fn) / tp))
    print("Precision = {0:.4f}, recall = {1:.4f}".format(p, r))
    print("False positive rate =", fpr )
    print("F1 =", f1)
    return p, r, fpr, f1

best_model = BERT().to(device)

load_checkpoint(best_model_path, best_model)

forecasts_df = evaluate(best_model, test_iter)
out_path = best_model_path.replace('/', '_').split('.')[0] + '_predictions'
forecasts_df.to_csv(os.path.join(RESULTS_DIR, out_path + '.csv'))

def process_output(forecasts_df):

    model_type = best_model_path.split('/')[1]
    seed = best_model_path.split('/')[2]
    train_data = ''
    val_data = ''
    which_eval = 'test'
    #model_name = '{}_{}_{}_{}'.format(model_type, train_data, val_data, seed)

    # on-line
    labels = forecasts_df.groupby('convo_ids')['true'].max().values
    preds = forecasts_df.groupby('convo_ids')['prediction'].max().values
    acc = (preds==labels).sum()/len(preds)
    print('\n\n------------------------- Online classification -------------------------')
    print('Accuracy', acc)
    print('F-score')
    p, r, fpr, f1 = get_pr_stats(preds, labels)

    # first warning
    correct_pos_convos = forecasts_df.groupby(['convo_ids']).filter(lambda x : x['true'].max()==1 and x['prediction'].max()==1)
    first_warning = correct_pos_convos.groupby('convo_ids').apply(lambda x: x.sort_values(['prediction','comment_ids'], ascending=[False,True]))
    first_warning = first_warning.reset_index(drop=True).groupby('convo_ids', sort=False).first()['comment_ids']
    total_convo_length = correct_pos_convos.groupby('convo_ids').size()
    warning_offset = total_convo_length - first_warning
    stats = {'mean': warning_offset.mean(), 'max': warning_offset.max(), 'min': warning_offset.min(), 'mode': warning_offset.mode().item()}
    print('Stats for early warning', stats)

    #with open(os.path.join(RESULTS_DIR, 'results.csv'), 'a') as results_f:
    #    results_f.write('{},{},{},{},{},{},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f}\n'.format(model_type, train_data, val_data, seed, test_data, which_eval,
    #                                                                             100*acc, 100*p, 100*r, 100*fpr, 100*f1,
    #                                                                             stats['min'], stats['max'], stats['mode'], stats['mean']
    #                                                                             ))

    # last only
    last_comment_in_convo = forecasts_df.groupby('convo_ids')['comment_ids'].max()
    last_comment_in_convo = list(zip(last_comment_in_convo.index, last_comment_in_convo))
    _forecasts_df = forecasts_df.set_index(['convo_ids', 'comment_ids'])
    labels = _forecasts_df.loc[last_comment_in_convo]['true']
    preds = _forecasts_df.loc[last_comment_in_convo]['prediction']

    acc = (preds==labels).sum()/len(preds)
    print('\n\n------------------------- Last-only classification -------------------------')
    print('Accuracy', acc)
    print('F-score')
    p, r, fpr, f1 =  get_pr_stats(preds, labels)

    #with open(os.path.join(RESULTS_DIR, 'last_only_results.csv'), 'a') as last_only_results_f:
    #    last_only_results_f.write('{},{},{},{},{},{},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f}\n'.format(model_type, train_data, val_data, seed, test_data, which_eval,
    #                                                                             100*acc, 100*p, 100*r, 100*fpr, 100*f1))



    comments_until_derail_vals = list(warning_offset.values)
    # visualize the distribution of "number of comments until derailment" as a histogram (reproducing Figure 4 from the paper)
    plt.rcParams['figure.figsize'] = (10.0, 5.0)
    plt.rcParams['font.size'] = 24
    plt.hist(comments_until_derail_vals, bins=range(1, np.max(comments_until_derail_vals)), density=True)
    plt.xlim(1,10)
    plt.xticks(np.arange(1,10)+0.5, np.arange(1,10))
    #plt.yticks(np.arange(0,0.25,0.05), np.arange(0,25,5))
    plt.xlabel("Number of comments elapsed")
    plt.ylabel("% of conversations")

    plot_path = os.path.join(RESULTS_DIR, out_path+'.pdf')
    plt.savefig(plot_path, format='pdf')

process_output(forecasts_df)

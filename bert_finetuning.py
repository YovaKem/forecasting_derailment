# -*- coding: utf-8 -*-
"""

Code based on
    https://colab.research.google.com/drive/1P4Hq0btDUDOTGkCHGzZbAx1lb0bTzMMa

# Parameters
"""
data = 'cga' # 'cga' or 'cmv'
data_prefix = 'dynamic' # use "base" for static training and "dynamic" for dynamic training
source_folder = 'data/{}/'.format(data)
destination_folder = 'models/{}/'.format(data)

import os
if not os.path.exists(destination_folder):
    os.mkdir(destination_folder)

"""# Libraries"""

# Libraries

import matplotlib.pyplot as plt
import pandas as pd
import torch
import random

# Preliminaries

from torchtext.legacy.data import Field, TabularDataset, BucketIterator, Iterator

# Models

import torch.nn as nn
from transformers import BertConfig, BertTokenizer, BertForSequenceClassification

# Training

from transformers import AdamW

# Evaluation

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import seaborn as sns

device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
print(device)

"""# Preliminaries"""

tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

# Model parameter
MAX_SEQ_LEN = 128
PAD_INDEX = tokenizer.convert_tokens_to_ids(tokenizer.pad_token)
UNK_INDEX = tokenizer.convert_tokens_to_ids(tokenizer.unk_token)

# Fields

label_field = Field(sequential=False, use_vocab=False, batch_first=True, dtype=torch.float)
text_field = Field(use_vocab=False, tokenize=tokenizer.encode, include_lengths=True, batch_first=True,
                   pad_token=PAD_INDEX, unk_token=UNK_INDEX)
id_field = Field(sequential=False, use_vocab=False, dtype=torch.int32)


fields = {'src': ('src', text_field), 'tgt': ('tgt', label_field), 'reply': ('reply', text_field), 'comment_id': ('comment_id', id_field)}

# TabularDataset

train, valid, test = TabularDataset.splits(
  path = source_folder + data_prefix,
  train = 'train.json',
  validation = 'valid.json',
  test = 'test.json',
  format = 'json',
  fields = fields
)

# Iterators

train_iter = BucketIterator(train, batch_size=16, sort_key=lambda x: len(x.src),
                            device=device, train=True, sort=True, sort_within_batch=True)
valid_iter = BucketIterator(valid, batch_size=16, sort_key=lambda x: len(x.src),
                            device=device, train=True, sort=True, sort_within_batch=True)
test_iter = Iterator(test, batch_size=16, device=device, train=False, shuffle=False, sort=False)

"""# Models"""

class BERT(nn.Module):

    def __init__(self):
        super(BERT, self).__init__()

        options_name = "bert-base-uncased"
        configuration = BertConfig.from_pretrained(options_name, hidden_dropout_prob=0.1, attention_probs_dropout_prob=0.1)
        self.encoder = BertForSequenceClassification.from_pretrained(options_name, config=configuration)

    def forward(self, text, pad_mask, label):
        output = self.encoder(text, attention_mask=pad_mask, labels=label, return_dict=True)

        return output['loss'], output['logits']

"""# Training"""

# Save and Load Functions

def save_checkpoint(save_path, model, valid_loss):

    if save_path == None:
        return
    
    state_dict = {'model_state_dict': model.state_dict(),
                  'valid_loss': valid_loss}
    
    torch.save(state_dict, save_path)
    print(f'Model saved to ==> {save_path}')

def load_checkpoint(load_path, model):
    
    if load_path==None:
        return
    
    state_dict = torch.load(load_path, map_location=device)
    print(f'Model loaded from <== {load_path}')
    
    model.load_state_dict(state_dict['model_state_dict'])
    return state_dict['valid_loss']


def save_metrics(save_path, train_loss_list, valid_loss_list, global_steps_list):

    if save_path == None:
        return
    
    state_dict = {'train_loss_list': train_loss_list,
                  'valid_loss_list': valid_loss_list,
                  'global_steps_list': global_steps_list}
    
    torch.save(state_dict, save_path)
    print(f'Model saved to ==> {save_path}')


def load_metrics(load_path):

    if load_path==None:
        return
    
    state_dict = torch.load(load_path, map_location=device)
    print(f'Model loaded from <== {load_path}')
    
    return state_dict['train_loss_list'], state_dict['valid_loss_list'], state_dict['global_steps_list']

# Training Function

def train(model,
          optimizer,
          criterion = nn.BCELoss(),
          train_loader = train_iter,
          valid_loader = valid_iter,
          accum_count=1,
          num_epochs = 120,
          eval_every = len(train_iter) // 2,
          file_path = destination_folder + data_prefix,
          best_valid_loss = float("Inf")):
    
    # initialize running values
    running_loss = 0.0
    valid_running_loss = 0.0
    global_step = 0
    train_loss_list = []
    valid_loss_list = []
    global_steps_list = []

    # training loop
    model.train()
    no_improv = 0
    best_accuracy = 0
    cur_accum_count = 0
    for epoch in range(num_epochs):
        if no_improv > 15:
            continue
        for batch in train_loader:
            labels = batch.tgt.type(torch.LongTensor)
            labels = labels.to(device)
            titletext = batch.src[0].type(torch.LongTensor).to(device)
            pad_mask = ~titletext.data.eq(PAD_INDEX)
            output = model(titletext, pad_mask, labels)
            loss, _ = output

            optimizer.zero_grad()
            loss.backward()
            cur_accum_count += 1

            if cur_accum_count == accum_count:
              optimizer.step()
              cur_accum_count = 0

            # update running values
            running_loss += loss.item()
            global_step += 1

        # evaluation step

        model.eval()
        y_pred = []
        y_true = []

        with torch.no_grad():
        # validation loop
            for batch in valid_loader:
                labels = batch.tgt.type(torch.LongTensor)
                labels = labels.to(device)
                titletext =  batch.src[0].type(torch.LongTensor).to(device)#, batch.src[1].to(device))  
                pad_mask = ~ titletext.data.eq(PAD_INDEX)
                output = model(titletext, pad_mask, labels)
                loss, output = output
                y_pred.extend(torch.argmax(output, 1).tolist())
                y_true.extend(labels.tolist())
                valid_running_loss += loss.item()

        # evaluation
        average_train_loss = running_loss / len(train_loader)
        average_valid_loss = valid_running_loss / len(valid_loader)
        train_loss_list.append(average_train_loss)
        valid_loss_list.append(average_valid_loss)
        global_steps_list.append(global_step)

        accuracy = 100*sum([t==p for t, p in zip(y_true, y_pred)])/len(y_true)

        # resetting running values
        running_loss = 0.0
        valid_running_loss = 0.0
        model.train()

        # print progress
        print('Epoch [{}/{}], Step [{}/{}], Train Loss: {:.4f}, Valid Loss: {:.4f} Valid Acc: {:.2f}'
          .format(epoch+1, num_epochs, global_step, num_epochs*len(train_loader),
              average_train_loss, average_valid_loss, accuracy))

        if accuracy > best_accuracy:
            best_accuracy = accuracy
            save_checkpoint(file_path + '/' + 'model.pt', model, best_accuracy)
            no_improv = 0
        else:
            no_improv += 1

    save_metrics(file_path + '/' + 'metrics.pt', train_loss_list, valid_loss_list, global_steps_list)
    print('Finished Training!')

model = BERT().to(device)
optimizer = AdamW(model.parameters(), lr=6.7e-6)

train(model=model, optimizer=optimizer, accum_count=2)

train_loss_list, valid_loss_list, global_steps_list = load_metrics(destination_folder + '/metrics.pt')

"""# Evaluation"""

# Evaluation Function

def evaluate(model, test_loader):
    y_pred = []
    y_true = []

    model.eval()
    with torch.no_grad():
        for batch in test_loader:
            labels = batch.tgt.type(torch.LongTensor)
            labels = labels.to(device)
            titletext = batch.src[0].type(torch.LongTensor).to(device)#, batch.src[1].to(device)) 
            pad_mask = ~titletext.data.eq(PAD_INDEX)
            output = model(titletext, pad_mask, labels)

            _, output = output
            y_pred.extend(torch.argmax(output, 1).tolist())
            y_true.extend(labels.tolist())

    print('Classification Report:')
    print(classification_report(y_true, y_pred, labels=[1,0], digits=4))

    cm = confusion_matrix(y_true, y_pred, labels=[1,0])
    ax= plt.subplot()
    sns.heatmap(cm, annot=True, ax = ax, cmap='Blues', fmt="d")

    ax.set_title('Confusion Matrix')

    ax.set_xlabel('Predicted Labels')
    ax.set_ylabel('True Labels')

    ax.xaxis.set_ticklabels(['FAKE', 'REAL'])
    ax.yaxis.set_ticklabels(['FAKE', 'REAL'])

best_model = BERT().to(device)

load_checkpoint(destination_folder + '/model.pt', best_model)

evaluate(best_model, test_iter)


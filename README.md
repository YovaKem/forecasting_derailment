# Code for paper "Dynamic Forecasting of Conversation Derailment"

Finetune model with `python bert_finetuning.py`

Run inference with `python bert_inference.py`

### Citations

CGA dataset

```
@inproceedings{awry,
    title = "Conversations Gone Awry: Detecting Early Signs of Conversational Failure",
    author = "Zhang, Justine  and
      Chang, Jonathan  and
      Danescu-Niculescu-Mizil, Cristian  and
      Dixon, Lucas  and
      Hua, Yiqing  and
      Taraborelli, Dario  and
      Thain, Nithum",
    booktitle = "Proceedings of the 56th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)",
    month = jul,
    year = "2018",
    address = "Melbourne, Australia",
    publisher = "Association for Computational Linguistics",
    url = "https://www.aclweb.org/anthology/P18-1125",
    doi = "10.18653/v1/P18-1125",
    pages = "1350--1361",
}
```


CMV dataset

```
@inproceedings{trouble,
    title = "Trouble on the Horizon: Forecasting the Derailment of Online Conversations as they Develop",
    author = "Chang, Jonathan P.  and
      Danescu-Niculescu-Mizil, Cristian",
    booktitle = "Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing and the 9th International Joint Conference on Natural Language Processing (EMNLP-IJCNLP)",
    month = nov,
    year = "2019",
    address = "Hong Kong, China",
    publisher = "Association for Computational Linguistics",
    url = "https://www.aclweb.org/anthology/D19-1481",
    doi = "10.18653/v1/D19-1481",
    pages = "4743--4754",
}
```


Main work (BERT-based classification model with static and dynamic training)

```@inproceedings{kementchedjhieva-sogaard-2021-dynamic,
    title = "Dynamic Forecasting of Conversation Derailment",
    author = "Kementchedjhieva, Yova  and
      S{\o}gaard, Anders",
    booktitle = "Proceedings of the 2021 Conference on Empirical Methods in Natural Language Processing",
    month = nov,
    year = "2021",
    address = "Online and Punta Cana, Dominican Republic",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2021.emnlp-main.624",
    doi = "10.18653/v1/2021.emnlp-main.624",
    pages = "7915--7919",
    abstract = "Online conversations can sometimes take a turn for the worse, either due to systematic cultural differences, accidental misunderstandings, or mere malice. Automatically forecasting derailment in public online conversations provides an opportunity to take early action to moderate it. Previous work in this space is limited, and we extend it in several ways. We apply a pretrained language encoder to the task, which outperforms earlier approaches. We further experiment with shifting the training paradigm for the task from a static to a dynamic one to increase the forecast horizon. This approach shows mixed results: in a high-quality data setting, a longer average forecast horizon can be achieved at the cost of a small drop in F1; in a low-quality data setting, however, dynamic training propagates the noise and is highly detrimental to performance.",
}
```

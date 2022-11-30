# forecasting_derailment

Code for paper "Dynamic Forecasting of Conversation Derailment"

Finetune model with `python bert_finetuning.py`
Run inference with `python bert_inference.py`

Please cite

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

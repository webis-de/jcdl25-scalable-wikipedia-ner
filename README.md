# Scalable Recognition of Scientists’ Names in Wikipedia Articles

## Introduction

This repository contains the experimental data, source code, and datasets used for the **JCDL paper submission: “Scalable Recognition of Scientists’ Names in Wikipedia Articles.”**

It provides all resources necessary to reproduce the experiments and performance results described in the paper.

### System Used for Experiments

All reported performance results were produced on the following machine:

- **Device:** MacBook Air (M2, 8 GB RAM)

---

## Folder Structure

### `data/`

Contains datasets and outputs from different processing approaches.

- **`custom_parser/`**

  - `_revisions.json` – Script instructions for identifying the correct revision and its output destination.
  - `54` JSON files – Each contains the results of the latest run of the corresponding script.

- **`dataset/`**

  - `54` JSON files – Each includes a hyperlink to a Wikipedia article and manually annotated person named entities.

- **`hybrid_approach/`**

  - `_revisions.json` – Script instructions for identifying the correct revision and its output destination.
  - `54` JSON files – Each contains the results of the latest run of the corresponding script.

- **`spacy_pipeline/`**
  - `_revisions.json` – Script instructions for identifying the correct revision and its output destination.
  - `54` JSON files – Each contains the results of the latest run of the corresponding script.

---

### `scripts/`

Contains all Python scripts and supporting modules.

- **`requirements.txt`** – Lists Python dependencies required for the project.
- **`dumps/`** – A placeholder folder for Wikipedia article dumps in XML format. These files must be downloaded via `dump_downloader.py` before running the pipelines (see later sections).
- **`modules/`** – Utility functions and helper modules for the pipelines.
- **`dump_downloader.py`** – Downloads Wikipedia article dumps in XML format.
- **`wikipedia_hybrid_processor.py`** – Uses a hybrid approach to identify person named entities.
- **`wikipedia_parser_processor.py`** – Implements a wikitext, citation-centric approach pipeline.
- **`wikipedia_spacy_processor.py`** – Processes articles using a spaCy-based configuration.

---

## Experiment Setup

The code section of this repository serves mostly clarification purposes, as the `data` folder is already populated with the results of the latest script versions. Still, if it is necessary to re-run a pipeline, precise steps should be followed:

1. Make sure to install all dependencies listed in `requirements.txt`, not forgetting to download the spaCy transformer model.
2. Before running individual method scripts, populate the `dumps` folder with the 24 articles mentioned in the paper. Their names can be found in `dataset/_revisions.json`. An example of an output file name can be found in each method folder’s `_revisions.json`.
3. After a successful download of all dumps, all individual pipelines can be run with the input of the corresponding `_revisions.json` instructions file.

---

## Results Evaluation

The last, but not least, step is the correct setup for evaluation. Our initial motivation was to find as many scientists’ names as possible in order to achieve our goal. Since our custom pipeline follows a rule-based matching paradigm, it is possible that an entity may be recognized only partially — for example, the matcher may find only the last or the first part of a named entity, while in the text the entity has both a first and last name.

In such cases, we decided to count only **last-name matches**, while counting matches containing only first names as **false positives**. Since this custom logic works on character spans, not tokens, no separate method was implemented to evaluate results automatically, and evaluation should be done manually.

There is still work in progress to develop an accurate method that can perform this evaluation automatically.

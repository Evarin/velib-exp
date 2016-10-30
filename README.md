# Velib Experiments
Experiments with JCDecaux's API

Install
-------

__Requirements__:

    pip install -r requirements.txt
    mkdir output

And put your [JCDecaux API key](https://developer.jcdecaux.com) in a file `secrets.py`

Run
---

__Make the heatmap__:

    python visu.py paris

(outputs files to `output/`)

__Just save the data for later__:

    python get_data.py paris


Works with [many cities](https://developer.jcdecaux.com/#/opendata/vls?page=static).

Demo
----

What it can give superposed on a (Google) Map:

![An example of Paris](http://www.evarin.fr/velib/statique.jpg)

http://evarin.fr/velib/

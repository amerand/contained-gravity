# running ESO GRAVITY pipeline in docker

Build the image:
```
docker build -t gravipipe:latest .
```

Run the image, sharing the data directory:
```
docker run -it -p 8890:8888 -v ./data:/data --name="gravi" -d gravipipe
```
Put your raw data in the shared directory (here data). 

## Check raw data 
Open a terminal in the jupyter-lab environment (which runs in the container):
```
gravi_list_rawfits.py .
```

## reduce using python tools

Reduce GRAVITY data by calling python tools:
```
run_gravi_reduce.py --vis=TRUE --gravity_vis.flat-flux=TRUE --gravity_vis.vis-correction-sc=FORCE --gravity_vis.p2vmreduced-file=FALSE --gravity_vis.astro-file=FALSE --commoncalib-dir=/usr/share/esopipes/datastatic/gravity-1.6.6/  --gravity_vis.reduce-acq-cam=FALSE --viscal=TRUE --tf=TRUE
```

## optional: get data whithin container using the provided notebook
In a browser, go to `localhost:8890` to connect to jupyter-lab, then start notebook `Get GRAVITY data from Archive.ipynb` to get the list of files based on target and nights. Get the shell script from [ESO archive](http://archive.eso.org/cms/eso-data/eso-data-direct-retrieval.html) by uploading the list DPID created by the notebook. Save it somewhere in the shared directory (here data).


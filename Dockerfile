FROM fedora:37

RUN dnf -y install dnf-plugins-core  
# -- install python and provide jupyter lab env for reducing / checking data
RUN dnf -y install python3-pip
RUN python3 -m pip install scipy numpy matplotlib astropy astroquery jupyterlab ipympl

# -- get pipeline
RUN dnf -y config-manager --add-repo=https://ftp.eso.org/pub/dfs/pipelines/repositories/stable/fedora/esorepo.repo
RUN dnf -y install esopipe-gravity-1.6.6

# -- get consortia python tools
RUN dnf -y install subversion
RUN svn co https://version-lesia.obspm.fr:/repos/DRS_gravity/python_tools
ENV PATH="${PATH}:/python_tools"
RUN ln -s /usr/bin/python3 /usr/bin/python

# -- dfits and dfits and fitsort
RUN dnf -y install git gcc
RUN git clone https://github.com/granttremblay/eso_fits_tools
RUN cd eso_fits_tools; gcc -o dfits dfits.c; cp dfits /usr/bin
RUN cd eso_fits_tools; gcc -o fitsort fitsort.c; cp fitsort /usr/bin

# -- script based on dfits/fitsort to display GRAVITY raw files
ADD gravi_list_rawfits.py /usr/bin 
RUN chmod +x /usr/bin/gravi_list_rawfits.py

# -- needed to be able to run eso archive download scripts
RUN dnf -y install wget ncompress

# -- PMOIRED
RUN pip3 install -i https://test.pypi.org/simple/ pmoired==1.2.1

WORKDIR /data
# --ip 0.0.0.0 to allow external connection
EXPOSE 8888
ENTRYPOINT ["jupyter-lab", "--allow-root", "--ip", "0.0.0.0", "--NotebookApp.token=''"]

FROM phusion/baseimage:master-386

RUN apt-get update
RUN apt-get -y install python3 python3-pip

RUN pip3 install pytest
RUN pip3 install pytest-cov

# would be pulled in anyway, here for the cacheing during debug
RUN pip3 install numpy matplotlib python-dateutil
RUN pip3 install networkx spacy sympy filelock pyyaml cmake fsspec tokenizers tqdm
RUN pip3 install torch>=1.8.0


# takes a while, mostly in CUDA dependencies
# --quiet
RUN pip3 install -U https://github.com/scarfboy/wetsuite-dev/archive/refs/heads/main.zip


ADD https://github.com/scarfboy/wetsuite-dev/archive/refs/heads/main.tar.gz /root/test/
RUN cd /root/test && tar xf main.tar.gz && rm main.tar.gz


